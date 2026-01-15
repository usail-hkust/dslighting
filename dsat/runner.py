# dsat/runner.py
import logging
import shutil
import uuid
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Coroutine, Any, Tuple, Dict, Type, Optional, List

# Core configuration and models
from dsat.config import DSATConfig
from dsat.models.task import TaskDefinition, TaskType

# Services and workflows
from dsat.services.llm import LLMService
from dsat.workflows.base import DSATWorkflow

# Dynamic components (factories and handlers)
from dsat.tasks.handlers import TaskHandler, KaggleTaskHandler, QATaskHandler, DataSciTaskHandler, OpenEndedTaskHandler
from dsat.workflows.factory import (
    WorkflowFactory,
    AutoMindWorkflowFactory,
    AIDEWorkflowFactory,
    DSAgentWorkflowFactory,
    DataInterpreterWorkflowFactory,
    AutoKaggleWorkflowFactory,
    AFlowWorkflowFactory,
    DeepAnalyzeWorkflowFactory,
    DynamicWorkflowFactory,
)
# Import AFlow workflow for type checking
from dsat.workflows.search.aflow_workflow import AFlowWorkflow
from dsat.services.states.journal import JournalState

logger = logging.getLogger(__name__)

# ==============================================================================
# ==                            COMPONENT REGISTRIES                          ==
# ==============================================================================

WORKFLOW_FACTORIES: Dict[str, WorkflowFactory] = {
    "automind": AutoMindWorkflowFactory(),
    "aide": AIDEWorkflowFactory(),
    "dsagent": DSAgentWorkflowFactory(),
    "data_interpreter": DataInterpreterWorkflowFactory(),
    "autokaggle": AutoKaggleWorkflowFactory(),
    "aflow": AFlowWorkflowFactory(),
    "deepanalyze": DeepAnalyzeWorkflowFactory(),
}

TASK_HANDLER_CLASSES: Dict[TaskType, Type[TaskHandler]] = {
    "kaggle": KaggleTaskHandler,
    "qa": QATaskHandler,
    "datasci": DataSciTaskHandler,
    "open_ended": OpenEndedTaskHandler,
    # "code": CodeTaskHandler, # future extension
}


# ==============================================================================
# ==                                DSAT RUNNER                               ==
# ==============================================================================

