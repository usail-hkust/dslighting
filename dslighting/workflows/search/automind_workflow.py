import logging
import json
from typing import Dict, Any, Optional, List, Tuple, Type
from pathlib import Path

from dslighting.runtime.dag import BaseWorkflowActor, NodeResult, OpNode
from dslighting.state.search.journal import Node, MetricValue
from dslighting.utils.typing import ExecutionResult
from dslighting.benchmark.core.base import BaseBenchmark
from dslighting.error import LLMServiceError
from dslighting.services.vdb import VDBService

from dslighting.prompts.common import create_draft_prompt
from dslighting.prompts.workflows.automind import (
    create_stepwise_code_prompt,
    create_stepwise_debug_prompt,
)
from dslighting.prompts.workflows.aide import create_improve_prompt, create_debug_prompt

from dslighting.state.context import (
    ContextManager,
    MAX_HISTORY_CHARS,
    MAX_OUTPUT_CHARS,
    summarize_repetitive_logs,
    truncate_output,
)
from dslighting.workflows.search.aide_workflow import AIDEWorkflow
from dslighting.workflows.utils import (
    build_error_history,
    capture_llm_history,
    llm_history_length,
)

logger = logging.getLogger(__name__)


class AutoMindWorkflowDagActor(BaseWorkflowActor):
    """
    DAG actor for AutoMind workflow.

    AutoMind-specific features:
    - Knowledge retrieval from VDB for new drafts
    - Complexity scoring to decide one-pass vs stepwise execution
    - Stepwise execution for complex plans

    DAG structure (dynamically generated):
    gen_0 ──→ complexity_0 ──→ exec_0 ──→ review_0 ──success──→ gen_1
                  │                 │            │failure
                  └──complex>3────┘ │failure    ▼
                            stepwise_0 ┌───────┘
                                  │    │
                                  ▼
                            continue/finish
    """

    def __init__(
        self,
        *,
        task_id: str,
        workflow: "AutoMindWorkflow",
        description: str,
        io_instructions: str,
        output_path: Path,
        enable_debug_branch: bool = False,
        max_retries: int = 3,
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
        return f"{self.task_id}:automind_gen:{step}"

    def _complexity_node_id(self, step: int) -> str:
        return f"{self.task_id}:automind_complexity:{step}"

    def _decompose_node_id(self, step: int) -> str:
        return f"{self.task_id}:automind_decompose:{step}"

    def _exec_node_id(self, step: int) -> str:
        return f"{self.task_id}:automind_exec:{step}"

    def _stepwise_node_id(self, step: int, sub_step: int) -> str:
        return f"{self.task_id}:automind_stepwise:{step}:{sub_step}"

    def _review_node_id(self, step: int) -> str:
        return f"{self.task_id}:automind_review:{step}"

    def _finalize_node_id(self) -> str:
        return f"{self.task_id}:automind_finalize"

    def _build_gen_node(self, step: int, depends_on: List[str]) -> OpNode:
        """Gen node: generate initial plan and code using AutoMind's prompting strategy"""
        parent_node = self.workflow._select_node_to_expand()
        task_goal = self.task_context.get("goal_and_data", "Solve the data science task.")

        if parent_node is None:
            retrieved_knowledge = ""
            if self.workflow.vdb_service:
                cases = self.workflow.vdb_service.retrieve_cases(task_goal, top_k=2)
                retrieved_knowledge = self.workflow.context_manager.summarize_knowledge(
                    cases, task_goal
                )
            prompt = create_draft_prompt(
                self.task_context,
                self.workflow.state.generate_summary(),
                retrieved_knowledge,
                visualization_policy=self.workflow.visualization_policy,
            )
        elif parent_node.is_buggy:
            error_summary = self.workflow.context_manager.summarize_error(
                parent_node.term_out, parent_node.exc_type
            )
            prompt = create_debug_prompt(
                self.task_context,
                parent_node.code,
                error_summary,
                previous_plan=parent_node.plan,
                memory_summary=self.workflow.state.generate_summary(),
                visualization_policy=self.workflow.visualization_policy,
            )
        else:
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

        return OpNode(
            node_id=self._gen_node_id(step),
            task_id=self.task_id,
            op_type="llm",
            operator_name="generate",
            depends_on=depends_on,
            payload={
                "callable": self.workflow.generate_op,
                "kwargs": {
                    "system_prompt": prompt,
                },
            },
            state_version=step,
            priority=10,
            estimated_runtime_seconds=15.0,
        )

    def _build_complexity_node(self, step: int, plan: str, depends_on: List[str]) -> OpNode:
        """Complexity scoring node: decide one-pass vs stepwise execution"""
        return OpNode(
            node_id=self._complexity_node_id(step),
            task_id=self.task_id,
            op_type="custom",
            operator_name="complexity_scorer",
            depends_on=depends_on,
            payload={
                "callable": self.workflow.complexity_scorer_op,
                "kwargs": {
                    "plan": plan,
                    "task_goal": self.task_context.get("goal_and_data", ""),
                },
            },
            state_version=step,
            priority=8,
            estimated_runtime_seconds=5.0,
        )

    def _build_decompose_node(self, step: int, plan: str, depends_on: List[str]) -> OpNode:
        """Plan decomposition node: decompose complex plan into smaller tasks"""
        return OpNode(
            node_id=self._decompose_node_id(step),
            task_id=self.task_id,
            op_type="custom",
            operator_name="plan_decomposer",
            depends_on=depends_on,
            payload={
                "callable": self.workflow.plan_decomposer_op,
                "kwargs": {
                    "plan": plan,
                    "task_goal": self.task_context.get("goal_and_data", ""),
                },
            },
            state_version=step,
            priority=7,
            estimated_runtime_seconds=10.0,
        )

    def _build_exec_node(self, step: int, code: str, depends_on: List[str]) -> OpNode:
        """Exec node: execute code in sandbox (one-pass mode)"""
        return OpNode(
            node_id=self._exec_node_id(step),
            task_id=self.task_id,
            op_type="sandbox",
            operator_name="execute",
            depends_on=depends_on,
            payload={
                "callable": self.workflow.execute_op,
                "kwargs": {
                    "code": code,
                    "mode": "script",
                },
            },
            state_version=step,
            priority=5,
            estimated_runtime_seconds=30.0,
        )

    def _build_stepwise_node(
        self, step: int, sub_step: int, code: str, depends_on: List[str], is_retry: bool = False
    ) -> OpNode:
        """Stepwise execution node: execute a single step in notebook context"""
        return OpNode(
            node_id=self._stepwise_node_id(step, sub_step),
            task_id=self.task_id,
            op_type="sandbox",
            operator_name="execute_stepwise",
            depends_on=depends_on,
            payload={
                "callable": self.workflow.execute_op,
                "kwargs": {
                    "code": code,
                    "mode": "notebook",
                },
            },
            state_version=step * 100 + sub_step,
            priority=5,
            estimated_runtime_seconds=20.0,
        )

    def _build_review_node(self, step: int, exec_result: Dict, depends_on: List[str]) -> OpNode:
        """Review node: review execution results"""
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
        """Finalize node"""
        return OpNode(
            node_id=self._finalize_node_id(),
            task_id=self.task_id,
            op_type="custom",
            operator_name="finalize",
            depends_on=depends_on,
            payload={
                "callable": self.workflow._finalize_best_solution,
                "kwargs": {
                    "output_path": self.output_path,
                },
            },
            state_version=self.max_iterations,
            priority=1,
            estimated_runtime_seconds=30.0,
        )

    def initial_nodes(self) -> List[OpNode]:
        """Initial node: first Gen"""
        return [self._build_gen_node(step=0, depends_on=[])]

    def on_node_result(self, result: NodeResult) -> Tuple[List[OpNode], bool]:
        """
        Core of dynamic DAG

        Why is it dynamic?
        - Not predefined all steps
        - Dynamically decide next step based on runtime results
        """
        node_id = result.node_id

        if node_id.startswith(f"{self.task_id}:automind_gen:"):
            step = int(node_id.split(":")[-1])
            return self._handle_gen_result(step, result)

        elif node_id.startswith(f"{self.task_id}:automind_complexity:"):
            step = int(node_id.split(":")[-2])
            return self._handle_complexity_result(step, result)

        elif node_id.startswith(f"{self.task_id}:automind_decompose:"):
            step = int(node_id.split(":")[-2])
            return self._handle_decompose_result(step, result)

        elif node_id.startswith(f"{self.task_id}:automind_exec:"):
            step = int(node_id.split(":")[-1])
            return self._handle_exec_result(step, result)

        elif node_id.startswith(f"{self.task_id}:automind_stepwise:"):
            parts = node_id.split(":")
            step = int(parts[-2])
            sub_step = int(parts[-1])
            return self._handle_stepwise_result(step, sub_step, result)

        elif node_id.startswith(f"{self.task_id}:automind_review:"):
            step = int(node_id.split(":")[-1])
            return self._handle_review_result(step, result)

        elif node_id == self._finalize_node_id():
            self._done = True
            self._final_result = dict(result.outputs or {})
            self._final_result["status"] = "success"
            return [], True

        return [], self._done

    def _handle_gen_result(self, step: int, result: NodeResult) -> Tuple[List[OpNode], bool]:
        """Handle Gen result: proceed to complexity scoring

        修复：手动包装返回值到 outputs
        """
        if result.status == "success":
            # ===== 修复：手动包装返回值到 outputs =====
            if not result.outputs or not isinstance(result.outputs, dict):
                # 如果 outputs 为空或不是字典，尝试从返回值获取
                if hasattr(result, 'return_value') and result.return_value:
                    # 返回值是 (plan, code) 元组
                    plan, code = result.return_value if isinstance(result.return_value, tuple) else ("", result.return_value)
                    result.outputs = {"plan": plan, "code": code}
                else:
                    # 降级处理：使用空字符串
                    result.outputs = {"plan": "", "code": ""}

            # 现在可以安全地获取 plan 和 code
            plan = result.outputs.get("plan", "")
            code = result.outputs.get("code", "")

            if not code:
                # 如果 code 仍然为空，记录错误并重试
                logger.warning(f"Gen_{step} returned empty code, retrying...")
                return self._handle_gen_failure(step, result)

            if self.workflow.complexity_scorer_op and self.workflow.plan_decomposer_op:
                return [
                    self._build_complexity_node(step=step, plan=plan, depends_on=[result.node_id])
                ], False
            else:
                return [
                    self._build_exec_node(
                        step=step, code=code, depends_on=[result.node_id]
                    )
                ], False
        else:
            return self._handle_gen_failure(step, result)

    def _handle_gen_failure(self, step: int, result: NodeResult) -> Tuple[List[OpNode], bool]:
        """Handle Gen failure: retry or terminate"""
        self._retry_counts[result.node_id] = self._retry_counts.get(result.node_id, 0) + 1
        if self._retry_counts[result.node_id] < self.max_retries:
            logger.info(f"Retrying Gen_{step} (attempt {self._retry_counts[result.node_id]}/{self.max_retries})")
            return [self._build_gen_node(step=step, depends_on=[])], False
        else:
            logger.error(f"Gen_{step} failed after {self.max_retries} retries")
            self._done = True
            return [], True

    def _handle_complexity_result(self, step: int, result: NodeResult) -> Tuple[List[OpNode], bool]:
        """Handle complexity scoring result: decide one-pass or stepwise"""
        if result.status == "success":
            complexity = result.outputs.get("complexity", 0)
            plan = result.outputs.get("plan", "")
            one_pass_code = result.outputs.get("code", "")

            if complexity <= 3:
                logger.info(
                    f"Plan is simple (complexity={complexity}). Executing in one-pass mode."
                )
                return [
                    self._build_exec_node(
                        step=step, code=one_pass_code, depends_on=[result.node_id]
                    )
                ], False
            else:
                logger.info(
                    f"Plan is complex (complexity={complexity}). Decomposing for stepwise execution."
                )
                return [
                    self._build_decompose_node(step=step, plan=plan, depends_on=[result.node_id])
                ], False
        else:
            return [
                self._build_exec_node(step=step, code=result.outputs.get("code", ""), depends_on=[])
            ], False

    def _handle_decompose_result(self, step: int, result: NodeResult) -> Tuple[List[OpNode], bool]:
        """Handle decomposition result: start stepwise execution

        修复：设置 decomposed_plan_cache 以支持完整的 stepwise 执行
        """
        if result.status == "success":
            tasks = result.outputs.get("tasks", [])

            # ===== 修复：设置 decomposed_plan_cache =====
            if not hasattr(self, "_decomposed_plan_cache"):
                self._decomposed_plan_cache = {}
            self._decomposed_plan_cache[step] = tasks

            if tasks:
                first_task = tasks[0]
                logger.info(f"Starting stepwise execution for step {step} with {len(tasks)} tasks")
                return [
                    self._build_stepwise_node(
                        step=step,
                        sub_step=0,
                        code=first_task.get("code", ""),
                        depends_on=[result.node_id],
                    )
                ], False
            else:
                logger.warning(f"Decomposition returned no tasks for step {step}")
                return self._continue_or_finish(step)
        else:
            return self._continue_or_finish(step)

    def _handle_exec_result(self, step: int, result: NodeResult) -> Tuple[List[OpNode], bool]:
        """Handle exec result: proceed to review

        修复：包装 ExecutionResult 到 outputs
        """
        if result.status == "success":
            # ===== 修复：包装 ExecutionResult 到 outputs =====
            if not result.outputs or not isinstance(result.outputs, dict):
                if hasattr(result, 'return_value') and result.return_value:
                    exec_result = result.return_value
                    # ExecutionResult 对象转为字典
                    result.outputs = {
                        "success": exec_result.success,
                        "stdout": exec_result.stdout,
                        "stderr": exec_result.stderr,
                        "exc_type": exec_result.exc_type,
                        "metadata": exec_result.metadata,
                        "code": getattr(exec_result, 'code', ""),  # 保留原始代码
                    }
                else:
                    result.outputs = {"success": False, "stdout": "", "stderr": "No output"}

            return [
                self._build_review_node(
                    step=step, exec_result=result.outputs, depends_on=[result.node_id]
                )
            ], False
        else:
            if self.enable_debug_branch:
                return [], True
            else:
                return self._continue_or_finish(step)

    def _handle_stepwise_result(
        self, step: int, sub_step: int, result: NodeResult
    ) -> Tuple[List[OpNode], bool]:
        """Handle stepwise execution result: continue to next sub-step or finish"""
        if result.status == "success":
            decomposed_plan = getattr(self, "_decomposed_plan_cache", {}).get(step, [])
            next_sub_step = sub_step + 1

            if next_sub_step < len(decomposed_plan):
                next_task = decomposed_plan[next_sub_step]
                return [
                    self._build_stepwise_node(
                        step=step,
                        sub_step=next_sub_step,
                        code=next_task.get("code", ""),
                        depends_on=[result.node_id],
                    )
                ], False
            else:
                return [
                    self._build_review_node(
                        step=step, exec_result=result.outputs, depends_on=[result.node_id]
                    )
                ], False
        else:
            self._retry_counts[result.node_id] = self._retry_counts.get(result.node_id, 0) + 1
            if self._retry_counts[result.node_id] < self.max_retries:
                return [
                    self._build_stepwise_node(
                        step=step,
                        sub_step=sub_step,
                        code="",
                        depends_on=[result.node_id],
                        is_retry=True,
                    )
                ], False
            else:
                return self._continue_or_finish(step)

    def _handle_review_result(self, step: int, result: NodeResult) -> Tuple[List[OpNode], bool]:
        """Handle review result: continue or finish"""
        return self._continue_or_finish(step)

    def _continue_or_finish(self, step: int) -> Tuple[List[OpNode], bool]:
        """Decide whether to continue with next iteration or finish

        修复：确保 Gen_{step+1} 依赖 Review_{step}
        """
        next_step = step + 1

        # ===== 修复：正确的依赖关系 =====
        # Gen_{next_step} 应该依赖 Review_{step}
        review_node_id = self._review_node_id(step)

        if next_step < self.max_iterations:
            logger.debug(f"Creating Gen_{next_step} with dependency on {review_node_id}")
            return [
                self._build_gen_node(
                    step=next_step,
                    depends_on=[review_node_id]  # 依赖 Review 节点
                )
            ], False
        else:
            # Finalize 节点依赖最后一个 Review
            logger.debug(f"Creating Finalize node with dependency on {review_node_id}")
            return [self._build_finalize_node(depends_on=[review_node_id])], False

    def get_result(self) -> Any:
        return dict(self._final_result)


class AutoMindWorkflow(AIDEWorkflow):
    """
    Implements the AUTOMIND iterative search algorithm.
    This workflow extends AIDE by incorporating a knowledge base (VDB),
    a self-adaptive coding strategy (one-pass vs. stepwise), and more
    sophisticated context management for complex tasks.
    """

    def __init__(
        self,
        operators: Dict[str, Any],
        services: Dict[str, Any],
        agent_config: Dict[str, Any],
        benchmark: Optional[BaseBenchmark] = None,
    ):
        """
        Initializes the AutoMindWorkflow, building upon the AIDE base.
        """
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

        task_goal = task_context.get("goal_and_data", "Solve the data science task.")
        io_instructions = task_context.get("io_instructions", "N/A")

        # 2. Create a prompt
        if parent_node is None:
            # For new drafts, retrieve similar examples from the knowledge base.
            retrieved_knowledge = ""
            if self.vdb_service:
                cases = self.vdb_service.retrieve_cases(task_goal, top_k=2)
                retrieved_knowledge = await self.context_manager.summarize_knowledge(
                    cases, task_goal
                )

            prompt = create_draft_prompt(
                task_context,
                self.state.generate_summary(),
                retrieved_knowledge,
                visualization_policy=self.visualization_policy,
            )
        elif parent_node.is_buggy:
            error_summary = self.context_manager.summarize_error(
                parent_node.term_out, parent_node.exc_type
            )
            prompt = create_debug_prompt(
                task_context,
                parent_node.code,
                error_summary,
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

        # 3. Generate initial plan and one-pass code.
        plan, one_pass_code = await self.generate_op(system_prompt=prompt)

        # 4. Apply the self-adaptive coding strategy for new drafts.
        use_adaptive = self.complexity_scorer_op and self.plan_decomposer_op
        if use_adaptive and parent_node is None:
            final_code, exec_result = await self._execute_step_adaptively(
                plan, one_pass_code, task_goal, io_instructions
            )
        else:
            # For simpler tasks, improvements, or debugging, use the one-pass code.
            final_code = one_pass_code
            exec_result = await self.execute_op(code=final_code, mode="script")

        # 5. Create a new node and absorb the execution result.
        new_node = Node(plan=plan, code=final_code)
        new_node.absorb_exec_result(exec_result)

        if exec_result.success:
            submission_file_in_sandbox = (
                self.sandbox_service.workspace.get_path("sandbox_workdir") / output_path.name
            )

            maximize = self._maximize_from_task_context(task_context)

            if not submission_file_in_sandbox.exists():
                new_node.is_buggy = True
                new_node.analysis = (
                    "Code executed without error, but failed to produce the required output file."
                )
                new_node.metric = MetricValue(value=0.0, maximize=maximize)
            elif self.benchmark and hasattr(self.benchmark, "grade"):
                logger.info(
                    f"Performing grounded validation using benchmark grader on '{submission_file_in_sandbox}'..."
                )
                score = await self._grade_submission_with_context(
                    submission_file_in_sandbox, output_path
                )

                if score > 0:
                    new_node.is_buggy = False
                    new_node.metric = MetricValue(value=score, maximize=maximize)
                    logger.info(f"Grounded validation PASSED. Score: {score:.4f}")
                    try:
                        review = await self.review_op(
                            prompt_context={
                                "task": task_context,
                                "code": new_node.code,
                                "output": new_node.term_out,
                                "grounded_metric_value": score,
                            }
                        )
                    except LLMServiceError as exc:
                        logger.warning("Grounded review failed after successful grading; preserving grounded score: %s", exc)
                        new_node.analysis = self._grounded_review_fallback_summary(
                            score=score,
                            error=exc,
                        )
                    else:
                        self._apply_grounded_metric_to_review(
                            review,
                            score=score,
                            task_context=task_context,
                        )
                        new_node.analysis = (
                            f"Grounded Score: {score:.4f}. Reviewer Summary: {review.summary}"
                        )
                else:
                    new_node.is_buggy = True
                    new_node.metric = MetricValue(value=score, maximize=maximize)
                    new_node.analysis = "Grounded validation FAILED: The generated submission file was invalid or scored 0.0."
                    logger.warning(f"Grounded validation FAILED. Score: {score}")
            else:
                logger.warning(
                    "No benchmark with 'grade' method found. Falling back to unreliable LLM-based review."
                )
                review = await self.review_op(
                    prompt_context={
                        "task": task_context,
                        "code": new_node.code,
                        "output": new_node.term_out,
                    }
                )
                new_node.absorb_review(review, task_context)

        # 8. Add the new node to the search tree state.
        self.state.append(new_node, parent=parent_node)
        logger.info(
            f"Step {new_node.step} complete. Buggy: {new_node.is_buggy}. Metric: {new_node.metric}."
        )

    async def _execute_step_adaptively(
        self, plan: str, one_pass_code: str, task_goal: str, io_instructions: str
    ) -> tuple[str, ExecutionResult]:
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
                        logger.info(
                            f"Step {task.task_id}, Attempt {attempt + 1}/{max_step_retries}"
                        )

                        # Build a concise history of recent steps to provide context for the next step.
                        recent_history_str = self.context_manager.build_history_context(
                            history_steps, key_order=["task_id", "code", "output"]
                        )

                        if attempt == 0:
                            step_prompt = create_stepwise_code_prompt(
                                task_goal,
                                plan,
                                recent_history_str,
                                task.instruction,
                                io_instructions,
                            )
                        else:
                            error_summary = self.context_manager.summarize_error(
                                exec_result.stderr, exec_result.exc_type
                            )
                            step_failure_history.append(
                                {
                                    "attempt": attempt,
                                    "code": truncate_output(current_code, MAX_OUTPUT_CHARS),
                                    "error": error_summary,
                                }
                            )

                            formatted_failure_history = "\n".join(
                                [
                                    f"--- Attempt {f['attempt']} Failed ---\nCode:\n```python\n{f['code']}\n```\nError: {f['error']}\n---"
                                    for f in step_failure_history
                                ]
                            )
                            safe_failure_history = truncate_output(
                                formatted_failure_history, MAX_HISTORY_CHARS
                            )

                            step_prompt = create_stepwise_debug_prompt(
                                task_goal,
                                plan,
                                recent_history_str,
                                task.instruction,
                                current_code,
                                safe_failure_history,
                                io_instructions,
                            )

                        _, current_code = await self.generate_op(system_prompt=step_prompt)
                        exec_result = await self.execute_op(
                            code=current_code, mode="notebook", executor_context=notebook
                        )

                        if exec_result.success:
                            step_succeeded = True
                            break

                    if not step_succeeded:
                        logger.error(
                            f"Step {task.task_id} failed after {max_step_retries} attempts. Aborting stepwise execution."
                        )
                        final_exec_result = exec_result  # Capture the failed result
                        break

                    step_codes.append(
                        f"# --- Step {task.task_id}: {task.instruction} ---\n{current_code}"
                    )
                    # Record the successful step for future context.
                    history_steps.append(
                        {
                            "task_id": task.task_id,
                            "code": truncate_output(current_code, MAX_OUTPUT_CHARS),
                            "output": truncate_output(exec_result.stdout, MAX_OUTPUT_CHARS),
                        }
                    )
                    final_exec_result = exec_result  # Update with the latest successful result

            final_code = "\n\n".join(step_codes)
            exec_result = final_exec_result

        return final_code, exec_result
