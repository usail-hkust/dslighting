import logging
import shutil
from pathlib import Path
from typing import Dict, Optional, Any, List, Tuple

from dslighting.workflows.base import BaseWorkflow
from dslighting.state.search.journal import JournalState, Node, MetricValue
from dslighting.benchmark.core.base import BaseBenchmark
from dslighting.core.visualization_policy import resolve_visualization_policy_from_agent_config
from dslighting.runtime.dag import BaseWorkflowActor, NodeResult, OpNode
from dslighting.error import LLMServiceError
from dslighting.services.llm import LLMService

from dslighting.prompts.workflows.aide import create_improve_prompt, create_debug_prompt
from dslighting.prompts.common import create_draft_prompt

from dslighting.state.context import ContextManager, summarize_repetitive_logs
from dslighting.workflows.utils import (
    build_error_history,
    capture_llm_history,
    llm_history_length,
)

logger = logging.getLogger(__name__)


class AIDEWorkflowDagActor(BaseWorkflowActor):
    """DAG actor that expands AIDE as dynamic, step-based nodes."""

    def __init__(
        self,
        *,
        task_id: str,
        workflow: "AIDEWorkflow",
        description: str,
        io_instructions: str,
        output_path: Path,
    ) -> None:
        self.task_id = task_id
        self.workflow = workflow
        self.output_path = output_path
        self.task_context = workflow._build_task_context(
            description=description,
            io_instructions=io_instructions,
        )
        self.max_iterations = max(
            1, int(workflow.agent_config.get("search", {}).get("max_iterations", 3))
        )

        self._done = False
        self._final_result: Dict[str, Any] = {}

    def _step_node_id(self, step_index: int) -> str:
        return f"{self.task_id}:aide_step:{step_index}"

    def _finalize_node_id(self) -> str:
        return f"{self.task_id}:aide_finalize"

    def _build_step_node(self, step_index: int, depends_on: List[str]) -> OpNode:
        return OpNode(
            node_id=self._step_node_id(step_index),
            task_id=self.task_id,
            op_type="custom",
            operator_name="aide_search_step",
            depends_on=list(depends_on),
            payload={
                "callable": self.workflow._dag_execute_search_step,
                "kwargs": {
                    "step_index": step_index,
                    "task_context": self.task_context,
                    "output_path": self.output_path,
                },
            },
            state_version=step_index,
            priority=10,
            estimated_runtime_seconds=60.0,
        )

    def _build_finalize_node(self, depends_on: List[str]) -> OpNode:
        return OpNode(
            node_id=self._finalize_node_id(),
            task_id=self.task_id,
            op_type="custom",
            operator_name="aide_finalize",
            depends_on=list(depends_on),
            payload={
                "callable": self.workflow._finalize_best_solution,
                "kwargs": {
                    "output_path": self.output_path,
                },
            },
            state_version=self.max_iterations,
            priority=5,
            estimated_runtime_seconds=30.0,
        )

    def initial_nodes(self) -> List[OpNode]:
        return [self._build_step_node(step_index=0, depends_on=[])]

    def on_node_result(self, result: NodeResult) -> Tuple[List[OpNode], bool]:
        if result.status != "success":
            self._done = True
            self._final_result = {
                "failed_node_id": result.node_id,
                "error": result.error,
                "status": result.status,
            }
            return [], True

        if result.node_id.startswith(f"{self.task_id}:aide_step:"):
            try:
                step_index = int(result.node_id.rsplit(":", 1)[-1])
            except ValueError:
                self._done = True
                self._final_result = {
                    "failed_node_id": result.node_id,
                    "error": f"Invalid step node id format: {result.node_id}",
                    "status": "failed",
                }
                return [], True

            next_step = step_index + 1
            if next_step < self.max_iterations:
                return [
                    self._build_step_node(step_index=next_step, depends_on=[result.node_id])
                ], False
            return [self._build_finalize_node(depends_on=[result.node_id])], False

        if result.node_id == self._finalize_node_id():
            self._done = True
            self._final_result = dict(result.outputs or {})
            self._final_result["status"] = "success"
            return [], True

        return [], self._done

    def get_result(self) -> Any:
        return dict(self._final_result)