class DSATRunner:
    """
    Orchestrates benchmarking tasks by instantiating workflows, preparing inputs,
    executing runs, and collecting telemetry for later inspection.
    """

    def __init__(self, config: DSATConfig):
        logger.info(f"Initializing DSATRunner for workflow: '{config.workflow.name}'")
        self.config = config
        self.factories = WORKFLOW_FACTORIES.copy()
        self.factory = self.factories.get(config.workflow.name)
        if not self.factory:
            available = ", ".join(self.factories.keys())
            raise ValueError(f"Unknown workflow '{config.workflow.name}'. Available workflows: [{available}]")

        self.handler_classes = TASK_HANDLER_CLASSES
        self.benchmark = None
        self.run_records: List[Dict[str, Any]] = []

        logger.info("DSATRunner is ready to evaluate tasks.")

    def register_workflow(self, name: str, factory: WorkflowFactory) -> None:
        """
        Register a workflow factory dynamically for this runner instance.
        Critical for paradigms like AFLOW which synthesize workflows at runtime.
        """
        logger.info(f"Registering workflow '{name}' for this runner instance.")
        self.factories[name] = factory
        if self.config.workflow and self.config.workflow.name == name:
            self.factory = factory
            logger.info(f"Active workflow factory switched to '{name}'.")

    def get_eval_function(self) -> Callable[[TaskDefinition], Coroutine[Any, Any, Tuple[Any, float, Dict[str, Any]]]]:
        """
        Produce an async function that evaluates a single TaskDefinition and returns (result, cost, usage_summary).
        Benchmark drivers call this function repeatedly for each competition/task.
        """

        async def eval_function(task: TaskDefinition) -> Tuple[Any, float, Dict[str, Any]]:
            logger.info(f"Starting evaluation for task '{task.task_id}' (type='{task.task_type}').")

            # If a specific run name is provided in config, use it. Otherwise, generate one.
            if self.config.run.name and self.config.run.name != "dsat_run":
                task_run_name = self.config.run.name
            else:
                safe_task_id = "".join(c if c.isalnum() else "_" for c in task.task_id)
                unique_suffix = uuid.uuid4().hex[:8]
                task_run_name = f"{self.config.run.name}_{safe_task_id}_{unique_suffix}"

            task_config = self.config.model_copy(deep=True)
            task_config.run.name = task_run_name

            workflow: Optional[DSATWorkflow] = None
            workspace_service = None
            sandbox_service = None
            llm_service: Optional[LLMService] = None
            result: Any = None
            run_total_cost = 0.0
            run_started_at = datetime.utcnow()
            run_perf_start = time.perf_counter()

            benchmark_instance = self.benchmark

            try:
                workflow = self.factory.create_workflow(task_config, benchmark=benchmark_instance)
                workspace_service = workflow.services.get("workspace")
                llm_service = workflow.services.get("llm")
                sandbox_service = workflow.services.get("sandbox")

                if isinstance(workflow, AFlowWorkflow):
                    optimizer_name = "AFLOW"
                    logger.info("Detected %s workflow. Running meta-optimization stage.", optimizer_name)
                    best_workflow_code = await workflow.optimize()
                    logger.info("Meta-optimization complete. Proceeding with final evaluation workflow.")

                    if hasattr(benchmark_instance, 'set_mode'):
                        logger.info("Switching benchmark to 'test' mode for final %s evaluation.", optimizer_name)
                        benchmark_instance.set_mode('test')

                    dynamic_factory = DynamicWorkflowFactory(code_string=best_workflow_code)
                    workflow = dynamic_factory.create_workflow(task_config, benchmark=benchmark_instance)
                    llm_service = workflow.services.get("llm")
                    sandbox_service = workflow.services.get("sandbox")
                    workspace_service = workflow.services.get("workspace")
                    logger.info("Final %s workflow instantiated and ready.", optimizer_name)

                workspace_service = workspace_service or workflow.services.get("workspace")
                llm_service = llm_service or workflow.services.get("llm")
                sandbox_service = sandbox_service or workflow.services.get("sandbox")

                if not llm_service:
                    logger.error("Workflow did not expose an LLMService.")
                    return "[ERROR] Missing LLM service", 0.0

                handler_class = self.handler_classes.get(task.task_type)
                if not handler_class:
                    logger.error(f"No handler registered for task type '{task.task_type}'.")
                    return f"[ERROR] Unsupported task type '{task.task_type}'", 0.0

                handler: TaskHandler = handler_class()

                description, io_instructions = "", ""
                data_dir, output_path = None, None

                try:
                    description, io_instructions, data_dir, output_path = handler.prepare_input(task)

                    if workspace_service:
                        try:
                            workspace_service.link_data_to_workspace(data_dir)
                        except Exception as link_error:
                            raise RuntimeError(f"Failed to link data directory: {link_error}") from link_error
                    else:
                        logger.warning("WorkspaceService missing; skipping data linkage.")

                    await workflow.solve(
                        description=description,
                        io_instructions=io_instructions,
                        data_dir=data_dir,
                        output_path=output_path
                    )

                    if workspace_service and output_path:
                        sandbox_workdir = workspace_service.get_path("sandbox_workdir")
                        generated_file = sandbox_workdir / output_path.name
                        if generated_file.exists():
                            output_path.parent.mkdir(parents=True, exist_ok=True)
                            if generated_file.resolve() != output_path.resolve():
                                logger.info(f"Collecting produced artifact '{output_path.name}' from the sandbox.")

                                # Handle both files and directories (e.g., for open-ended tasks)
                                if generated_file.is_dir():
                                    # For directories (like 'artifacts'), use copytree
                                    if output_path.exists():
                                        if output_path.is_dir():
                                            shutil.rmtree(output_path)
                                        else:
                                            output_path.unlink()
                                    shutil.copytree(generated_file, output_path)
                                    logger.info(f"Copied directory '{generated_file}' to '{output_path}'")
                                else:
                                    # For files, use regular copy
                                    shutil.copy(generated_file, output_path)
                                    logger.info(f"Copied file '{generated_file}' to '{output_path}'")
                        else:
                            logger.warning(f"No output '{output_path.name}' found in sandbox '{sandbox_workdir}' after workflow execution.")

                    if output_path:
                        result = handler.parse_output(output_path)

                        # Grade the submission if benchmark is available
                        if benchmark_instance and hasattr(benchmark_instance, 'grade') and isinstance(result, Path):
                            try:
                                logger.info(f"Grading submission: {result}")
                                score = await benchmark_instance.grade(result)
                                logger.info(f"✓ Grading complete | Score: {score}")
                                # Return score as result
                                result = {"score": score, "submission_path": str(result)}
                            except Exception as grade_error:
                                logger.warning(f"Grading failed: {grade_error}")
                                # Keep the path as result if grading fails
                                logger.info(f"Submission created at: {result}")
                        elif isinstance(result, Path):
                            logger.info(f"Submission created at: {result}")

                    logger.info(f"Task '{task.task_id}' evaluation finished successfully.")

                except Exception as execution_error:
                    logger.error(f"Task '{task.task_id}' failed: {execution_error}", exc_info=True)
                    result = f"[ERROR] {execution_error.__class__.__name__}: {execution_error}"
                finally:
                    handler.cleanup()
                    if workspace_service:
                        ended_at = datetime.utcnow()
                        duration_sec = round(time.perf_counter() - run_perf_start, 4)
                        run_total_cost = llm_service.get_total_cost() if llm_service else 0.0
                        try:
                            self._persist_run_metadata(
                                workspace_service=workspace_service,
                                task_config=task_config,
                                task=task,
                                description=description,
                                io_instructions=io_instructions,
                                data_dir=data_dir,
                                output_path=output_path,
                                result=result,
                                llm_service=llm_service,
                                sandbox_service=sandbox_service,
                                workflow=workflow,
                                started_at=run_started_at,
                                ended_at=ended_at,
                                duration_seconds=duration_sec,
                                total_cost=run_total_cost
                            )
                        except Exception as persist_error:
                            logger.error(f"Failed to persist telemetry for task '{task.task_id}': {persist_error}", exc_info=True)

                        failed = isinstance(result, str) and result.startswith("[ERROR]")
                        keep_on_fail = self.config.run.keep_workspace_on_failure
                        keep_all = self.config.run.keep_all_workspaces
                        workspace_service.cleanup(keep_workspace=keep_all or (failed and keep_on_fail))

            except Exception as workflow_error:
                logger.error(f"Workflow creation failed for task '{task.task_id}': {workflow_error}", exc_info=True)
                result = f"[ERROR] {workflow_error.__class__.__name__}: {workflow_error}"
                if workspace_service:
                    ended_at = datetime.utcnow()
                    duration_sec = round(time.perf_counter() - run_perf_start, 4)
                    run_total_cost = llm_service.get_total_cost() if llm_service else 0.0
                    try:
                        self._persist_run_metadata(
                            workspace_service=workspace_service,
                            task_config=task_config,
                            task=task,
                            description="",
                            io_instructions="",
                            data_dir=None,
                            output_path=None,
                            result=result,
                            llm_service=llm_service,
                            sandbox_service=sandbox_service,
                            workflow=workflow,
                            started_at=run_started_at,
                            ended_at=ended_at,
                            duration_seconds=duration_sec,
                            total_cost=run_total_cost
                        )
                    except Exception as persist_error:
                        logger.error(f"Telemetry persistence failed after workflow creation error: {persist_error}", exc_info=True)
                    workspace_service.cleanup(keep_workspace=True)

            run_total_cost = llm_service.get_total_cost() if llm_service else run_total_cost
            usage_summary = llm_service.get_usage_summary() if llm_service else {}
            logger.info(f"Task '{task.task_id}' LLM cost: ${run_total_cost:.6f}")
            return result, run_total_cost, usage_summary

        return eval_function

    def get_run_records(self) -> List[Dict[str, Any]]:
        """
        Return a shallow copy of stored run metadata records for summary rendering.
        """
        return [record.copy() for record in self.run_records]

    def _persist_run_metadata(
        self,
        *,
        workspace_service,
        task_config: DSATConfig,
        task: TaskDefinition,
        description: str,
        io_instructions: str,
        data_dir: Optional[Path],
        output_path: Optional[Path],
        result: Any,
        llm_service: Optional[LLMService],
        sandbox_service: Optional[Any],
        workflow: Optional[DSATWorkflow],
        started_at: datetime,
        ended_at: datetime,
        duration_seconds: float,
        total_cost: float,
    ) -> None:
        """
        Write per-task telemetry (LLM calls, sandbox runs, search tree, summary) to the workspace.
        """
        telemetry_dir = "telemetry"
        workspace_dir = workspace_service.get_path("run_dir")
        llm_calls = llm_service.get_call_history() if llm_service else []
        sandbox_runs = sandbox_service.get_execution_history() if sandbox_service else []
        usage_summary = llm_service.get_usage_summary() if llm_service else {}
        best_node = self._get_best_node(workflow)
        search_tree_data, search_tree_info = self._extract_search_tree(workflow, best_node)

        config_snapshot = task_config.model_dump()
        if "llm" in config_snapshot and "api_key" in config_snapshot["llm"]:
            config_snapshot["llm"]["api_key"] = "***REDACTED***"

        benchmark_snapshot = self._build_benchmark_snapshot()

        final_code_path: Optional[str] = None
        final_candidate = workspace_service.get_path("artifacts") / "final_submission" / "final_solution.py"
        if final_candidate.exists():
            final_code_path = str(final_candidate)
        elif best_node:
            final_code_path = best_node.final_submission_path or best_node.code_artifact_path

        filtered_parameters = {
            key: value for key, value in (task_config.run.parameters or {}).items()
            if value not in (None, "", [], {})
        }

        metadata = {
            "run_name": task_config.run.name,
            "workspace_dir": str(workspace_dir),
            "workflow": task_config.workflow.name if task_config.workflow else None,
            "parameters": filtered_parameters,
            "benchmark": benchmark_snapshot,
            "task": {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "payload": task.payload,
            },
            "task_context": {
                "description": description,
                "io_instructions": io_instructions,
                "data_dir": str(data_dir) if data_dir else None,
                "expected_output_path": str(output_path) if output_path else None,
            },
            "timeline": {
                "started_at_utc": started_at.isoformat() + "Z",
                "ended_at_utc": ended_at.isoformat() + "Z",
                "duration_seconds": duration_seconds,
            },
            "summary": {
                "result": self._format_result(result),
                "success": not (isinstance(result, str) and result.startswith("[ERROR]")),
                "total_cost": total_cost,
                "usage": usage_summary,
                "cost_per_token": usage_summary.get("cost_per_token"),
                "llm_call_count": len(llm_calls),
                "sandbox_run_count": len(sandbox_runs),
                "final_code": best_node.code if best_node else None,
                "final_code_path": final_code_path,
                "best_node_id": best_node.id if best_node else None,
                "best_path_node_ids": search_tree_info.get("best_path"),
            },
            "config_snapshot": config_snapshot,
        }

        # Save Final Code to a standard location
        if best_node and best_node.code:
            final_code_file = workspace_service.get_path("run_dir") / "final_solution.py"
            with open(final_code_file, "w", encoding="utf-8") as f:
                f.write(best_node.code)
            metadata["summary"]["final_code_path"] = str(final_code_file)

            # 💾 NEW: Save model training code to code_history directory
            try:
                code_history_dir = workspace_service.get_path("sandbox_workdir") / "code_history"
                code_history_dir.mkdir(parents=True, exist_ok=True)

                # Find next available number for model training code
                import re
                existing_model_codes = list(code_history_dir.glob("model_code_*.py"))
                if existing_model_codes:
                    numbers = []
                    for f in existing_model_codes:
                        match = re.search(r'model_code_(\d+)\.py', f.name)
                        if match:
                            numbers.append(int(match.group(1)))
                    next_num = max(numbers) + 1 if numbers else 1
                else:
                    next_num = 1

                # Save with formatted number and metadata
                model_code_filename = f"model_code_{next_num:03d}.py"
                model_code_filepath = code_history_dir / model_code_filename

                # Add header with training metadata
                import datetime
                header = f'''# Code Type: MODEL TRAINING
# Workflow: {task_config.workflow.name if task_config.workflow else 'Unknown'}
# Model: {task_config.llm.model if task_config.llm else 'Unknown'}
# Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Task ID: {task.task_id}
# Success: {not (isinstance(result, str) and result.startswith("[ERROR]"))}

'''
                model_code_filepath.write_text(header + best_node.code)
                logger.info(f"💾 Saved model training code to workspace: {model_code_filepath}")
            except Exception as e:
                logger.warning(f"Failed to save model training code to code_history: {e}")

        # Save Evaluation Result to a CSV in workspace
        if isinstance(result, (float, int, str)) and not str(result).startswith("[ERROR]"):
            try:
                res_file = workspace_service.get_path("run_dir") / "evaluation_result.csv"
                with open(res_file, "w") as f:
                    f.write("task_id,score,cost,duration\n")
                    f.write(f"{task.task_id},{result},{total_cost},{duration_seconds}\n")
            except Exception:
                pass

        detail_files = {}
        if llm_calls:
            llm_calls_path = f"{telemetry_dir}/llm_calls.jsonl"
            self._write_jsonl(workspace_service, llm_calls_path, llm_calls)
            detail_files["llm_calls"] = f"artifacts/{llm_calls_path}"
        if sandbox_runs:
            sandbox_runs_path = f"{telemetry_dir}/sandbox_runs.jsonl"
            self._write_jsonl(workspace_service, sandbox_runs_path, sandbox_runs)
            detail_files["sandbox_runs"] = f"artifacts/{sandbox_runs_path}"
        if search_tree_data:
            search_tree_path = f"{telemetry_dir}/search_tree.json"
            workspace_service.write_file(
                json.dumps(search_tree_data, ensure_ascii=False, indent=2),
                "artifacts",
                search_tree_path
            )
            detail_files["search_tree"] = f"artifacts/{search_tree_path}"
            metadata["search_tree"] = {
                "node_count": len(search_tree_data),
                "best_node_id": search_tree_info.get("best_node_id"),
                "best_path_node_ids": search_tree_info.get("best_path"),
                "file": f"artifacts/{search_tree_path}",
            }
        else:
            metadata["search_tree"] = None

        if detail_files:
            metadata["detail_files"] = detail_files

        run_metadata_path = f"{telemetry_dir}/run_metadata.json"
        workspace_service.write_file(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            "artifacts",
            run_metadata_path
        )

        metadata_file = workspace_service.get_path("artifacts") / run_metadata_path
        record_entry = {
            "task_id": task.task_id,
            "metadata_path": str(metadata_file),
            "workspace_dir": metadata["workspace_dir"],
            "summary": metadata["summary"],
            "timeline": metadata["timeline"],
            "parameters": metadata["parameters"],
            "detail_files": metadata.get("detail_files"),
        }
        self.run_records.append(record_entry)

    def _write_jsonl(self, workspace_service, relative_path: str, records: List[Dict[str, Any]]) -> None:
        """Write newline-delimited JSON records to an artifacts sub-path."""
        content = "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
        workspace_service.write_file(content, "artifacts", relative_path)

    def _format_result(self, result: Any) -> Any:
        """Return a serialization-friendly representation of the workflow result."""
        if isinstance(result, Path):
            return str(result)
        return result

    def _get_best_node(self, workflow: Optional[DSATWorkflow]):
        if not workflow or not hasattr(workflow, "state"):
            return None
        state = workflow.state
        if isinstance(state, JournalState):
            return state.get_best_node()
        return None

    def _extract_search_tree(self, workflow: Optional[DSATWorkflow], best_node: Optional[Any]):
        if not workflow or not hasattr(workflow, "state"):
            return None, {"best_node_id": None, "best_path": None}
        state = workflow.state
        if not isinstance(state, JournalState):
            return None, {"best_node_id": None, "best_path": None}

        nodes = [
            node.model_dump(mode="json")
            for node in sorted(state.nodes.values(), key=lambda n: n.step)
        ]
        best_path = self._extract_best_path(state, best_node)
        info = {
            "best_node_id": best_node.id if best_node else None,
            "best_path": best_path,
        }
        return nodes, info

    def _extract_best_path(self, state: JournalState, best_node: Optional[Any]) -> Optional[List[str]]:
        if not best_node:
            return None
        path: List[str] = []
        current = best_node
        while current:
            path.append(current.id)
            current = state.get_node(current.parent_id) if current.parent_id else None
        return list(reversed(path))

    def _build_benchmark_snapshot(self) -> Optional[Dict[str, Any]]:
        if not self.benchmark:
            return None
        snapshot: Dict[str, Any] = {"name": getattr(self.benchmark, "name", None)}
        data_dir = getattr(self.benchmark, "data_dir", None)
        if data_dir is not None:
            snapshot["data_dir"] = str(data_dir)
        config_value = getattr(self.benchmark, "config", None)
        if isinstance(config_value, dict):
            snapshot["config"] = config_value
        return snapshot
