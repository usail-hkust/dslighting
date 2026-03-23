import logging
from typing import Any, Dict

from dslighting.core.types import Plan, ReviewResult, Task
from dslighting.ops.base import Operator
from dslighting.services.llm import LLMService
from dslighting.utils.parsing import parse_plan_and_code
from dslighting.state.context import summarize_repetitive_logs

logger = logging.getLogger(__name__)

class GenerateCodeAndPlanOperator(Operator):
    """Generates a plan and corresponding code based on a prompt."""
    async def __call__(self, system_prompt: str, user_prompt: str = "") -> tuple[str, str]:
        if not self.llm_service:
            raise ValueError("LLMService is required for this operator.")

        logger.info("Generating new code and plan...")
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        # Use the new standard call method
        response = await self.llm_service.call(full_prompt)
        plan, code = parse_plan_and_code(response)

        if "# ERROR" in code:
            logger.warning("Failed to parse a valid code block from the LLM response.")
        else:
            logger.info("Successfully generated code and plan.")
        
        return plan, code

class PlanOperator(Operator):
    """
    Creates a structured, multi-step plan based on a user request.

    This operator uses an LLM to decompose a natural language user request
    into a structured Plan containing multiple Tasks with dependencies.
    The output is suitable for sequential or parallel execution by other operators.

    Args:
        user_request: The user's task request or goal in natural language.
                     Should describe what the user wants to accomplish.

    Returns:
        Plan: A structured Plan object from dslighting.core.types containing
              a list of Tasks. Each Task has:
              - task_id (str): Unique identifier for the task
              - instruction (str): Natural language description of what to do
              - dependent_task_ids (List[str]): IDs of tasks that must complete first

    Example:
        >>> from dslighting.ops import PlanOperator
        >>> from dslighting.services import LLMService
        >>> llm_service = LLMService(model="gpt-4o")
        >>> operator = PlanOperator(llm_service=llm_service)
        >>> user_request = "Analyze the bike sharing dataset and predict future demand"
        >>> plan = await operator(user_request=user_request)
        >>> # Output: Plan(tasks=[
        >>> #   Task(task_id="1", instruction="Load and explore data", dependent_task_ids=[]),
        >>> #   Task(task_id="2", instruction="Build prediction model", dependent_task_ids=["1"]),
        >>> # ])
    """
    async def __call__(self, user_request: str) -> Plan:
        if not self.llm_service:
            raise ValueError("LLMService is required for this operator.")
        
        logger.info(f"Generating a plan for request: '{user_request[:100]}...'")
        
        prompt = f"Create a structured JSON plan for this user request: {user_request}"
        # No more placeholder! This is a real structured call.
        try:
            plan_model = await self.llm_service.call_with_json(prompt, output_model=Plan)
        except Exception as e:
            logger.warning(f"Structured plan failed ({e}); falling back to text plan.")
            text = await self.llm_service.call(prompt)
            plan_model = Plan(tasks=[Task(task_id="1", instruction=text.strip(), dependent_task_ids=[])])
        logger.info(f"Successfully generated a plan with {len(plan_model.tasks)} tasks.")
        return plan_model