class FineGrainedAIDEWorkflowDagActor(BaseWorkflowActor):
    """
    细粒度DAG模式的AIDE Actor。

    1. 每个Operator（Gen/Exec/Review）作为独立DAG节点
    2. 根据运行时结果（成功/失败）动态决定下一步
    3. 支持失败分支、重试、提前结束等动态行为

    DAG结构（动态生成）：
    gen_0 ──→ exec_0 ──→ review_0 ──成功──→ gen_1
        │           │            │失败
        │失败       │失败        ▼
        ▼           ▼         debug_0 (由新的gen实现)
    retry_0      retry_0        │
                              └──────┘
                                  │
                                  ▼
                            继续/结束
    """

    def __init__(
        self,
        *,
        task_id: str,
        workflow: "AIDEWorkflow",
        description: str,
        io_instructions: str,
        output_path: Path,
        enable_debug_branch: bool = True,  # Defaulting to True as it's core logic
        max_retries: int = 2,
    ) -> None:
        self.task_id = task_id
        self.workflow = workflow
        self.output_path = output_path
        self.task_context = workflow._build_task_context(
            description=description,
            io_instructions=io_instructions,
        )
        self.max_iterations = max(
            1, int(workflow.agent_config.get("search", {}).get("max_iterations", 3))
        )
        self.enable_debug_branch = enable_debug_branch
        self.max_retries = max_retries

        self._done = False
        self._final_result: Dict[str, Any] = {}
        self._retry_counts: Dict[str, int] = {}

    def _gen_node_id(self, step: int) -> str:
        return f"{self.task_id}:gen:{step}"

    def _exec_node_id(self, step: int) -> str:
        return f"{self.task_id}:exec:{step}"

    def _review_node_id(self, step: int) -> str:
        return f"{self.task_id}:review:{step}"

    def _finalize_node_id(self) -> str:
        return f"{self.task_id}:finalize"

    def _build_gen_node(self, step: int, depends_on: List[str], system_prompt: str) -> OpNode:
        """细粒度：Gen节点，接收一个动态构建的prompt"""
        return OpNode(
            node_id=self._gen_node_id(step),
            task_id=self.task_id,
            op_type="llm",
            operator_name="generate",
            depends_on=depends_on,
            payload={
                "callable": self.workflow.generate_op,
                "kwargs": {"system_prompt": system_prompt},
            },
            state_version=step,
            priority=10,
            estimated_runtime_seconds=10.0,
        )

    def _build_exec_node(self, step: int, code: str, depends_on: List[str]) -> OpNode:
        """细粒度：Exec节点"""
        return OpNode(
            node_id=self._exec_node_id(step),
            task_id=self.task_id,
            op_type="sandbox",
            operator_name="execute",
            depends_on=depends_on,
            payload={
                "callable": self.workflow.execute_op,
                "kwargs": {"code": code, "mode": "script"},
            },
            state_version=step,
            priority=5,
            estimated_runtime_seconds=30.0,
        )

    def _build_review_node(self, step: int, exec_result: Dict, depends_on: List[str]) -> OpNode:
        """细粒度：Review节点"""
        return OpNode(
            node_id=self._review_node_id(step),
            task_id=self.task_id,
            op_type="llm",
            operator_name="review",
            depends_on=depends_on,
            payload={
                "callable": self.workflow.review_op,
                "kwargs": {
                    "prompt_context": {
                        "task": self.task_context,
                        "code": exec_result.get("code", ""),
                        "output": exec_result.get("stdout", ""),
                    },
                },
            },
            state_version=step,
            priority=3,
            estimated_runtime_seconds=5.0,
        )

    def _build_finalize_node(self, depends_on: List[str]) -> OpNode:
        """Finalize节点"""
        return OpNode(
            node_id=self._finalize_node_id(),
            task_id=self.task_id,
            op_type="custom",
            operator_name="finalize",
            depends_on=depends_on,
            payload={
                "callable": self.workflow._finalize_best_solution,
                "kwargs": {"output_path": self.output_path},
            },
            state_version=self.max_iterations,
            priority=1,
            estimated_runtime_seconds=30.0,
        )

    def initial_nodes(self) -> List[OpNode]:
        """初始节点：第一个Gen, 使用draft prompt"""
        system_prompt = create_draft_prompt(
            self.task_context,
            self.workflow.state.generate_summary(),
            visualization_policy=self.workflow.visualization_policy,
        )
        return [self._build_gen_node(step=0, depends_on=[], system_prompt=system_prompt)]

    def on_node_result(self, result: NodeResult) -> Tuple[List[OpNode], bool]:
        node_id = result.node_id
        try:
            step = int(node_id.split(":")[-1])
        except (ValueError, IndexError):
            step = -1 # Finalize node or other format

        if node_id.startswith(f"{self.task_id}:gen:"):
            return self._handle_gen_result(step, result)
        elif node_id.startswith(f"{self.task_id}:exec:"):
            return self._handle_exec_result(step, result)
        elif node_id.startswith(f"{self.task_id}:review:"):
            return self._handle_review_result(step, result)
        elif node_id == self._finalize_node_id():
            self._done = True
            self._final_result = dict(result.outputs or {})
            self._final_result["status"] = "success"
            return [], True

        logger.warning(f"Unhandled node result for ID: {node_id}. Finishing workflow.")
        return [], True

    def _handle_gen_result(self, step: int, result: NodeResult) -> Tuple[List[OpNode], bool]:
        if result.status == "success":
            code = result.outputs.get("code", "")
            if not code or not code.strip():
                logger.warning(f"Step {step} generated empty code. Triggering search logic to debug/retry.")
                return self._create_next_generation_nodes(result.node_id, step)
            return [self._build_exec_node(step=step, code=code, depends_on=[result.node_id])], False
        else: # Gen failed
            self._retry_counts[result.node_id] = self._retry_counts.get(result.node_id, 0) + 1
            if self._retry_counts[result.node_id] < self.max_retries:
                logger.info(f"Generation failed at step {step}. Retrying with search logic...")
                return self._create_next_generation_nodes(result.node_id, step)
            else:
                logger.error(f"Max retries reached for generate op at step {step}. Finishing.")
                self._done = True
                self._final_result = {"status": "failed", "error": "Max retries for generate op reached."}
                return [], True

    def _handle_exec_result(self, step: int, result: NodeResult) -> Tuple[List[OpNode], bool]:
        # ASSUMPTION: The `execute_op` has updated the shared `JournalState` with execution results.
        if result.status == "success":
            return [self._build_review_node(step=step, exec_result=result.outputs, depends_on=[result.node_id])], False
        else:
            logger.info(f"Execution failed at step {step}. Triggering search logic for debug.")
            return self._create_next_generation_nodes(result.node_id, step)

    def _handle_review_result(self, step: int, result: NodeResult) -> Tuple[List[OpNode], bool]:
        # A full gen-exec-review cycle is complete.
        logger.info(f"Review complete for step {step}. Triggering next search iteration.")
        return self._create_next_generation_nodes(result.node_id, step)

    def _create_next_generation_nodes(self, from_node_id: str, last_step_index: int) -> Tuple[List[OpNode], bool]:
        """
        The "brain" of the actor. Decides what to do next based on the full history.
        This mimics the logic of _execute_search_step's prompt creation.
        """
        next_step = last_step_index + 1
        if next_step >= self.max_iterations:
            logger.info("Max iterations reached. Triggering finalize node.")
            return [self._build_finalize_node(depends_on=[from_node_id])], False

        # --- Ported Intelligence from AIDEWorkflow ---
        # 1. Select a node from history to expand upon using the workflow's search strategy.
        parent_node = self.workflow._select_node_to_expand()

        # 2. Create the appropriate prompt based on the selected node's state.
        if parent_node is None:
            # This case happens if the journal is empty or no nodes are expandable. Start fresh.
            logger.info(f"Step {next_step}: Creating new draft solution from scratch.")
            prompt = create_draft_prompt(
                self.task_context,
                self.workflow.state.generate_summary(),
                visualization_policy=self.workflow.visualization_policy,
            )
        elif parent_node.is_buggy:
            # Debug branch: create a prompt to fix the code of the selected buggy node.
            logger.info(f"Step {next_step}: Debugging failed node #{parent_node.step}.")
            error_history = self.workflow._get_error_history(parent_node)
            prompt = create_debug_prompt(
                self.task_context,
                parent_node.code,
                error_history,
                previous_plan=parent_node.plan,
                memory_summary=self.workflow.state.generate_summary(),
                visualization_policy=self.workflow.visualization_policy,
            )
        else:
            # Improve branch: create a prompt to improve upon the selected successful node.
            logger.info(f"Step {next_step}: Improving successful node #{parent_node.step}.")
            summarized_output = summarize_repetitive_logs(parent_node.term_out)
            prompt = create_improve_prompt(
                self.task_context,
                self.workflow.state.generate_summary(),
                parent_node.code,
                parent_node.analysis,
                previous_plan=parent_node.plan,
                previous_output=summarized_output,
                visualization_policy=self.workflow.visualization_policy,
            )

        # 3. Build and return the new generation node for the next step.
        return [self._build_gen_node(step=next_step, depends_on=[from_node_id], system_prompt=prompt)], False

    def get_result(self) -> Any:
        return dict(self._final_result)



