import logging
import json
from typing import Dict, Any, Optional
from pathlib import Path

from .aide_workflow import AIDEWorkflow
from dsat.services.states.journal import Node, MetricValue
from dsat.common.typing import ExecutionResult
from dsat.benchmark.benchmark import BaseBenchmark

from dsat.services.vdb import VDBService

from dsat.prompts.common import create_draft_prompt 
from dsat.prompts.automind_prompt import create_stepwise_code_prompt, create_stepwise_debug_prompt
from dsat.prompts.aide_prompt import create_improve_prompt, create_debug_prompt

from dsat.utils.context import (
    ContextManager,
    MAX_HISTORY_CHARS,
    MAX_OUTPUT_CHARS,
    summarize_repetitive_logs,
    truncate_output,
)

logger = logging.getLogger(__name__)


class AutoMindWorkflow(AIDEWorkflow):
    """
    Implements the AUTOMIND iterative search algorithm.
    This workflow extends AIDE by incorporating a knowledge base (VDB),
    a self-adaptive coding strategy (one-pass vs. stepwise), and more
    sophisticated context management for complex tasks.
    """
    def __init__(self, operators: Dict[str, Any], services: Dict[str, Any], agent_config: Dict[str, Any], benchmark: Optional[BaseBenchmark] = None):
        """
        Initializes the AutoMindWorkflow, building upon the AIDE base.
        """
        # Initialize base AIDE components, now passing the benchmark instance up.
        super().__init__(operators, services, agent_config, benchmark=benchmark)
        
        self.vdb_service: VDBService = services.get("vdb")
        
        self.complexity_scorer_op = self.operators.get("complexity_scorer")
        self.plan_decomposer_op = self.operators.get("plan_decomposer")
        
        # AutoMind's context manager requires an LLM service to summarize knowledge and history.
        self.context_manager = ContextManager(llm_service=services.get("llm"))

    async def _execute_search_step(self, task_context: Dict, output_path: Path):
        """
        Execute a single step of the AutoMind search loop.
        This overrides the AIDE implementation to add knowledge retrieval, the
        self-adaptive coding strategy, and now uses **grounded validation**.
        
        Args:
            task_context: A dictionary containing the task goal, data report, and I/O instructions.
            output_path: The path where the final output file is expected. Used for grounded validation.
        """
        # 1. Select a node
        parent_node = self._select_node_to_expand()
        
        task_goal = task_context.get('goal_and_data', 'Solve the data science task.')
        io_instructions = task_context.get('io_instructions', 'N/A')

        # 2. Create a prompt
        if parent_node is None:
            # For new drafts, retrieve similar examples from the knowledge base.
            retrieved_knowledge = ""
            if self.vdb_service:
                cases = self.vdb_service.retrieve(task_goal, top_k=2)
                retrieved_knowledge = await self.context_manager.summarize_knowledge(cases, task_goal)
            
            prompt = create_draft_prompt(task_context, self.state.generate_summary(), retrieved_knowledge)
        elif parent_node.is_buggy:
            error_summary = self.context_manager.summarize_error(parent_node.term_out, parent_node.exc_type)
            prompt = create_debug_prompt(task_context, parent_node.code, error_summary, previous_plan=parent_node.plan, memory_summary=self.state.generate_summary())
        else:
            summarized_output = summarize_repetitive_logs(parent_node.term_out)
            prompt = create_improve_prompt(
                task_context, self.state.generate_summary(), parent_node.code,
                parent_node.analysis, previous_plan=parent_node.plan, previous_output=summarized_output
            )

        # 3. Generate initial plan and one-pass code.
        plan, one_pass_code = await self.generate_op(system_prompt=prompt)
        
        # 4. Apply the self-adaptive coding strategy for new drafts.
        use_adaptive = self.complexity_scorer_op and self.plan_decomposer_op
        if use_adaptive and parent_node is None:
            final_code, exec_result = await self._execute_step_adaptively(plan, one_pass_code, task_goal, io_instructions)
        else:
            # For simpler tasks, improvements, or debugging, use the one-pass code.
            final_code = one_pass_code
            exec_result = await self.execute_op(code=final_code, mode="script")

        # 5. Create a new node and absorb the execution result.
        new_node = Node(plan=plan, code=final_code)
        new_node.absorb_exec_result(exec_result)

        if exec_result.success:
            submission_file_in_sandbox = self.sandbox_service.workspace.get_path("sandbox_workdir") / output_path.name
            
            if not submission_file_in_sandbox.exists():
                new_node.is_buggy = True
                new_node.analysis = "Code executed without error, but failed to produce the required output file."
                new_node.metric = MetricValue(value=0.0, maximize=True)
            elif self.benchmark and hasattr(self.benchmark, 'grade'):
                logger.info(f"Performing grounded validation using benchmark grader on '{submission_file_in_sandbox}'...")
                score = await self.benchmark.grade(submission_file_in_sandbox)
                
                if score > 0:
                    new_node.is_buggy = False
                    new_node.metric = MetricValue(value=score, maximize=True)
                    logger.info(f"Grounded validation PASSED. Score: {score:.4f}")
                    review = await self.review_op(prompt_context={
                        "task": task_context, "code": new_node.code, "output": new_node.term_out
                    })
                    new_node.analysis = f"Grounded Score: {score:.4f}. Reviewer Summary: {review.summary}"
                else:
                    new_node.is_buggy = True
                    new_node.metric = MetricValue(value=score, maximize=True)
                    new_node.analysis = "Grounded validation FAILED: The generated submission file was invalid or scored 0.0."
                    logger.warning(f"Grounded validation FAILED. Score: {score}")
            else:
                logger.warning("No benchmark with 'grade' method found. Falling back to unreliable LLM-based review.")
                review = await self.review_op(prompt_context={
                    "task": task_context, "code": new_node.code, "output": new_node.term_out
                })
                new_node.analysis = review.summary
                new_node.is_buggy = review.is_buggy
                new_node.metric = MetricValue(value=review.metric_value, maximize=not review.lower_is_better) if review.metric_value is not None else MetricValue(value=None)
        
        # 8. Add the new node to the search tree state.
        self.state.append(new_node, parent=parent_node)
        logger.info(f"Step {new_node.step} complete. Buggy: {new_node.is_buggy}. Metric: {new_node.metric}.")

    async def _execute_step_adaptively(self, plan: str, one_pass_code: str, task_goal: str, io_instructions: str) -> tuple[str, ExecutionResult]:
        """
        Core of the Self-Adaptive Coding Strategy.
        It scores the complexity of a plan and chooses to either execute the provided
        one-pass code directly or decompose the plan into smaller steps and execute them
        sequentially in a notebook context.
        
        Args:
            plan: The overall plan for the task.
            one_pass_code: The single block of code generated for the entire plan.
            task_goal: The user's primary goal.
            
        Returns:
            A tuple containing the final code (either one-pass or combined steps) and the
            final ExecutionResult.
        """
        final_code = one_pass_code
        
        # 1. Score plan complexity using the dedicated operator.
        score = await self.complexity_scorer_op(plan=plan, task_goal=task_goal)

        # 2. Choose strategy based on the complexity score.
        if score.complexity <= 3:  # Threshold for one-pass vs stepwise
            logger.info("Plan is simple. Executing in one-pass mode.")
            exec_result = await self.execute_op(code=final_code, mode="script")
        else:
            logger.info("Plan is complex. Decomposing and executing in stepwise mode.")
            # 3. Decompose the complex plan into a sequence of smaller tasks.
            decomposed_plan = await self.plan_decomposer_op(plan=plan, task_goal=task_goal)
            
            step_codes = []
            history_steps = []
            final_exec_result = None
            # Get max retries config
            max_step_retries = self.agent_config.get("max_retries", 3)

            async with self.sandbox_service.notebook_executor() as notebook:
                for task in decomposed_plan.tasks:
                    logger.info(f"Executing step {task.task_id}: {task.instruction}")
                    
                    step_succeeded = False
                    current_code = ""
                    step_failure_history = []  # History for the current step

                    # Implement retry loop for robustness
                    for attempt in range(max_step_retries):
                        logger.info(f"Step {task.task_id}, Attempt {attempt + 1}/{max_step_retries}")

                        # Build a concise history of recent steps to provide context for the next step.
                        recent_history_str = self.context_manager.build_history_context(
                            history_steps, 
                            key_order=["task_id", "code", "output"]
                        )
                        
                        if attempt == 0:
                            step_prompt = create_stepwise_code_prompt(task_goal, plan, recent_history_str, task.instruction, io_instructions)
                        else:
                            error_summary = self.context_manager.summarize_error(exec_result.stderr, exec_result.exc_type)
                            step_failure_history.append({
                                "attempt": attempt,
                                "code": truncate_output(current_code, MAX_OUTPUT_CHARS),
                                "error": error_summary
                            })
                            
                            formatted_failure_history = "\n".join([
                                f"--- Attempt {f['attempt']} Failed ---\nCode:\n```python\n{f['code']}\n```\nError: {f['error']}\n---"
                                for f in step_failure_history
                            ])
                            safe_failure_history = truncate_output(formatted_failure_history, MAX_HISTORY_CHARS)
                            
                            step_prompt = create_stepwise_debug_prompt(
                                task_goal, plan, recent_history_str, task.instruction,
                                current_code, safe_failure_history, io_instructions
                            )

                        _, current_code = await self.generate_op(system_prompt=step_prompt)
                        exec_result = await self.execute_op(code=current_code, mode="notebook", executor_context=notebook)
                        
                        if exec_result.success:
                            step_succeeded = True
                            break

                    if not step_succeeded:
                        logger.error(f"Step {task.task_id} failed after {max_step_retries} attempts. Aborting stepwise execution.")
                        final_exec_result = exec_result  # Capture the failed result
                        break

                    step_codes.append(f"# --- Step {task.task_id}: {task.instruction} ---\n{current_code}")
                    # Record the successful step for future context.
                    history_steps.append({
                        "task_id": task.task_id,
                        "code": truncate_output(current_code, MAX_OUTPUT_CHARS),
                        "output": truncate_output(exec_result.stdout, MAX_OUTPUT_CHARS),
                    })
                    final_exec_result = exec_result  # Update with the latest successful result
            
            final_code = "\n\n".join(step_codes)
            exec_result = final_exec_result

        return final_code, exec_result