class LLMBasedReviewOperator(Operator):
    """Reviews code execution output and provides a structured score and analysis."""
    async def __call__(self, prompt_context: Dict) -> ReviewResult:
        if not self.llm_service:
            raise ValueError("LLMService is required for this operator.")

        logger.info("Reviewing execution output...")

        raw_output = prompt_context.get('output', '# N/A')
        processed_output = summarize_repetitive_logs(raw_output)

        # task may be a full task_context dict or a plain string
        task = prompt_context.get('task', {})
        if isinstance(task, dict):
            task_str = task.get('goal_and_data', str(task))
            metric_name_value = task.get('metric_name')
            metric_name = metric_name_value.strip() if isinstance(metric_name_value, str) else ""
            lower_is_better_value = task.get('lower_is_better')
            lower_is_better = lower_is_better_value if isinstance(lower_is_better_value, bool) else None
        else:
            task_str = str(task)
            metric_name = ''
            lower_is_better = None

        grounded_metric_value: float | None = None
        grounded_value = prompt_context.get("grounded_metric_value")
        if isinstance(grounded_value, (int, float)) and not isinstance(grounded_value, bool):
            grounded_metric_value = float(grounded_value)

        if grounded_metric_value is not None:
            metric_label = metric_name or "score"
            metric_hint = (
                f"\n\nThe authoritative grounded metric for this run is **{metric_label}** with value "
                f"**{grounded_metric_value}**. Set `metric_value` to this exact numeric value."
            )
            if lower_is_better is not None:
                direction_literal = "true" if lower_is_better else "false"
                metric_hint += (
                    f" Set `lower_is_better` to {direction_literal}; do not infer direction from the output."
                )
            else:
                metric_hint += (
                    " Infer `lower_is_better` only from explicit task evidence or the metric name; "
                    "if direction cannot be determined reliably, set it to null."
                )
        elif metric_name and lower_is_better is not None:
            direction = "lower is better" if lower_is_better else "higher is better"
            metric_hint = (
                f"\n\nThe primary metric for this task is **{metric_name}** ({direction}). "
                f"Extract its numeric value from the output as `metric_value`. "
                f"Only set `metric_value` to null if the code produced no measurable output at all. "
                f"Set `lower_is_better` to {'true' if lower_is_better else 'false'} exactly as specified."
            )
        elif metric_name:
            metric_hint = (
                f"\n\nThe primary metric for this task is **{metric_name}**. "
                f"Extract its numeric value from the output as `metric_value`. "
                "Infer `lower_is_better` from the metric name or explicit task evidence only; "
                "if direction cannot be determined reliably, set `lower_is_better` to null."
            )
        else:
            metric_hint = (
                "\n\nIf the output contains any quantitative metric "
                "(e.g. accuracy, F1, loss, RMSE, score), extract it as `metric_value`. "
                "Only set `metric_value` to null if there is truly no numeric result. "
                "Set `lower_is_better` only when the task or metric direction is explicit; otherwise set it to null."
            )

        prompt = (
            "You are a data science judge. Review the following code and its output.\n\n"
            f"# TASK\n{task_str}\n\n"
            f"# CODE\n```python\n{prompt_context.get('code', '# N/A')}\n```\n\n"
            f"# OUTPUT\n```\n{processed_output}\n```\n\n"
            f"Respond with a JSON object containing your evaluation.{metric_hint}"
        )

        review_model = await self.llm_service.call_with_json(prompt, output_model=ReviewResult)
        return review_model

class SummarizeOperator(Operator):
    """
    Generates a concise summary of a completed phase or task.

    This operator uses an LLM to condense execution context, logs, or results
    into a readable summary. It is useful for documenting workflow progress
    and creating audit trails.

    Example:
        >>> from dslighting.ops import SummarizeOperator
        >>> from dslighting.services import LLMService
        >>> llm_service = LLMService(model="gpt-4o")
        >>> operator = SummarizeOperator(llm_service=llm_service)
        >>> context = '''
        ... Phase 1: Data exploration completed. Found 10 features, 2 missing values.
        ... Phase 2: Preprocessing applied. Missing values imputed.
        ... Phase 3: Model trained with accuracy 0.85.
        ... '''
        >>> summary = await operator(context=context)
    """
    async def __call__(self, context: str) -> str:
        if not self.llm_service:
            raise ValueError("LLMService is required for this operator.")

        logger.info("Generating summary...")
        prompt = f"Please provide a concise summary of the following events:\n\n{context}"
        summary = await self.llm_service.call(prompt)
        logger.info("Summary generated successfully.")
        return summary

__all__ = [
    "GenerateCodeAndPlanOperator",
    "PlanOperator",
    "LLMBasedReviewOperator",
    "SummarizeOperator",
]