class AIDEWorkflow(BaseWorkflow):
    """
    Implements the AIDE iterative search algorithm.
    This class serves as the base for search-based workflows, containing shared
    logic for the main search loop, node selection policy, and final artifact generation.
    """

    def __init__(
        self,
        operators: Dict[str, Any],
        services: Dict[str, Any],
        agent_config: Dict[str, Any],
        benchmark: Optional[BaseBenchmark] = None,
    ):
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
        self.visualization_policy = resolve_visualization_policy_from_agent_config(agent_config)

    def _get_error_history(self, node: Node, max_depth: int = 3) -> str:
        """
        Traverses up a chain of buggy parent nodes to build a concise error history.
        """
        return build_error_history(
            node=node,
            state=self.state,
            context_manager=self.context_manager,
            max_depth=max_depth,
        )

    def _llm_history_length(self) -> int:
        return llm_history_length(self.llm_service)

    def _capture_llm_calls_since(self, start_index: int) -> List[Dict[str, Any]]:
        return capture_llm_history(self.llm_service, start_index)

    @staticmethod
    def _maximize_from_task_context(task_context: Dict[str, Any]) -> bool:
        lower_is_better = task_context.get("lower_is_better")
        return False if lower_is_better is True else True

    def _build_task_context(self, *, description: str, io_instructions: str) -> Dict[str, Any]:
        task_context = {
            "goal_and_data": description,
            "io_instructions": io_instructions,
        }
        raw_hints = self.agent_config.get("task_context", {}) if isinstance(self.agent_config, dict) else {}
        if isinstance(raw_hints, dict):
            metric_name = raw_hints.get("metric_name")
            if isinstance(metric_name, str) and metric_name.strip():
                task_context["metric_name"] = metric_name.strip()
            lower_is_better = raw_hints.get("lower_is_better")
            if isinstance(lower_is_better, bool):
                task_context["lower_is_better"] = lower_is_better
        return task_context

    @staticmethod
    def _apply_grounded_metric_to_review(
        review: Any,
        *,
        score: float,
        task_context: Dict[str, Any],
    ) -> None:
        review.metric_value = score
        lower_is_better = task_context.get("lower_is_better")
        review.lower_is_better = lower_is_better if isinstance(lower_is_better, bool) else None

    @staticmethod
    def _grounded_review_fallback_summary(*, score: float, error: Exception) -> str:
        return f"Grounded Score: {score:.4f}. Review unavailable due to LLM failure: {error}"

    def build_actor(
        self,
        *,
        task_id: str,
        description: str,
        io_instructions: str,
        data_dir: Path,
        output_path: Path,
        dag_options: Optional[Any] = None,
    ) -> BaseWorkflowActor:
        # data_dir is accepted for interface consistency; AIDE actor uses workflow state + output path.
        _ = data_dir

        dag_mode = str(getattr(dag_options, "dag_mode", "coarse") or "coarse").strip().lower()
        if dag_mode == "fine":
            try:
                fine_max_retries = max(1, int(getattr(dag_options, "max_retries", 3) or 3))
            except (TypeError, ValueError):
                fine_max_retries = 3

            return FineGrainedAIDEWorkflowDagActor(
                task_id=task_id,
                workflow=self,
                description=description,
                io_instructions=io_instructions,
                output_path=output_path,
                enable_debug_branch=bool(getattr(dag_options, "enable_debug_branch", False)),
                max_retries=fine_max_retries,
            )

        return AIDEWorkflowDagActor(
            task_id=task_id,
            workflow=self,
            description=description,
            io_instructions=io_instructions,
            output_path=output_path,
        )

    @staticmethod
    def _infer_competition_id_from_output_path(output_path: Path) -> Optional[str]:
        stem = output_path.stem
        if not stem.startswith("submission_"):
            return None
        core = stem[len("submission_") :]
        if "_" not in core:
            return core or None
        return core.rsplit("_", 1)[0] or None

    async def _grade_submission_with_context(
        self, submission_path: Path, output_path: Path
    ) -> float:
        """
        Grade with best-effort competition context.
        Falls back to legacy signature for non-MLE benchmarks.
        """
        if not self.benchmark or not hasattr(self.benchmark, "grade"):
            return 0.0

        competition_id = self._infer_competition_id_from_output_path(output_path)
        if not competition_id:
            for key in ("competition_id", "task_id"):
                candidate = self.agent_config.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    competition_id = candidate.strip()
                    break
        try:
            if competition_id:
                return await self.benchmark.grade(submission_path, competition_id=competition_id)
            return await self.benchmark.grade(submission_path)
        except TypeError:
            return await self.benchmark.grade(submission_path)

    async def solve(
        self, description: str, io_instructions: str, data_dir: Path, output_path: Path
    ) -> None:
        """
        The main entry point for the workflow.
        ...
        """
        logger.info(
            f"{self.__class__.__name__} starting to solve task. Target output: {output_path}"
        )

        max_iterations = self.agent_config.get("search", {}).get("max_iterations", 3)

        for i in range(max_iterations):
            logger.info(
                f"--- Starting {self.__class__.__name__} Solve Step {i + 1}/{max_iterations} ---"
            )

            task_context = self._build_task_context(
                description=description,
                io_instructions=io_instructions,
            )

            await self._execute_search_step(task_context, output_path)

        await self._finalize_best_solution(output_path)

    async def _dag_execute_search_step(
        self,
        *,
        step_index: int,
        task_context: Dict[str, Any],
        output_path: Path,
    ) -> Dict[str, Any]:
        await self._execute_search_step(task_context, output_path)
        best_node = self.state.get_best_node()
        return {
            "step_index": step_index,
            "journal_nodes": len(self.state.nodes),
            "best_step": best_node.step if best_node else None,
            "best_metric": best_node.metric.value if best_node and best_node.metric else None,
        }

    async def _finalize_best_solution(self, output_path: Path) -> Dict[str, Any]:
        logger.info("Max iterations reached. Generating final output from the best found solution.")
        best_node = self.state.get_best_node()

        if not best_node:
            logger.warning("No successful solution was found during the search.")
            return {
                "has_best_node": False,
                "output_path": str(output_path),
            }

        logger.info(f"Executing code from best node #{best_node.step} to generate final artifact.")
        final_exec_result = await self.execute_op(code=best_node.code, mode="script")
        if not final_exec_result.success:
            logger.warning(
                f"Final execution of best node's code failed: {final_exec_result.stderr}"
            )
        final_solution_path = self._write_final_submission(best_node, output_path)
        if final_solution_path:
            logger.info(f"Final solution code saved to {final_solution_path}")

        return {
            "has_best_node": True,
            "best_step": best_node.step,
            "best_metric": best_node.metric.value if best_node.metric else None,
            "final_exec_success": bool(final_exec_result.success),
            "final_solution_path": str(final_solution_path) if final_solution_path else None,
            "output_path": str(output_path),
        }

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
            prompt = create_draft_prompt(
                task_context,
                self.state.generate_summary(),
                visualization_policy=self.visualization_policy,
            )
        elif parent_node.is_buggy:
            error_history = self._get_error_history(parent_node)
            prompt = create_debug_prompt(
                task_context,
                parent_node.code,
                error_history,
                previous_plan=parent_node.plan,
                memory_summary=self.state.generate_summary(),
                visualization_policy=self.visualization_policy,
            )
        else:
            summarized_output = summarize_repetitive_logs(parent_node.term_out)
            prompt = create_improve_prompt(
                task_context,
                self.state.generate_summary(),
                parent_node.code,
                parent_node.analysis,
                previous_plan=parent_node.plan,
                previous_output=summarized_output,
                visualization_policy=self.visualization_policy,
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
            submission_file_in_sandbox = (
                self.sandbox_service.workspace.get_path("sandbox_workdir") / output_path.name
            )

            maximize = self._maximize_from_task_context(task_context)

            if not submission_file_in_sandbox.exists():
                new_node.is_buggy = True
                new_node.analysis = (
                    f"Code executed without error, but the required output file was not found. "
                    f"You MUST save the output as `{output_path.name}` in the current working "
                    f"directory. Do NOT use a different filename or hash suffix. "
                    f"Check that your code ends with exactly: "
                    f"`df.to_csv('{output_path.name}', index=False)` (or equivalent)."
                )
                new_node.metric = MetricValue(value=0.0, maximize=maximize)
            elif self.benchmark and hasattr(self.benchmark, "grade"):
                logger.info(
                    f"Performing grounded validation using benchmark grader on '{submission_file_in_sandbox}'..."
                )
                score = await self._grade_submission_with_context(
                    submission_file_in_sandbox, output_path
                )

                # A score > 0 from the grader is the ground truth for a non-buggy, valid submission.
                if score > 0:
                    new_node.is_buggy = False
                    new_node.metric = MetricValue(value=score, maximize=maximize)
                    logger.info(f"Grounded validation PASSED. Score: {score:.4f}")
                    review_context = {
                        "task": task_context,
                        "code": new_node.code,
                        "output": new_node.term_out,
                        "grounded_metric_value": score,
                    }
                    new_node.review_context = review_context
                    review_start = self._llm_history_length()
                    try:
                        review = await self.review_op(prompt_context=review_context)
                    except LLMServiceError as exc:
                        logger.warning("Grounded review failed after successful grading; preserving grounded score: %s", exc)
                        review_calls = self._capture_llm_calls_since(review_start)
                        if review_calls:
                            new_node.llm_review = review_calls[-1]
                        new_node.analysis = self._grounded_review_fallback_summary(score=score, error=exc)
                        review = None
                    else:
                        self._apply_grounded_metric_to_review(
                            review,
                            score=score,
                            task_context=task_context,
                        )
                        review_calls = self._capture_llm_calls_since(review_start)
                        if review_calls:
                            new_node.llm_review = review_calls[-1]
                        new_node.analysis = (
                            f"Grounded Score: {score:.4f}. Reviewer Summary: {review.summary}"
                        )
                else:
                    new_node.is_buggy = True
                    new_node.metric = MetricValue(value=score, maximize=maximize)
                    new_node.analysis = "Grounded validation FAILED: The generated submission file was invalid or scored 0.0."
                    logger.warning(f"Grounded validation FAILED. Score: {score}")
            else:
                review_context = {
                    "task": task_context,
                    "code": new_node.code,
                    "output": new_node.term_out,
                }
                new_node.review_context = review_context
                review_start = self._llm_history_length()
                review = await self.review_op(prompt_context=review_context)
                review_calls = self._capture_llm_calls_since(review_start)
                if review_calls:
                    new_node.llm_review = review_calls[-1]
                new_node.absorb_review(review, task_context)

        # 7. Add the new node to the search tree state and persist artifacts.
        self.state.append(new_node, parent=parent_node)
        self._persist_node_artifacts(new_node)
        logger.info(
            f"Step {new_node.step} complete. Buggy: {new_node.is_buggy}. Metric: {new_node.metric}."
        )

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
                target_path = final_dir / expected_output.name
                if expected_output.is_dir():
                    if target_path.exists():
                        if target_path.is_dir():
                            shutil.rmtree(target_path)
                        else:
                            target_path.unlink()
                    shutil.copytree(expected_output, target_path)
                else:
                    shutil.copy2(expected_output, target_path)
            except Exception as copy_error:
                logger.warning(
                    f"Failed to copy final submission artifact '{expected_output}': {copy_error}"
                )

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
            n
            for n in buggy_nodes
            if not n.children_ids and self._get_debug_depth(n) < max_debug_depth
        ]

        if debuggable:
            # Select the most recent buggy node to work on
            selected = max(debuggable, key=lambda n: n.step)
            logger.info(
                f"[Search Policy] Debugging: Prioritizing most recent failed node #{selected.step}."
            )
            return selected

        best_node = self.state.get_best_node()
        if best_node:
            logger.info(
                f"[Search Policy] Improving: No bugs to fix. Selected best node #{best_node.step} with metric {best_node.metric}."
            )
            return best_node

        logger.info(
            "[Search Policy] Drafting: No bugs to fix and no successful nodes to improve. Creating new solution."
        )
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
