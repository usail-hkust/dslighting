import logging
from typing import Dict

from dsat.models.formats import Plan, ReviewResult, Task
from dsat.operators.base import Operator
from dsat.services.llm import LLMService
from dsat.utils.parsing import parse_plan_and_code
from dsat.utils.context import summarize_repetitive_logs

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
    """Creates a structured, multi-step plan based on a user request."""
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

class ReviewOperator(Operator):
    """Reviews code execution output and provides a structured score and analysis."""
    async def __call__(self, prompt_context: Dict) -> ReviewResult:
        if not self.llm_service:
            raise ValueError("LLMService is required for this operator.")

        logger.info("Reviewing execution output...")
        
        raw_output = prompt_context.get('output', '# N/A')
        processed_output = summarize_repetitive_logs(raw_output)

        prompt = (
            "You are a data science judge. Review the following code and its output.\n\n"
            f"# TASK\n{prompt_context.get('task', 'N/A')}\n\n"
            f"# CODE\n```python\n{prompt_context.get('code', '# N/A')}\n```\n\n"
            f"# OUTPUT\n```\n{processed_output}\n```\n\n"
            "Respond with a JSON object containing your evaluation."
        )

        # No more simulation! This is a real structured call.
        review_model = await self.llm_service.call_with_json(prompt, output_model=ReviewResult)
        return review_model

class SummarizeOperator(Operator):
    """Generates a concise summary of a completed phase or task."""
    async def __call__(self, context: str) -> str:
        if not self.llm_service:
            raise ValueError("LLMService is required for this operator.")

        logger.info("Generating summary...")
        prompt = f"Please provide a concise summary of the following events:\n\n{context}"
        summary = await self.llm_service.call(prompt)
        logger.info("Summary generated successfully.")
        return summary