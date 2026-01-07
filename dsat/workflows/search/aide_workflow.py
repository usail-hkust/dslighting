# dsat/workflows/search/aide_workflow.py

import logging
import shutil
from pathlib import Path
from typing import Dict, Optional, Any, List

from dsat.workflows.base import DSATWorkflow
from dsat.services.states.journal import JournalState, Node, MetricValue
from dsat.benchmark.benchmark import BaseBenchmark
from dsat.services.llm import LLMService

from dsat.prompts.aide_prompt import create_improve_prompt, create_debug_prompt
from dsat.prompts.common import create_draft_prompt

from dsat.utils.context import ContextManager, summarize_repetitive_logs

logger = logging.getLogger(__name__)


class AIDEWorkflow(DSATWorkflow):
    """
    Implements the AIDE iterative search algorithm.
    This class serves as the base for search-based workflows, containing shared
    logic for the main search loop, node selection policy, and final artifact generation.
    """
    def __init__(self, operators: Dict[str, Any], services: Dict[str, Any], agent_config: Dict[str, Any], benchmark: Optional[BaseBenchmark] = None):
        """
        Initializes the AIDEWorkflow and its required services and operators.
        """
        super().__init__(operators, services, agent_config)
        self.state: JournalState = services["state"]
        self.sandbox_service = services["sandbox"]
        self.workspace_service = services.get("workspace")
        self.llm_service: LLMService = services["llm"]
        self.benchmark = benchmark
        
        self.execute_op = self.operators["execute"]
        
        self.generate_op = self.operators["generate"]
        self.review_op = self.operators["review"]
        
        self.context_manager = ContextManager()

    def _get_error_history(self, node: Node, max_depth: int = 3) -> str:
        """
        Traverses up a chain of buggy parent nodes to build a concise error history.
        """
        history = []
        current = node
        depth = 0
        while current and current.is_buggy and depth < max_depth:
            error_summary = self.context_manager.summarize_error(current.term_out, current.exc_type)
            entry = (
                f"--- Failure at Step #{current.step} ---\n"
                f"Plan: {current.plan}\n"
                f"Code:\n```python\n{current.code}\n```\n"
                f"Error:\n```\n{error_summary}\n```"
            )
            history.append(entry)
            depth += 1
            current = self.state.get_node(current.parent_id) if current.parent_id else None
        
        if not history:
            return "No error history found."

        # Reverse to show chronological order (oldest failure first)
        return "\n".join(reversed(history))

    def _llm_history_length(self) -> int:
        return len(self.llm_service.get_call_history())

    def _capture_llm_calls_since(self, start_index: int) -> List[Dict[str, Any]]:
        history = self.llm_service.get_call_history()
        if start_index < len(history):
            return history[start_index:]
        return []

    async def solve(self, description: str, io_instructions: str, data_dir: Path, output_path: Path) -> None:
        """
        The main entry point for the workflow.
        ...
        """
        logger.info(f"{self.__class__.__name__} starting to solve task. Target output: {output_path}")

        max_iterations = self.agent_config.get("search", {}).get("max_iterations", 3)

        for i in range(max_iterations):
            logger.info(f"--- Starting {self.__class__.__name__} Solve Step {i + 1}/{max_iterations} ---")
            
            task_context = {
                "goal_and_data": description,
                "io_instructions": io_instructions
            }
            
            await self._execute_search_step(task_context, output_path)
        
        logger.info("Max iterations reached. Generating final output from the best found solution.")
        best_node = self.state.get_best_node()

        if best_node:
            logger.info(f"Executing code from best node #{best_node.step} to generate final artifact.")
            final_exec_result = await self.execute_op(code=best_node.code, mode="script")
            if not final_exec_result.success:
                logger.warning(f"Final execution of best node's code failed: {final_exec_result.stderr}")
            final_solution_path = self._write_final_submission(best_node, output_path)
            if final_solution_path:
                logger.info(f"Final solution code saved to {final_solution_path}")
        else:
            logger.warning("No successful solution was found during the search.")

    async def _execute_search_step(self, task_context: Dict, output_path: Path):
        """
        Execute a single, concrete step of the AIDE search loop.
        This involves selecting a node to expand, generating new code, executing it,
        and performing **grounded validation** against the benchmark's grading function.
        
        Args:
            task_context: A dictionary containing the task goal, data report, and I/O instructions.
            output_path: The path where the final output file is expected. Used for grounded validation.
        """
        # 1. Select a node
        parent_node = self._select_node_to_expand()

        # 2. Create a prompt
        if parent_node is None:
            prompt = create_draft_prompt(task_context, self.state.generate_summary())
        elif parent_node.is_buggy:
            error_history = self._get_error_history(parent_node)
            prompt = create_debug_prompt(task_context, parent_node.code, error_history, previous_plan=parent_node.plan, memory_summary=self.state.generate_summary())
        else:
            summarized_output = summarize_repetitive_logs(parent_node.term_out)
            prompt = create_improve_prompt(
                task_context, self.state.generate_summary(), parent_node.code,
                parent_node.analysis, previous_plan=parent_node.plan, previous_output=summarized_output
            )

        # 3. Generate a new plan and code using the LLM.
        generate_start = self._llm_history_length()
        plan, code = await self.generate_op(system_prompt=prompt)
        new_node = Node(plan=plan, code=code)
        new_node.generate_prompt = prompt
        new_node.task_context = task_context
        new_calls = self._capture_llm_calls_since(generate_start)
        if new_calls:
            new_node.llm_generate = new_calls[-1]

        # 4. Execute the new code in the sandbox.
        exec_result = await self.execute_op(code=new_node.code, mode="script")
        new_node.absorb_exec_result(exec_result)

        # Perform grounded validation if code execution was successful.
        if exec_result.success:
            submission_file_in_sandbox = self.sandbox_service.workspace.get_path("sandbox_workdir") / output_path.name
            
            if not submission_file_in_sandbox.exists():
                new_node.is_buggy = True
                new_node.analysis = "Code executed without error, but failed to produce the required output file."
                new_node.metric = MetricValue(value=0.0, maximize=True)
            elif self.benchmark and hasattr(self.benchmark, 'grade'):
                logger.info(f"Performing grounded validation using benchmark grader on '{submission_file_in_sandbox}'...")
                score = await self.benchmark.grade(submission_file_in_sandbox)
                
                # A score > 0 from the grader is the ground truth for a non-buggy, valid submission.
                if score > 0:
                    new_node.is_buggy = False
                    new_node.metric = MetricValue(value=score, maximize=True)
                    logger.info(f"Grounded validation PASSED. Score: {score:.4f}")
                    review_context = {
                        "task": task_context,
                        "code": new_node.code,
                        "output": new_node.term_out
                    }
                    new_node.review_context = review_context
                    review_start = self._llm_history_length()
                    review = await self.review_op(prompt_context=review_context)
                    review_calls = self._capture_llm_calls_since(review_start)
                    if review_calls:
                        new_node.llm_review = review_calls[-1]
                    new_node.analysis = f"Grounded Score: {score:.4f}. Reviewer Summary: {review.summary}"
                else:
                    new_node.is_buggy = True
                    new_node.metric = MetricValue(value=score, maximize=True)
                    new_node.analysis = "Grounded validation FAILED: The generated submission file was invalid or scored 0.0."
                    logger.warning(f"Grounded validation FAILED. Score: {score}")
            else:
                review_context = {
                    "task": task_context,
                    "code": new_node.code,
                    "output": new_node.term_out
                }
                new_node.review_context = review_context
                review_start = self._llm_history_length()
                review = await self.review_op(prompt_context=review_context)
                review_calls = self._capture_llm_calls_since(review_start)
                if review_calls:
                    new_node.llm_review = review_calls[-1]
                new_node.analysis = review.summary
                new_node.is_buggy = review.is_buggy
                new_node.metric = MetricValue(value=review.metric_value, maximize=not review.lower_is_better) if review.metric_value is not None else MetricValue(value=None)
        
        # 7. Add the new node to the search tree state and persist artifacts.
        self.state.append(new_node, parent=parent_node)
        self._persist_node_artifacts(new_node)
        logger.info(f"Step {new_node.step} complete. Buggy: {new_node.is_buggy}. Metric: {new_node.metric}.")

    def _persist_node_artifacts(self, node: Node) -> None:
        """
        保存每个节点生成的代码，以便后续分析和还原完整路径。
        """
        if not self.workspace_service:
            return
        code_steps_dir = self.workspace_service.get_path("artifacts") / "code_steps"
        code_steps_dir.mkdir(parents=True, exist_ok=True)
        filename = f"step_{node.step:03d}_{node.id}.py"
        file_path = code_steps_dir / filename
        file_path.write_text(node.code, encoding="utf-8")
        node.code_artifact_path = str(file_path)

    def _write_final_submission(self, node: Node, expected_output: Path) -> Optional[Path]:
        """
        将最终成功的代码与输出复制到固定位置，便于后续复现。
        """
        if not self.workspace_service:
            return None
        final_dir = self.workspace_service.get_path("artifacts") / "final_submission"
        final_dir.mkdir(parents=True, exist_ok=True)

        final_solution_path = final_dir / "final_solution.py"
        final_solution_path.write_text(node.code, encoding="utf-8")
        node.final_submission_path = str(final_solution_path)

        if expected_output and expected_output.exists():
            try:
                shutil.copy2(expected_output, final_dir / expected_output.name)
            except Exception as copy_error:
                logger.warning(f"Failed to copy final submission artifact '{expected_output}': {copy_error}")

        return final_solution_path

    def _select_node_to_expand(self) -> Optional[Node]:
        """
        Implements the REVISED, DEBUG-FIRST search policy.
        The policy prioritizes:
        1. Debugging failed solutions.
        2. Improving the current best solution if no bugs exist.
        3. Drafting a new solution only as a last resort.
        """
        search_cfg = self.agent_config.get("search", {})
        # num_drafts is no longer used to block debugging
        max_debug_depth = search_cfg.get("max_debug_depth", 3)

        buggy_nodes = [n for n in self.state.nodes.values() if n.is_buggy]
        # Find nodes that are leaves in the bug-chain and haven't exceeded debug depth
        debuggable = [
            n for n in buggy_nodes 
            if not n.children_ids and self._get_debug_depth(n) < max_debug_depth
        ]
        
        if debuggable:
            # Select the most recent buggy node to work on
            selected = max(debuggable, key=lambda n: n.step)
            logger.info(f"[Search Policy] Debugging: Prioritizing most recent failed node #{selected.step}.")
            return selected

        best_node = self.state.get_best_node()
        if best_node:
            logger.info(f"[Search Policy] Improving: No bugs to fix. Selected best node #{best_node.step} with metric {best_node.metric}.")
            return best_node

        logger.info("[Search Policy] Drafting: No bugs to fix and no successful nodes to improve. Creating new solution.")
        return None

    def _get_debug_depth(self, node: Node) -> int:
        depth = 0
        current = node
        while current.parent_id:
            parent = self.state.get_node(current.parent_id)
            if not parent or not parent.is_buggy:
                break
            depth += 1
            current = parent
        return depth
