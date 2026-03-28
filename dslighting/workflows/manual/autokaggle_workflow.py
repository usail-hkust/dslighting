import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dslighting.core.visualization_policy import (
    resolve_visualization_policy_from_agent_config,
)
from dslighting.core.types import StepPlan, TaskContract
from dslighting.ops.presets.autokaggle import (
    AutoKaggleDeveloperOperator,
    AutoKagglePlannerOperator,
    AutoKaggleReviewerOperator,
    AutoKaggleSummarizerOperator,
    DynamicValidationOperator,
    TaskDeconstructionOperator,
)
from dslighting.runtime.dag import GraphDelta, NodeResult, OpNode, WorkflowGraphSpec
from dslighting.services.llm import LLMService
from dslighting.services.sandbox import SandboxService
from dslighting.services.workspace import WorkspaceService
from dslighting.state.autokaggle import AttemptMemory, AutoKaggleState, PhaseMemory
from dslighting.workflows.base import BaseWorkflow

logger = logging.getLogger(__name__)


class AutoKaggleWorkflow(BaseWorkflow):
    """Implements the Contract-Driven Dynamic AutoKaggle Standard Operating Procedure."""

    _NODE_NAMESPACE = "autokaggle"
    _BRANCH_DIRNAME = ".autokaggle_branches"

    def __init__(self, operators: Dict[str, Any], services: Dict[str, Any], agent_config: Dict[str, Any]):
        super().__init__(operators, services, agent_config)

        required_services = ["workspace", "llm", "sandbox"]
        for service_name in required_services:
            if service_name not in services:
                raise ValueError(f"AutoKaggleWorkflow requires '{service_name}' service")

        self.workspace: WorkspaceService = services["workspace"]
        self.llm_service: LLMService = services["llm"]
        self.sandbox: SandboxService = services["sandbox"]

        sop_config = agent_config.get("autokaggle", {})
        visualization_policy = resolve_visualization_policy_from_agent_config(agent_config)

        validator = DynamicValidationOperator(llm_service=self.llm_service)
        self.operators = {
            "deconstructor": TaskDeconstructionOperator(llm_service=self.llm_service),
            "planner": AutoKagglePlannerOperator(llm_service=self.llm_service),
            "developer": AutoKaggleDeveloperOperator(
                llm_service=self.llm_service,
                sandbox_service=self.sandbox,
                validator=validator,
                visualization_policy=visualization_policy,
            ),
            "reviewer": AutoKaggleReviewerOperator(
                llm_service=self.llm_service,
                visualization_policy=visualization_policy,
            ),
            "summarizer": AutoKaggleSummarizerOperator(llm_service=self.llm_service),
        }

        self.config = {
            "max_attempts_per_phase": sop_config.get("max_attempts_per_phase", 5),
            "success_threshold": sop_config.get("success_threshold", 3.0),
            "visualization_policy": visualization_policy.value,
        }

    # ---------------------------------------------------------------------
    # Traditional path (kept for compatibility)
    # ---------------------------------------------------------------------

    async def solve(self, description: str, io_instructions: str, data_dir: Path, output_path: Path) -> None:
        logger.info("Starting Stateful Contract-Driven Dynamic SOP Workflow...")

        task_contract = await self._deconstruct_task(description, io_instructions)
        dynamic_phases = await self.operators["planner"].plan_phases(task_contract)

        state = AutoKaggleState(
            contract=task_contract,
            dynamic_phases=dynamic_phases,
            io_instructions=io_instructions,
            full_task_description=description,
        )

        for phase_index, phase_goal in enumerate(state.dynamic_phases):
            logger.info(
                "--- Starting Dynamic Phase %s/%s: '%s' ---",
                phase_index + 1,
                len(state.dynamic_phases),
                phase_goal,
            )

            current_phase_memory = PhaseMemory(phase_goal=phase_goal)
            phase_succeeded = False

            for attempt_index in range(self._max_attempts_per_phase()):
                logger.info("--- Phase '%s', Attempt %s ---", phase_goal, attempt_index + 1)

                step_plan: StepPlan = await self.operators["planner"].plan_step_details(state, phase_goal)
                dev_result = await self.operators["developer"](
                    state,
                    phase_goal,
                    step_plan.plan,
                    current_phase_memory.attempts,
                )
                review_result = await self.operators["reviewer"](
                    state,
                    phase_goal,
                    dev_result,
                    plan=step_plan.plan,
                )

                normalized_dev_result = self._normalize_dev_result(dev_result)
                artifacts_ok = self._check_planned_artifacts(
                    dev_result=normalized_dev_result,
                    step_plan=step_plan,
                    phase_goal=phase_goal,
                    state=state,
                )
                self._append_attempt_memory(
                    phase_memory=current_phase_memory,
                    attempt_index=attempt_index,
                    step_plan=step_plan,
                    dev_result=normalized_dev_result,
                    review_result=review_result,
                )

                if self._is_attempt_success(
                    dev_result=normalized_dev_result,
                    artifacts_ok=artifacts_ok,
                    review_result=review_result,
                    state=state,
                    step_plan=step_plan,
                ):
                    logger.info("--- Phase '%s' Succeeded ---", phase_goal)
                    phase_succeeded = True
                    self._register_phase_artifacts(
                        state=state,
                        phase_memory=current_phase_memory,
                        phase_goal=phase_goal,
                        output_files=step_plan.output_files,
                    )
                    break

                logger.warning(
                    "Attempt failed. Code Success: %s. Artifacts Produced: %s. Score: %s. Retrying...",
                    normalized_dev_result.get("status"),
                    artifacts_ok,
                    self._extract_review_score(review_result),
                )

            if not phase_succeeded:
                logger.error(
                    "--- Phase '%s' FAILED after all attempts. Aborting workflow. ---",
                    phase_goal,
                )
                return

            summary_report = await self.operators["summarizer"](state, current_phase_memory)
            current_phase_memory.final_report = summary_report
            current_phase_memory.is_successful = True
            state.phase_history.append(current_phase_memory)

        logger.info("All dynamic phases completed successfully.")
        self._collect_final_submission(state=state, output_path=output_path)

    # ---------------------------------------------------------------------
    # Declarative DAG path
    # ---------------------------------------------------------------------

    def build_operator_graph(
        self,
        *,
        task_id: str,
        description: str,
        io_instructions: str,
        data_dir: Path,
        output_path: Path,
        dag_options: Any = None,
    ) -> WorkflowGraphSpec:
        parallel_drafts = self._resolve_parallel_drafts(dag_options)
        branch_budget = self._resolve_branch_budget(dag_options)

        dag_state: Dict[str, Any] = {
            "task_id": task_id,
            "description": description,
            "io_instructions": io_instructions,
            "data_dir": data_dir,
            "output_path": output_path,
            "state": None,
            "phase_index": 0,
            "attempt_index": 0,
            "current_phase_memory": None,
            "active_attempt": None,
            "last_step_plan": None,
            "last_dev_result": None,
            "last_review_result": None,
            "parallel_drafts": parallel_drafts,
            "branch_budget": branch_budget,
            "phase_branch_count": 0,
            "final_status": "running",
            "final_error": None,
            "final_submission_filename": None,
            "final_output_collected": False,
        }

        initial_nodes = [
            self._build_deconstruct_node(
                task_id=task_id,
                description=description,
                io_instructions=io_instructions,
            )
        ]
        return WorkflowGraphSpec(task_id=task_id, initial_nodes=initial_nodes, initial_state=dag_state)

    def on_operator_node_result(self, *, result: NodeResult, dag_state: Any) -> GraphDelta:
        if not isinstance(dag_state, dict):
            return GraphDelta(
                new_nodes=[],
                done=True,
                final_result={
                    "status": "failed",
                    "error": f"Invalid DAG state type: {type(dag_state).__name__}",
                    "output_path": None,
                },
            )

        task_id = str(dag_state.get("task_id") or result.task_id)

        if result.status != "success":
            dag_state["final_status"] = "failed"
            dag_state["final_error"] = result.error or f"Node failed: {result.node_id}"
            return GraphDelta(new_nodes=[], done=True, final_result=self._build_dag_final_result(dag_state))

        suffix = self._node_suffix(task_id=task_id, node_id=result.node_id)
        if suffix is None:
            dag_state["final_status"] = "failed"
            dag_state["final_error"] = f"Unexpected node id: {result.node_id}"
            return GraphDelta(new_nodes=[], done=True, final_result=self._build_dag_final_result(dag_state))

        if suffix == "deconstruct":
            contract = self._extract_task_contract(result)
            if contract is None:
                dag_state["final_status"] = "failed"
                dag_state["final_error"] = "Deconstructor did not return a valid TaskContract"
                return GraphDelta(new_nodes=[], done=True, final_result=self._build_dag_final_result(dag_state))

            dag_state["state"] = AutoKaggleState(
                contract=contract,
                dynamic_phases=[],
                io_instructions=str(dag_state.get("io_instructions") or ""),
                full_task_description=str(dag_state.get("description") or ""),
            )
            return GraphDelta(
                new_nodes=[
                    self._build_plan_phases_node(
                        task_id=task_id,
                        contract=contract,
                        depends_on=[result.node_id],
                    )
                ],
                done=False,
            )

        if suffix == "plan_phases":
            state = dag_state.get("state")
            if not isinstance(state, AutoKaggleState):
                dag_state["final_status"] = "failed"
                dag_state["final_error"] = "Workflow state is not initialized before phase planning"
                return GraphDelta(new_nodes=[], done=True, final_result=self._build_dag_final_result(dag_state))

            dynamic_phases = self._extract_phase_list(result)
            state.dynamic_phases = dynamic_phases
            dag_state["phase_index"] = 0
            dag_state["attempt_index"] = 0
            dag_state["phase_branch_count"] = 0
            dag_state["active_attempt"] = None

            if not dynamic_phases:
                # Keep compatibility with solve(): no phases -> still run final artifact collection.
                return GraphDelta(
                    new_nodes=[
                        self._build_finalize_node(
                            task_id=task_id,
                            state=state,
                            output_path=Path(dag_state["output_path"]),
                            depends_on=[result.node_id],
                        )
                    ],
                    done=False,
                )

            phase_goal = dynamic_phases[0]
            phase_memory = PhaseMemory(phase_goal=phase_goal)
            dag_state["current_phase_memory"] = phase_memory
            return GraphDelta(
                new_nodes=[
                    self._build_step_plan_node(
                        task_id=task_id,
                        phase_index=0,
                        attempt_index=0,
                        state=state,
                        phase_goal=phase_goal,
                        depends_on=[result.node_id],
                    )
                ],
                done=False,
            )

        if suffix.startswith("step_plan:"):
            state = dag_state.get("state")
            phase_memory = dag_state.get("current_phase_memory")
            if not isinstance(state, AutoKaggleState) or not isinstance(phase_memory, PhaseMemory):
                dag_state["final_status"] = "failed"
                dag_state["final_error"] = "Missing state or phase memory before develop step"
                return GraphDelta(new_nodes=[], done=True, final_result=self._build_dag_final_result(dag_state))

            step_plan = self._extract_step_plan(result)
            if step_plan is None:
                dag_state["final_status"] = "failed"
                dag_state["final_error"] = "Planner did not return a valid StepPlan"
                return GraphDelta(new_nodes=[], done=True, final_result=self._build_dag_final_result(dag_state))

            dag_state["last_step_plan"] = step_plan
            phase_index = int(dag_state.get("phase_index", 0))
            attempt_index = int(dag_state.get("attempt_index", 0))
            phase_goal = phase_memory.phase_goal

            draft_count = self._effective_draft_count(dag_state=dag_state)
            dag_state["phase_branch_count"] = int(dag_state.get("phase_branch_count", 0)) + draft_count

            attempt_context: Dict[str, Any] = {
                "phase_index": phase_index,
                "attempt_index": attempt_index,
                "phase_goal": phase_goal,
                "step_plan": step_plan,
                "draft_count": draft_count,
                "drafts": {},
            }

            develop_nodes: List[OpNode] = []
            for draft_index in range(draft_count):
                branch_workdir = self._prepare_branch_workspace(
                    task_id=task_id,
                    phase_index=phase_index,
                    attempt_index=attempt_index,
                    draft_index=draft_index,
                    state=state,
                    step_plan=step_plan,
                )
                develop_node = self._build_develop_node(
                    task_id=task_id,
                    phase_index=phase_index,
                    attempt_index=attempt_index,
                    draft_index=draft_index,
                    state=state,
                    phase_goal=phase_goal,
                    step_plan=step_plan,
                    phase_memory=phase_memory,
                    branch_workdir=branch_workdir,
                    depends_on=[result.node_id],
                )
                attempt_context["drafts"][draft_index] = {
                    "branch_workdir": str(branch_workdir),
                    "dev_result": None,
                    "review_result": None,
                    "artifacts_ok": False,
                    "review_node_id": None,
                }
                develop_nodes.append(develop_node)

            dag_state["active_attempt"] = attempt_context
            return GraphDelta(new_nodes=develop_nodes, done=False)

        if suffix.startswith("develop:"):
            state = dag_state.get("state")
            phase_memory = dag_state.get("current_phase_memory")
            if not isinstance(state, AutoKaggleState) or not isinstance(phase_memory, PhaseMemory):
                dag_state["final_status"] = "failed"
                dag_state["final_error"] = "Missing state before review step"
                return GraphDelta(new_nodes=[], done=True, final_result=self._build_dag_final_result(dag_state))

            parsed_indices = self._parse_phase_attempt_draft_from_suffix(suffix=suffix, prefix="develop")
            if parsed_indices is None:
                dag_state["final_status"] = "failed"
                dag_state["final_error"] = f"Invalid develop node suffix: {suffix}"
                return GraphDelta(new_nodes=[], done=True, final_result=self._build_dag_final_result(dag_state))

            phase_index, attempt_index, draft_index = parsed_indices
            active_attempt = dag_state.get("active_attempt")
            if not isinstance(active_attempt, dict):
                dag_state["final_status"] = "failed"
                dag_state["final_error"] = "Missing active attempt context before review step"
                return GraphDelta(new_nodes=[], done=True, final_result=self._build_dag_final_result(dag_state))

            if (
                int(active_attempt.get("phase_index", -1)) != phase_index
                or int(active_attempt.get("attempt_index", -1)) != attempt_index
            ):
                dag_state["final_status"] = "failed"
                dag_state["final_error"] = "Active attempt context does not match develop node index"
                return GraphDelta(new_nodes=[], done=True, final_result=self._build_dag_final_result(dag_state))

            draft_state = active_attempt.get("drafts", {}).get(draft_index)
            if not isinstance(draft_state, dict):
                dag_state["final_status"] = "failed"
                dag_state["final_error"] = f"Missing draft state for draft_index={draft_index}"
                return GraphDelta(new_nodes=[], done=True, final_result=self._build_dag_final_result(dag_state))

            step_plan = active_attempt.get("step_plan")
            if not isinstance(step_plan, StepPlan):
                dag_state["final_status"] = "failed"
                dag_state["final_error"] = "Missing step plan before review step"
                return GraphDelta(new_nodes=[], done=True, final_result=self._build_dag_final_result(dag_state))

            phase_goal = str(active_attempt.get("phase_goal") or phase_memory.phase_goal)
            dev_result = self._normalize_dev_result(result.outputs, fallback_error=result.error)
            draft_state["dev_result"] = dev_result
            dag_state["last_dev_result"] = dev_result

            review_node = self._build_review_node(
                task_id=task_id,
                phase_index=phase_index,
                attempt_index=attempt_index,
                draft_index=draft_index,
                state=state,
                phase_goal=phase_goal,
                dev_result=dev_result,
                step_plan=step_plan,
                depends_on=[result.node_id],
            )
            draft_state["review_node_id"] = review_node.node_id
            return GraphDelta(new_nodes=[review_node], done=False)

        if suffix.startswith("review:"):
            state = dag_state.get("state")
            phase_memory = dag_state.get("current_phase_memory")
            if not isinstance(state, AutoKaggleState) or not isinstance(phase_memory, PhaseMemory):
                dag_state["final_status"] = "failed"
                dag_state["final_error"] = "Missing state before review evaluation"
                return GraphDelta(new_nodes=[], done=True, final_result=self._build_dag_final_result(dag_state))

            parsed_indices = self._parse_phase_attempt_draft_from_suffix(suffix=suffix, prefix="review")
            if parsed_indices is None:
                dag_state["final_status"] = "failed"
                dag_state["final_error"] = f"Invalid review node suffix: {suffix}"
                return GraphDelta(new_nodes=[], done=True, final_result=self._build_dag_final_result(dag_state))

            phase_index, attempt_index, draft_index = parsed_indices
            active_attempt = dag_state.get("active_attempt")
            if not isinstance(active_attempt, dict):
                dag_state["final_status"] = "failed"
                dag_state["final_error"] = "Missing active attempt context before review evaluation"
                return GraphDelta(new_nodes=[], done=True, final_result=self._build_dag_final_result(dag_state))

            if (
                int(active_attempt.get("phase_index", -1)) != phase_index
                or int(active_attempt.get("attempt_index", -1)) != attempt_index
            ):
                dag_state["final_status"] = "failed"
                dag_state["final_error"] = "Active attempt context does not match review node index"
                return GraphDelta(new_nodes=[], done=True, final_result=self._build_dag_final_result(dag_state))

            draft_state = active_attempt.get("drafts", {}).get(draft_index)
            if not isinstance(draft_state, dict):
                dag_state["final_status"] = "failed"
                dag_state["final_error"] = f"Missing draft state for review draft_index={draft_index}"
                return GraphDelta(new_nodes=[], done=True, final_result=self._build_dag_final_result(dag_state))

            step_plan = active_attempt.get("step_plan")
            if not isinstance(step_plan, StepPlan):
                dag_state["final_status"] = "failed"
                dag_state["final_error"] = "Missing step plan before review evaluation"
                return GraphDelta(new_nodes=[], done=True, final_result=self._build_dag_final_result(dag_state))

            dev_result = draft_state.get("dev_result")
            if not isinstance(dev_result, dict):
                dag_state["final_status"] = "failed"
                dag_state["final_error"] = f"Missing develop result for review draft_index={draft_index}"
                return GraphDelta(new_nodes=[], done=True, final_result=self._build_dag_final_result(dag_state))

            phase_goal = str(active_attempt.get("phase_goal") or phase_memory.phase_goal)
            review_result = dict(result.outputs or {})
            dag_state["last_review_result"] = review_result

            branch_workdir = Path(str(draft_state.get("branch_workdir") or self._sandbox_workdir()))
            artifacts_ok = self._check_planned_artifacts(
                dev_result=dev_result,
                step_plan=step_plan,
                phase_goal=phase_goal,
                state=state,
                workspace_dir=branch_workdir,
            )

            draft_state["review_result"] = review_result
            draft_state["artifacts_ok"] = artifacts_ok

            self._append_attempt_memory(
                phase_memory=phase_memory,
                attempt_index=attempt_index,
                attempt_number=len(phase_memory.attempts),
                step_plan=step_plan,
                dev_result=dev_result,
                review_result=review_result,
            )

            if not self._all_attempt_drafts_reviewed(active_attempt):
                return GraphDelta(new_nodes=[], done=False)

            review_node_ids = self._collect_attempt_review_node_ids(active_attempt)
            depends_on = review_node_ids or [result.node_id]
            winner = self._select_best_draft(
                state=state,
                step_plan=step_plan,
                attempt_context=active_attempt,
            )

            dag_state["active_attempt"] = None

            if winner is not None:
                winner_draft_index, winner_payload = winner
                winner_dev_result = dict(winner_payload.get("dev_result") or {})
                winner_review_result = dict(winner_payload.get("review_result") or {})
                winner_branch_workdir = Path(
                    str(winner_payload.get("branch_workdir") or self._sandbox_workdir())
                )

                logger.info(
                    "Phase '%s' attempt %s selected draft #%s as winner.",
                    phase_goal,
                    attempt_index + 1,
                    winner_draft_index,
                )

                self._promote_branch_outputs(
                    branch_workdir=winner_branch_workdir,
                    output_files=step_plan.output_files,
                )

                dag_state["last_dev_result"] = winner_dev_result
                dag_state["last_review_result"] = winner_review_result
                self._register_phase_artifacts(
                    state=state,
                    phase_memory=phase_memory,
                    phase_goal=phase_goal,
                    output_files=step_plan.output_files,
                )
                return GraphDelta(
                    new_nodes=[
                        self._build_summarize_node(
                            task_id=task_id,
                            phase_index=phase_index,
                            state=state,
                            phase_memory=phase_memory,
                            depends_on=depends_on,
                        )
                    ],
                    done=False,
                )

            next_attempt = attempt_index + 1
            if next_attempt < self._max_attempts_per_phase():
                dag_state["attempt_index"] = next_attempt
                return GraphDelta(
                    new_nodes=[
                        self._build_step_plan_node(
                            task_id=task_id,
                            phase_index=phase_index,
                            attempt_index=next_attempt,
                            state=state,
                            phase_goal=phase_goal,
                            depends_on=depends_on,
                        )
                    ],
                    done=False,
                )

            dag_state["final_status"] = "failed"
            dag_state["final_error"] = (
                f"Phase '{phase_goal}' failed after {self._max_attempts_per_phase()} attempts"
            )
            logger.error("--- %s. Aborting workflow. ---", dag_state["final_error"])
            return GraphDelta(new_nodes=[], done=True, final_result=self._build_dag_final_result(dag_state))

        if suffix.startswith("summarize:"):
            state = dag_state.get("state")
            phase_memory = dag_state.get("current_phase_memory")
            if not isinstance(state, AutoKaggleState) or not isinstance(phase_memory, PhaseMemory):
                dag_state["final_status"] = "failed"
                dag_state["final_error"] = "Missing state before summarize handling"
                return GraphDelta(new_nodes=[], done=True, final_result=self._build_dag_final_result(dag_state))

            summary_report = self._extract_string_value(result)
            phase_memory.final_report = summary_report
            phase_memory.is_successful = True
            state.phase_history.append(phase_memory)

            current_phase_index = int(dag_state.get("phase_index", 0))
            next_phase_index = current_phase_index + 1
            if next_phase_index < len(state.dynamic_phases):
                next_phase_goal = state.dynamic_phases[next_phase_index]
                dag_state["phase_index"] = next_phase_index
                dag_state["attempt_index"] = 0
                dag_state["phase_branch_count"] = 0
                dag_state["active_attempt"] = None
                dag_state["current_phase_memory"] = PhaseMemory(phase_goal=next_phase_goal)
                dag_state["last_step_plan"] = None
                dag_state["last_dev_result"] = None
                dag_state["last_review_result"] = None
                return GraphDelta(
                    new_nodes=[
                        self._build_step_plan_node(
                            task_id=task_id,
                            phase_index=next_phase_index,
                            attempt_index=0,
                            state=state,
                            phase_goal=next_phase_goal,
                            depends_on=[result.node_id],
                        )
                    ],
                    done=False,
                )

            output_path = Path(dag_state["output_path"])
            return GraphDelta(
                new_nodes=[
                    self._build_finalize_node(
                        task_id=task_id,
                        state=state,
                        output_path=output_path,
                        depends_on=[result.node_id],
                    )
                ],
                done=False,
            )

        if suffix == "finalize":
            final_info = dict(result.outputs or {})
            dag_state["final_submission_filename"] = final_info.get("final_submission_filename")
            dag_state["final_output_collected"] = bool(final_info.get("final_output_collected", False))
            if dag_state["final_output_collected"]:
                dag_state["final_status"] = "success"
                dag_state["final_error"] = None
            else:
                dag_state["final_status"] = "failed"
                dag_state["final_error"] = final_info.get("final_error") or dag_state.get("final_error")
            return GraphDelta(new_nodes=[], done=True, final_result=self._build_dag_final_result(dag_state))

        dag_state["final_status"] = "failed"
        dag_state["final_error"] = f"Unhandled node transition for suffix: {suffix}"
        return GraphDelta(new_nodes=[], done=True, final_result=self._build_dag_final_result(dag_state))

    def finalize_operator_graph(self, *, task_id: str, dag_state: Any) -> Any:
        _ = task_id
        return self._build_dag_final_result(dag_state)

    def _resolve_parallel_drafts(self, dag_options: Any) -> int:
        if dag_options is None:
            return 1
        try:
            return max(1, int(getattr(dag_options, "parallel_drafts", 1) or 1))
        except (TypeError, ValueError):
            return 1

    def _resolve_branch_budget(self, dag_options: Any) -> Optional[int]:
        if dag_options is None:
            return None
        try:
            budget = int(getattr(dag_options, "branch_budget", None))
        except (TypeError, ValueError):
            return None
        return budget if budget > 0 else None

    def _effective_draft_count(self, *, dag_state: Dict[str, Any]) -> int:
        configured = max(1, int(dag_state.get("parallel_drafts", 1) or 1))
        attempt_index = max(0, int(dag_state.get("attempt_index", 0) or 0))
        desired = configured if attempt_index > 0 else 1

        branch_budget = dag_state.get("branch_budget")
        if branch_budget is None:
            return desired

        try:
            budget = int(branch_budget)
        except (TypeError, ValueError):
            return desired

        if budget <= 0:
            return desired

        used = max(0, int(dag_state.get("phase_branch_count", 0) or 0))
        remaining = budget - used
        if remaining <= 1:
            return 1
        return max(1, min(desired, remaining))

    def _parse_phase_attempt_draft_from_suffix(
        self,
        *,
        suffix: str,
        prefix: str,
    ) -> Optional[Tuple[int, int, int]]:
        parts = [part.strip() for part in str(suffix).split(":")]
        if len(parts) < 3 or parts[0] != prefix:
            return None

        try:
            phase_index = int(parts[1])
            attempt_index = int(parts[2])
            draft_index = int(parts[3]) if len(parts) >= 4 else 0
        except (TypeError, ValueError):
            return None

        if phase_index < 0 or attempt_index < 0 or draft_index < 0:
            return None
        return phase_index, attempt_index, draft_index

    def _sanitize_task_component(self, task_id: str) -> str:
        safe = "".join(ch if (ch.isalnum() or ch in {"-", "_"}) else "_" for ch in str(task_id))
        safe = safe.strip("_")
        return safe or "task"

    def _branch_workdir(
        self,
        *,
        task_id: str,
        phase_index: int,
        attempt_index: int,
        draft_index: int,
    ) -> Path:
        return (
            self._sandbox_workdir()
            / self._BRANCH_DIRNAME
            / self._sanitize_task_component(task_id)
            / f"p{phase_index}_a{attempt_index}_d{draft_index}"
        )

    def _normalize_relative_path(self, value: Any) -> Optional[str]:
        raw = str(value or "").strip()
        if not raw:
            return None
        path = Path(raw)
        if path.is_absolute():
            return None
        if any(part == ".." for part in path.parts):
            return None
        normalized = str(path)
        if normalized in {"", "."}:
            return None
        return normalized

    def _collect_branch_input_candidates(
        self,
        *,
        state: AutoKaggleState,
        step_plan: StepPlan,
    ) -> List[str]:
        candidates: Dict[str, None] = {}

        def _add(candidate: Any) -> None:
            normalized = self._normalize_relative_path(candidate)
            if normalized:
                candidates[normalized] = None

        for artifact in state.contract.input_files:
            _add(getattr(artifact, "filename", ""))

        for filename in state.global_artifacts.keys():
            _add(filename)

        for filename in step_plan.input_artifacts:
            _add(filename)

        _add("sample_submission.csv")
        sandbox_workdir = self._sandbox_workdir()
        try:
            for child in sandbox_workdir.iterdir():
                if not child.is_file():
                    continue
                lowered = child.name.lower()
                if child.suffix.lower() == ".csv" and "sample" in lowered and "submission" in lowered:
                    _add(child.name)
        except Exception:
            pass

        return sorted(candidates.keys())

    def _materialize_branch_input(
        self,
        *,
        root_workdir: Path,
        branch_workdir: Path,
        relative_path: str,
    ) -> None:
        source = root_workdir / relative_path
        if not source.exists():
            return

        destination = branch_workdir / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)

        if destination.exists() or destination.is_symlink():
            if destination.is_dir() and not destination.is_symlink():
                shutil.rmtree(destination)
            else:
                destination.unlink()

        try:
            os.symlink(source, destination, target_is_directory=source.is_dir())
            return
        except Exception:
            pass

        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            shutil.copy2(source, destination)

    def _prepare_branch_workspace(
        self,
        *,
        task_id: str,
        phase_index: int,
        attempt_index: int,
        draft_index: int,
        state: AutoKaggleState,
        step_plan: StepPlan,
    ) -> Path:
        branch_workdir = self._branch_workdir(
            task_id=task_id,
            phase_index=phase_index,
            attempt_index=attempt_index,
            draft_index=draft_index,
        )

        if branch_workdir.exists():
            shutil.rmtree(branch_workdir)
        branch_workdir.mkdir(parents=True, exist_ok=True)

        root_workdir = self._sandbox_workdir()
        for relative_path in self._collect_branch_input_candidates(state=state, step_plan=step_plan):
            self._materialize_branch_input(
                root_workdir=root_workdir,
                branch_workdir=branch_workdir,
                relative_path=relative_path,
            )

        return branch_workdir

    def _all_attempt_drafts_reviewed(self, attempt_context: Dict[str, Any]) -> bool:
        drafts = attempt_context.get("drafts")
        if not isinstance(drafts, dict) or not drafts:
            return False

        for payload in drafts.values():
            if not isinstance(payload, dict):
                return False
            if not isinstance(payload.get("review_result"), dict):
                return False
        return True

    def _collect_attempt_review_node_ids(self, attempt_context: Dict[str, Any]) -> List[str]:
        drafts = attempt_context.get("drafts")
        if not isinstance(drafts, dict):
            return []

        review_ids: List[str] = []
        for draft_index in sorted(drafts.keys()):
            payload = drafts.get(draft_index)
            if not isinstance(payload, dict):
                continue
            node_id = payload.get("review_node_id")
            if isinstance(node_id, str) and node_id.strip():
                review_ids.append(node_id)
        return review_ids

    def _select_best_draft(
        self,
        *,
        state: AutoKaggleState,
        step_plan: StepPlan,
        attempt_context: Dict[str, Any],
    ) -> Optional[Tuple[int, Dict[str, Any]]]:
        drafts = attempt_context.get("drafts")
        if not isinstance(drafts, dict):
            return None

        best: Optional[Tuple[int, Dict[str, Any]]] = None
        best_key: Optional[Tuple[float, int]] = None

        for draft_index in sorted(drafts.keys()):
            payload = drafts.get(draft_index)
            if not isinstance(payload, dict):
                continue
            dev_result = payload.get("dev_result")
            review_result = payload.get("review_result")
            artifacts_ok = bool(payload.get("artifacts_ok", False))
            if not isinstance(dev_result, dict) or not isinstance(review_result, dict):
                continue

            if not self._is_attempt_success(
                dev_result=dev_result,
                artifacts_ok=artifacts_ok,
                review_result=review_result,
                state=state,
                step_plan=step_plan,
            ):
                continue

            score = self._extract_review_score(review_result)
            candidate_key = (score, -int(draft_index))
            if best is None or best_key is None or candidate_key > best_key:
                best = (int(draft_index), payload)
                best_key = candidate_key

        return best

    def _promote_branch_outputs(self, *, branch_workdir: Path, output_files: List[str]) -> None:
        root_workdir = self._sandbox_workdir()

        for filename in output_files:
            relative_path = self._normalize_relative_path(filename)
            if not relative_path:
                continue

            source_path = branch_workdir / relative_path
            if not source_path.exists():
                continue

            destination_path = root_workdir / relative_path
            destination_path.parent.mkdir(parents=True, exist_ok=True)

            if destination_path.exists() or destination_path.is_symlink():
                if destination_path.is_dir() and not destination_path.is_symlink():
                    shutil.rmtree(destination_path)
                else:
                    destination_path.unlink()

            if source_path.is_dir():
                shutil.copytree(source_path, destination_path)
            else:
                shutil.copy2(source_path, destination_path)

    # ---------------------------------------------------------------------
    # DAG node builders
    # ---------------------------------------------------------------------

    def _node_id(self, task_id: str, *parts: Any) -> str:
        suffix = ":".join(str(part) for part in parts)
        return f"{task_id}:{self._NODE_NAMESPACE}:{suffix}"

    def _node_suffix(self, *, task_id: str, node_id: str) -> Optional[str]:
        prefix = f"{task_id}:{self._NODE_NAMESPACE}:"
        if not node_id.startswith(prefix):
            return None
        return node_id[len(prefix):]

    def _build_deconstruct_node(self, *, task_id: str, description: str, io_instructions: str) -> OpNode:
        full_context_for_deconstructor = f"{description}\n\n{io_instructions}"
        return OpNode(
            node_id=self._node_id(task_id, "deconstruct"),
            task_id=task_id,
            op_type="llm",
            operator_name="autokaggle.deconstruct",
            depends_on=[],
            payload={
                "callable": self.operators["deconstructor"],
                "kwargs": {"description": full_context_for_deconstructor},
            },
            priority=100,
            estimated_runtime_seconds=20.0,
        )

    def _build_plan_phases_node(self, *, task_id: str, contract: TaskContract, depends_on: List[str]) -> OpNode:
        return OpNode(
            node_id=self._node_id(task_id, "plan_phases"),
            task_id=task_id,
            op_type="llm",
            operator_name="autokaggle.plan_phases",
            depends_on=list(depends_on),
            payload={
                "callable": self.operators["planner"].plan_phases,
                "kwargs": {"contract": contract},
            },
            priority=90,
            estimated_runtime_seconds=20.0,
        )

    def _build_step_plan_node(
        self,
        *,
        task_id: str,
        phase_index: int,
        attempt_index: int,
        state: AutoKaggleState,
        phase_goal: str,
        depends_on: List[str],
    ) -> OpNode:
        return OpNode(
            node_id=self._node_id(task_id, "step_plan", phase_index, attempt_index),
            task_id=task_id,
            op_type="llm",
            operator_name="autokaggle.step_plan",
            depends_on=list(depends_on),
            payload={
                "callable": self.operators["planner"].plan_step_details,
                "kwargs": {"state": state, "phase_goal": phase_goal},
            },
            priority=80,
            estimated_runtime_seconds=20.0,
        )

    def _build_develop_node(
        self,
        *,
        task_id: str,
        phase_index: int,
        attempt_index: int,
        draft_index: int,
        state: AutoKaggleState,
        phase_goal: str,
        step_plan: StepPlan,
        phase_memory: PhaseMemory,
        branch_workdir: Path,
        depends_on: List[str],
    ) -> OpNode:
        return OpNode(
            node_id=self._node_id(task_id, "develop", phase_index, attempt_index, draft_index),
            task_id=task_id,
            op_type="sandbox",
            operator_name="autokaggle.develop",
            depends_on=list(depends_on),
            payload={
                "callable": self.operators["developer"],
                "kwargs": {
                    "state": state,
                    "phase_goal": phase_goal,
                    "plan": step_plan.plan,
                    "attempt_history": phase_memory.attempts,
                    "branch_workdir": str(branch_workdir),
                },
            },
            priority=70,
            estimated_runtime_seconds=120.0,
        )

    def _build_review_node(
        self,
        *,
        task_id: str,
        phase_index: int,
        attempt_index: int,
        draft_index: int,
        state: AutoKaggleState,
        phase_goal: str,
        dev_result: Dict[str, Any],
        step_plan: StepPlan,
        depends_on: List[str],
    ) -> OpNode:
        return OpNode(
            node_id=self._node_id(task_id, "review", phase_index, attempt_index, draft_index),
            task_id=task_id,
            op_type="llm",
            operator_name="autokaggle.review",
            depends_on=list(depends_on),
            payload={
                "callable": self.operators["reviewer"],
                "kwargs": {
                    "state": state,
                    "phase_goal": phase_goal,
                    "dev_result": dev_result,
                    "plan": step_plan.plan,
                },
            },
            priority=60,
            estimated_runtime_seconds=20.0,
        )

    def _build_summarize_node(
        self,
        *,
        task_id: str,
        phase_index: int,
        state: AutoKaggleState,
        phase_memory: PhaseMemory,
        depends_on: List[str],
    ) -> OpNode:
        return OpNode(
            node_id=self._node_id(task_id, "summarize", phase_index),
            task_id=task_id,
            op_type="llm",
            operator_name="autokaggle.summarize",
            depends_on=list(depends_on),
            payload={
                "callable": self.operators["summarizer"],
                "kwargs": {"state": state, "phase_memory": phase_memory},
            },
            priority=50,
            estimated_runtime_seconds=20.0,
        )

    def _build_finalize_node(
        self,
        *,
        task_id: str,
        state: AutoKaggleState,
        output_path: Path,
        depends_on: List[str],
    ) -> OpNode:
        return OpNode(
            node_id=self._node_id(task_id, "finalize"),
            task_id=task_id,
            op_type="custom",
            operator_name="autokaggle.finalize",
            depends_on=list(depends_on),
            payload={
                "callable": self._collect_final_submission,
                "kwargs": {"state": state, "output_path": output_path},
            },
            priority=40,
            estimated_runtime_seconds=10.0,
        )

    # ---------------------------------------------------------------------
    # Shared business helpers (used by both solve and declarative path)
    # ---------------------------------------------------------------------

    async def _deconstruct_task(self, description: str, io_instructions: str) -> TaskContract:
        full_context_for_deconstructor = f"{description}\n\n{io_instructions}"
        return await self.operators["deconstructor"](full_context_for_deconstructor)

    def _max_attempts_per_phase(self) -> int:
        try:
            return max(1, int(self.config.get("max_attempts_per_phase", 5)))
        except (TypeError, ValueError):
            return 5

    def _success_threshold(self) -> float:
        try:
            return float(self.config.get("success_threshold", 3.0))
        except (TypeError, ValueError):
            return 3.0

    def _sandbox_workdir(self) -> Path:
        return self.sandbox.workspace.get_path("sandbox_workdir")

    def _extract_review_score(self, review_result: Dict[str, Any]) -> float:
        raw_score = review_result.get("score", 1.0)
        try:
            return float(raw_score)
        except (TypeError, ValueError):
            return 1.0

    def _normalize_dev_result(self, dev_result: Dict[str, Any], fallback_error: Optional[str] = None) -> Dict[str, Any]:
        validation_result = dev_result.get("validation_result")
        format_validation_result = dev_result.get("format_validation_result")

        normalized_format_validation: Dict[str, Any] = {
            "passed": False,
            "errors": ["Format validation result missing."],
        }
        if isinstance(format_validation_result, dict):
            raw_errors = format_validation_result.get("errors", [])
            if isinstance(raw_errors, list):
                normalized_errors = [str(item) for item in raw_errors]
            elif raw_errors:
                normalized_errors = [str(raw_errors)]
            else:
                normalized_errors = []

            normalized_format_validation = {
                "passed": bool(format_validation_result.get("passed", False)),
                "errors": normalized_errors,
            }
            if isinstance(format_validation_result.get("files"), dict):
                normalized_format_validation["files"] = dict(format_validation_result.get("files") or {})

        return {
            "code": str(dev_result.get("code") or ""),
            "status": bool(dev_result.get("status", False)),
            "output": str(dev_result.get("output") or ""),
            "error": str(dev_result.get("error") or fallback_error or ""),
            "validation_result": dict(validation_result) if isinstance(validation_result, dict) else {},
            "format_validation_result": normalized_format_validation,
        }

    def _check_planned_artifacts(
        self,
        *,
        dev_result: Dict[str, Any],
        step_plan: StepPlan,
        phase_goal: str,
        state: Optional[AutoKaggleState] = None,
        workspace_dir: Optional[Path] = None,
    ) -> bool:
        all_artifacts_produced = True
        sandbox_workdir = workspace_dir or self._sandbox_workdir()
        required_outputs = {
            str(artifact.filename).strip()
            for artifact in (state.contract.output_files if state else [])
            if getattr(artifact, "filename", None)
        }

        if dev_result.get("status"):
            if not step_plan.output_files:
                logger.warning(
                    "Phase '%s' has no planned output files. Relying on reviewer score alone.",
                    phase_goal,
                )
            for filename in step_plan.output_files:
                normalized_name = str(filename).strip()
                if not normalized_name:
                    continue
                if not (sandbox_workdir / normalized_name).exists():
                    if normalized_name in required_outputs:
                        logger.error(
                            "Attempt failed: Required output artifact '%s' was NOT created.",
                            normalized_name,
                        )
                        all_artifacts_produced = False
                        break
                    logger.warning(
                        "Planned intermediate artifact '%s' was not created in '%s'; continuing because it is not a required final output.",
                        normalized_name,
                        sandbox_workdir,
                    )
        else:
            all_artifacts_produced = False

        return all_artifacts_produced

    def _append_attempt_memory(
        self,
        *,
        phase_memory: PhaseMemory,
        attempt_index: int,
        step_plan: StepPlan,
        dev_result: Dict[str, Any],
        review_result: Dict[str, Any],
        attempt_number: Optional[int] = None,
    ) -> None:
        resolved_attempt_number = attempt_index if attempt_number is None else int(attempt_number)
        attempt_memory = AttemptMemory(
            attempt_number=resolved_attempt_number,
            plan=step_plan.plan,
            code=dev_result.get("code", ""),
            execution_output=dev_result.get("output", ""),
            execution_error=dev_result.get("error"),
            validation_result=dev_result.get("validation_result", {}),
            review_score=self._extract_review_score(review_result),
            review_suggestion=str(review_result.get("suggestion", "No suggestion provided.")),
        )
        phase_memory.attempts.append(attempt_memory)

    def _is_attempt_success(
        self,
        *,
        dev_result: Dict[str, Any],
        artifacts_ok: bool,
        review_result: Dict[str, Any],
        state: AutoKaggleState,
        step_plan: StepPlan,
    ) -> bool:
        final_output_filenames = {
            str(artifact.filename).strip()
            for artifact in state.contract.output_files
            if getattr(artifact, "filename", None)
        }
        step_outputs = {str(name).strip() for name in step_plan.output_files if str(name).strip()}
        enforce_format_gate = bool(final_output_filenames and (final_output_filenames & step_outputs))

        format_validation_result = dev_result.get("format_validation_result")
        format_validation_passed = bool(
            isinstance(format_validation_result, dict)
            and format_validation_result.get("passed", False)
        )

        return (
            bool(dev_result.get("status"))
            and artifacts_ok
            and ((not enforce_format_gate) or format_validation_passed)
            and self._extract_review_score(review_result) >= self._success_threshold()
        )

    def _register_phase_artifacts(
        self,
        *,
        state: AutoKaggleState,
        phase_memory: PhaseMemory,
        phase_goal: str,
        output_files: List[str],
    ) -> None:
        for filename in output_files:
            description = f"Generated during phase: {phase_goal}"
            state.global_artifacts[filename] = description
            phase_memory.output_artifacts[filename] = description
            logger.info("Registered new artifact: %s", filename)

    def _collect_final_submission(self, state: AutoKaggleState, output_path: Path) -> Dict[str, Any]:
        final_submission_filename: Optional[str] = None
        final_output_collected = False
        final_error: Optional[str] = None

        if state.contract.output_files:
            final_submission_filename = state.contract.output_files[0].filename

        if final_submission_filename and final_submission_filename in state.global_artifacts:
            source_file = self._sandbox_workdir() / final_submission_filename
            destination_file = output_path

            logger.info(
                "Collecting final submission artifact '%s' to '%s'.",
                source_file,
                destination_file,
            )
            try:
                destination_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(source_file, destination_file)
                final_output_collected = True
                logger.info("Final artifact collected successfully.")
            except Exception as exc:  # pragma: no cover - defensive
                final_error = str(exc)
                logger.error("Failed to collect final artifact: %s", exc)
        else:
            final_error = (
                f"Workflow finished, but required output file '{final_submission_filename}' "
                "was not found in the global artifact registry."
            )
            logger.error(final_error)

        return {
            "final_submission_filename": final_submission_filename,
            "final_output_collected": final_output_collected,
            "final_error": final_error,
            "output_path": str(output_path),
        }

    # ---------------------------------------------------------------------
    # Result extraction helpers for declarative node outputs
    # ---------------------------------------------------------------------

    def _extract_task_contract(self, result: NodeResult) -> Optional[TaskContract]:
        candidate = result.outputs.get("value")
        if isinstance(candidate, TaskContract):
            return candidate
        if isinstance(candidate, dict):
            try:
                return TaskContract.model_validate(candidate)
            except Exception:
                return None
        return None

    def _extract_phase_list(self, result: NodeResult) -> List[str]:
        candidate = result.outputs.get("value")
        if isinstance(candidate, list):
            return [str(item) for item in candidate if str(item).strip()]
        if isinstance(candidate, tuple):
            return [str(item) for item in candidate if str(item).strip()]
        return []

    def _extract_step_plan(self, result: NodeResult) -> Optional[StepPlan]:
        candidate = result.outputs.get("value")
        if isinstance(candidate, StepPlan):
            return candidate
        if isinstance(candidate, dict):
            try:
                return StepPlan.model_validate(candidate)
            except Exception:
                return None
        return None

    def _extract_string_value(self, result: NodeResult) -> str:
        value = result.outputs.get("value")
        if value is None:
            return ""
        return str(value)

    # ---------------------------------------------------------------------
    # Final result shaping for declarative runtime
    # ---------------------------------------------------------------------

    def _build_dag_final_result(self, dag_state: Any) -> Dict[str, Any]:
        if not isinstance(dag_state, dict):
            return {
                "status": "failed",
                "error": f"Invalid DAG state type: {type(dag_state).__name__}",
                "output_path": None,
                "phases_total": 0,
                "phases_succeeded": 0,
                "final_submission_filename": None,
                "final_output_collected": False,
                "global_artifacts": {},
            }

        state = dag_state.get("state")
        phases_total = len(state.dynamic_phases) if isinstance(state, AutoKaggleState) else 0
        phases_succeeded = len(state.phase_history) if isinstance(state, AutoKaggleState) else 0
        global_artifacts = dict(state.global_artifacts) if isinstance(state, AutoKaggleState) else {}

        return {
            "status": str(dag_state.get("final_status") or "failed"),
            "error": dag_state.get("final_error"),
            "output_path": str(dag_state.get("output_path")) if dag_state.get("output_path") else None,
            "phases_total": phases_total,
            "phases_succeeded": phases_succeeded,
            "final_submission_filename": dag_state.get("final_submission_filename"),
            "final_output_collected": bool(dag_state.get("final_output_collected", False)),
            "global_artifacts": global_artifacts,
        }
