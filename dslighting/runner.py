# dslighting/runner.py
from __future__ import annotations

import logging
import shutil
import uuid
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Coroutine, Any

# Core configuration and models
from dslighting.config import DSLightingConfig, DagRuntimeConfig
from dslighting.core.config.runtime_logging import log_resolved_runtime_config
from dslighting.core.types import TaskDefinition, TaskType

# Services and workflows
from dslighting.services.llm import LLMService
from dslighting.workflows.base import BaseWorkflow
from dslighting.runtime.dag import (
    DagRunSummary,
    DagRuntime,
    DagRuntimeOptions,
    DeclarativeWorkflowActor,
    NodeDispatcher,
    SolveWorkflowActor,
    create_pipeline_runtime,
)

# Dynamic components (factories and adapters)
from dslighting.core.tasks import (
    BaseTaskAdapter,
    DataScienceTaskAdapter,
    FileSubmissionTaskAdapter,
    OpenEndedTaskAdapter,
    QATaskAdapter,
    TaskResolver,
)
from dslighting.benchmark.evaluation.service import TaskEvaluationService
from dslighting.workflows.factory.base import BaseWorkflowFactory
from dslighting.workflows.factory.builtin import (
    AutoMindWorkflowFactory,
    AIDEWorkflowFactory,
    DSAgentWorkflowFactory,
    DataInterpreterWorkflowFactory,
    AutoKaggleWorkflowFactory,
    AFlowWorkflowFactory,
    DeepAnalyzeWorkflowFactory,
    DynamicWorkflowFactory,
    MyCustomAgentWorkflowFactory,
    ReActWorkflowFactory,
)
from dslighting.workflows.output_contract import (
    is_valid_output_path,
    resolve_runner_output_candidate,
)

# Import AFlow workflow for type checking
from dslighting.workflows.search.aflow_workflow import AFlowWorkflow
from dslighting.state.search.journal import JournalState
from dslighting.error import (
    BenchmarkError,
    ConfigurationError,
    WorkflowError,
    WorkspaceError,
)
from dslighting.utils.constants import UNIQUE_SUFFIX_LENGTH, CODE_FILENAME_ZERO_PADDING
from dslighting.utils.defaults import DEFAULT_WORKSPACE_DIR

logger = logging.getLogger(__name__)


# ==============================================================================
# ==                          RUNTIME CONFIG PARSER                           ==
# ==============================================================================


class RuntimeConfigParser:
    """
    Parser for runtime configuration extracted from task definitions.

    This class centralizes the extraction and parsing of runtime hints,
    DAG options, and task context from task definitions, eliminating duplicate
    parsing logic across the runner.

    Example:
        >>> parser = RuntimeConfigParser(task, task_config)
        >>> runtime_hints = parser.parse_runtime_hints()
        >>> dag_options = parser.parse_dag_options(runtime_hints)
    """

    def __init__(self, task: TaskDefinition, task_config: DSLightingConfig):
        """Initialize the parser with task definition and task configuration.

        Args:
            task: The task definition containing payload with runtime hints.
            task_config: The task configuration to be configured.
        """
        self.task = task
        self.task_config = task_config

    def parse_runtime_hints(self) -> dict[str, Any]:
        """Extract runtime hints from the task payload.

        Parses the 'runtime' key from task.payload, handling various edge cases
        for backward compatibility with different payload formats.

        Returns:
            A dictionary containing runtime hints (cuda_visible_devices,
            llm_max_concurrency, extra_env, enable_dag_runtime, etc.).
            Returns empty dict if payload is malformed or missing runtime.
        """
        payload = self.task.payload
        if not isinstance(payload, dict):
            return {}

        runtime = payload.get("runtime", {})
        if not isinstance(runtime, dict):
            return {}

        return runtime

    def parse_task_context(self) -> dict[str, Any]:
        """Parse task context from payload for backward compatibility.

        Extracts description, io_instructions, and metric semantics from task.payload if present.

        Returns:
            A dictionary containing execution context fields.
        """
        payload = self.task.payload
        if not isinstance(payload, dict):
            return {
                "description": "",
                "io_instructions": "",
                "metric_name": None,
                "lower_is_better": None,
            }

        execution_spec = payload.get("execution_spec")
        execution_spec = execution_spec if isinstance(execution_spec, dict) else {}

        return {
            "description": payload.get("description", ""),
            "io_instructions": payload.get("io_instructions", ""),
            "metric_name": payload.get("metric_name", execution_spec.get("metric_name")),
            "lower_is_better": payload.get(
                "lower_is_better", execution_spec.get("lower_is_better")
            ),
        }

    def apply_agent_task_context(self) -> DSLightingConfig:
        """Copy task-scoped metric semantics into config.agent.task_context."""
        task_context = self.parse_task_context()
        merged = dict(getattr(self.task_config.agent, "task_context", {}) or {})

        metric_name = task_context.get("metric_name")
        if isinstance(metric_name, str) and metric_name.strip():
            merged["metric_name"] = metric_name.strip()

        lower_is_better = task_context.get("lower_is_better")
        if isinstance(lower_is_better, bool):
            merged["lower_is_better"] = lower_is_better

        self.task_config.agent.task_context = merged
        return self.task_config

    def parse_dag_options(self, runtime_hints: dict[str, Any] | None = None) -> "DagRuntimeOptions":
        """Resolve DAG runtime options from configuration and runtime hints.

        Combines options from:
        1. task_config.run.dag_runtime (static configuration)
        2. task_config.run.parameters (runtime overrides)
        3. runtime_hints from task.payload (runtime hints)

        Args:
            runtime_hints: Optional runtime hints dict. If None, parses from task.

        Returns:
            A fully resolved DagRuntimeOptions instance with merged settings.
        """
        if runtime_hints is None:
            runtime_hints = self.parse_runtime_hints()

        options = DagRuntimeOptions()
        dag_config = getattr(self.task_config.run, "dag_runtime", None)
        if isinstance(dag_config, DagRuntimeConfig):
            options = DagRuntimeOptions(**dag_config.model_dump())
        elif isinstance(dag_config, dict):
            options = DagRuntimeOptions(**dag_config)

        run_parameters = dict(self.task_config.run.parameters or {})
        dag_override = run_parameters.get("dag_runtime")
        if isinstance(dag_override, DagRuntimeConfig):
            dag_override = dag_override.model_dump()
        if isinstance(dag_override, dict):
            for key, value in dag_override.items():
                if hasattr(options, key):
                    setattr(options, key, value)

        if "enable_dag_runtime" in run_parameters:
            options.enabled = bool(run_parameters.get("enable_dag_runtime"))
        if "enable_dag_runtime" in runtime_hints:
            options.enabled = bool(runtime_hints.get("enable_dag_runtime"))

        def _first_override(*keys: str) -> Any:
            for key in keys:
                if key in runtime_hints and runtime_hints.get(key) is not None:
                    return runtime_hints.get(key)
                if key in run_parameters and run_parameters.get(key) is not None:
                    return run_parameters.get(key)
            return None

        llm_global_cap = self._coerce_positive_int(
            _first_override("llm_global_max_concurrency", "llm_max_concurrency")
        )
        if llm_global_cap is not None:
            options.llm_global_max_concurrency = llm_global_cap

        max_inflight_nodes = self._coerce_positive_int(_first_override("max_inflight_nodes"))
        if max_inflight_nodes is not None:
            options.max_inflight_nodes = max_inflight_nodes

        max_retries = self._coerce_non_negative_int(
            _first_override("dag_max_retries", "max_retries")
        )
        if max_retries is not None:
            options.max_retries = max_retries

        node_timeout_seconds_raw = _first_override(
            "node_timeout_seconds", "dag_node_timeout_seconds"
        )
        if node_timeout_seconds_raw is not None:
            try:
                node_timeout_seconds = float(node_timeout_seconds_raw)
                if node_timeout_seconds > 0:
                    options.node_timeout_seconds = node_timeout_seconds
            except (TypeError, ValueError):
                pass

        ready_queue_policy = _first_override("ready_queue_policy")
        if ready_queue_policy is not None:
            options.ready_queue_policy = str(ready_queue_policy)

        dag_mode = _first_override("dag_mode")
        if dag_mode is not None:
            options.dag_mode = str(dag_mode)

        enable_debug_branch = _first_override("enable_debug_branch")
        if enable_debug_branch is not None:
            options.enable_debug_branch = bool(enable_debug_branch)

        enable_speculative_branches = _first_override("enable_speculative_branches")
        if enable_speculative_branches is not None:
            options.enable_speculative_branches = bool(enable_speculative_branches)

        llm_model_quotas = _first_override("llm_model_quotas")
        if isinstance(llm_model_quotas, dict):
            options.llm_model_quotas = dict(llm_model_quotas)

        actor_strategy = _first_override("dag_actor_strategy", "dag_runtime_actor_strategy")
        if actor_strategy is not None:
            options.dag_actor_strategy = str(actor_strategy)

        runtime_engine = _first_override("runtime_engine", "dag_runtime_engine")
        if runtime_engine is not None:
            options.runtime_engine = str(runtime_engine)

        timeout_policy = _first_override("node_timeout_policy", "dag_node_timeout_policy")
        if timeout_policy is not None:
            options.node_timeout_policy = str(timeout_policy)

        parallel_drafts = self._coerce_positive_int(
            _first_override("parallel_drafts", "dag_parallel_drafts")
        )
        if parallel_drafts is not None:
            options.parallel_drafts = parallel_drafts

        branch_budget = self._coerce_positive_int(
            _first_override("branch_budget", "dag_branch_budget")
        )
        if branch_budget is not None:
            options.branch_budget = branch_budget

        timeout_by_op = _first_override("node_timeout_by_op", "dag_node_timeout_by_op")
        if isinstance(timeout_by_op, dict):
            options.node_timeout_by_op = dict(timeout_by_op)

        return options.normalize()

    @staticmethod
    def _coerce_positive_int(value: Any) -> int | None:
        """Convert value to a positive integer, or None if invalid."""
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed > 0 else None

    @staticmethod
    def _coerce_non_negative_int(value: Any) -> int | None:
        """Convert value to a non-negative integer, or None if invalid."""
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed >= 0 else None

    def update_task_config_from_runtime_hints(
        self,
        runtime_hints: dict[str, Any] | None = None,
    ) -> "DSLightingConfig":
        """Update task configuration with runtime hints.

        Applies runtime configuration from task.payload to task_config,
        including:
        - CUDA_VISIBLE_DEVICES for GPU allocation
        - LLM concurrency limits
        - Extra environment variables

        Args:
            runtime_hints: Optional runtime hints dict. If None, parses from task.

        Returns:
            Updated task_config with runtime parameters applied.
        """
        if runtime_hints is None:
            runtime_hints = self.parse_runtime_hints()

        if not isinstance(runtime_hints, dict) or not runtime_hints:
            return self.task_config

        sandbox_env: dict[str, str] = {}
        extra_parameters: dict[str, Any] = {}

        cuda_visible_devices = runtime_hints.get("cuda_visible_devices")
        if cuda_visible_devices is not None:
            sandbox_env["CUDA_VISIBLE_DEVICES"] = str(cuda_visible_devices)

        llm_max_concurrency = runtime_hints.get("llm_max_concurrency")
        if llm_max_concurrency is not None:
            try:
                extra_parameters["llm_max_concurrency"] = max(1, int(llm_max_concurrency))
            except (TypeError, ValueError):
                pass

        extra_env = runtime_hints.get("extra_env")
        if isinstance(extra_env, dict):
            for env_key, env_value in extra_env.items():
                if env_value is not None:
                    sandbox_env[str(env_key)] = str(env_value)

        if sandbox_env or extra_parameters:
            merged_parameters = dict(self.task_config.run.parameters or {})
            if sandbox_env:
                merged_parameters["sandbox_env"] = sandbox_env
            merged_parameters.update(extra_parameters)
            self.task_config.run.parameters = merged_parameters

        return self.task_config


# ==============================================================================
# ==                            REGISTRY GRADER                               ==
# ==============================================================================


class RegistryGrader:
    """
    Handles direct grading using a strict registry contract.

    This class centralizes the grading logic for tasks that use a registry-based
    evaluation system, such as Kaggle competitions. It handles locating task
    registries, loading configurations, and executing the grading process.

    Example:
        >>> grader = RegistryGrader()
        >>> score = await grader.grade(
        ...     task_id="bike-sharing-demand",
        ...     submission_path=Path("submission.csv"),
        ...     data_dir=Path("data"),
        ... )
    """

    async def grade(
        self,
        task_id: str,
        submission_path: Path,
        data_dir: Path | None = None,
        registry_dir: str | None = None,
    ) -> float:
        """
        Direct grading using a strict registry contract.

        Args:
            task_id: Task/competition ID (e.g., "bike-sharing-demand")
            submission_path: Path to submission CSV file
            data_dir: Data directory containing prepared/ folder
            registry_dir: Optional registry root path containing `<task_id>/config.yaml`

        Returns:
            Score as float
        """
        logger.info("[RegistryGrader] Direct grading for task: %s", task_id)
        resolver = TaskResolver()
        layout = resolver.resolve(
            task_id=task_id,
            data=data_dir,
            registry_dir=registry_dir,
        )
        outcome = await TaskEvaluationService().evaluate(
            submission_path=submission_path,
            contract=layout.evaluation_contract,
            mode="test",
            metadata={"registry_dir": str(layout.registry_root)},
        )
        logger.info(
            "✓ [RegistryGrader] Grading completed | task=%s score=%s valid=%s",
            task_id,
            outcome.score,
            outcome.valid_submission,
        )
        return float(outcome.score) if outcome.score is not None else 0.0


# ==============================================================================
# ==                            COMPONENT REGISTRIES                          ==
# ==============================================================================

WORKFLOW_FACTORIES: dict[str, type[BaseWorkflowFactory]] = {
    "automind": AutoMindWorkflowFactory,
    "aide": AIDEWorkflowFactory,
    "dsagent": DSAgentWorkflowFactory,
    "data_interpreter": DataInterpreterWorkflowFactory,
    "autokaggle": AutoKaggleWorkflowFactory,
    "aflow": AFlowWorkflowFactory,
    "deepanalyze": DeepAnalyzeWorkflowFactory,
    "my_custom_agent": MyCustomAgentWorkflowFactory,
    "react": ReActWorkflowFactory,
}

TASK_ADAPTER_CLASSES: dict[TaskType, type[BaseTaskAdapter]] = {
    "kaggle": FileSubmissionTaskAdapter,
    "qa": QATaskAdapter,
    "datasci": DataScienceTaskAdapter,
    "open_ended": OpenEndedTaskAdapter,
}


# ==============================================================================
# ==                                DSLighting RUNNER                               ==
# ==============================================================================


class DSLightingRunner:
    """
    Orchestrates benchmarking tasks by instantiating workflows, preparing inputs,
    executing runs, and collecting telemetry for later inspection.
    """

    def __init__(self, config: DSLightingConfig):
        logger.info(f"Initializing DSLightingRunner for workflow: '{config.workflow.name}'")
        self.config = config
        self.factories = WORKFLOW_FACTORIES.copy()
        factory_class = self.factories.get(config.workflow.name)
        if not factory_class:
            available = ", ".join(self.factories.keys())
            raise WorkflowError(
                f"Unknown workflow '{config.workflow.name}'. Available workflows: [{available}]",
                error_code="WRK-001",
                details={
                    "workflow_name": config.workflow.name,
                    "available_workflows": list(self.factories.keys()),
                },
                suggestion="Check the workflow name against the list of available workflows",
            )
        self.factory: BaseWorkflowFactory = factory_class()

        self.adapter_classes = TASK_ADAPTER_CLASSES
        self.benchmark = None
        self.run_records: list[dict[str, Any]] = []
        self.registry_grader = RegistryGrader()
        self._llm_runtime_limits_lock = threading.RLock()
        self._llm_runtime_limit_signature: tuple[int | None, tuple[tuple[str, int], ...]] | None = (
            None
        )
        self._llm_runtime_limit_source_task: str | None = None

        logger.info("DSLightingRunner is ready to evaluate tasks.")

    @staticmethod
    def _format_llm_runtime_limit_signature(
        signature: tuple[int | None, tuple[tuple[str, int], ...]] | None,
    ) -> dict[str, Any]:
        if signature is None:
            return {"llm_global_max_concurrency": None, "llm_model_quotas": {}}
        global_cap, model_items = signature
        return {
            "llm_global_max_concurrency": global_cap,
            "llm_model_quotas": dict(model_items),
        }

    def register_workflow(
        self, name: str, factory: BaseWorkflowFactory | type[BaseWorkflowFactory]
    ) -> None:
        """
        Register a workflow factory dynamically for this runner instance.
        Critical for paradigms like AFLOW which synthesize workflows at runtime.
        """
        logger.info(f"Registering workflow '{name}' for this runner instance.")
        if isinstance(factory, type):
            self.factories[name] = factory
            candidate = factory()
        else:
            self.factories[name] = factory.__class__
            candidate = factory
        if self.config.workflow and self.config.workflow.name == name:
            self.factory = candidate
            logger.info(f"Active workflow factory switched to '{name}'.")

    def get_eval_function(
        self,
    ) -> Callable[[TaskDefinition], Coroutine[Any, Any, tuple[Any, float, dict[str, Any]]]]:
        """
        Produce an async function that evaluates a single TaskDefinition and returns (result, cost, usage_summary).
        Benchmark drivers call this function repeatedly for each competition/task.
        """

        async def eval_function(task: TaskDefinition) -> tuple[Any, float, dict[str, Any]]:
            logger.info(f"Starting evaluation for task '{task.task_id}' (type='{task.task_type}').")

            # ========================================================================
            # Initialize tracking variables
            # ========================================================================
            result: Any = None
            dag_summary: DagRunSummary | None = None
            run_total_cost = 0.0
            run_started_at = datetime.utcnow()
            run_perf_start = time.perf_counter()

            # Variables needed across stages
            task_config: DSLightingConfig | None = None
            workflow: BaseWorkflow | None = None
            workspace_service = None
            sandbox_service = None
            llm_service: LLMService | None = None
            adapter: BaseTaskAdapter | None = None
            description, io_instructions = "", ""
            data_dir, output_path = None, None

            # ========================================================================
            # Stage 1: Prepare task execution
            # ========================================================================
            try:
                task_config = await self._prepare_task_execution(task)

                # ========================================================================
                # Stage 2: Create workflow instance
                # ========================================================================
                (
                    workflow,
                    llm_service,
                    sandbox_service,
                    workspace_service,
                ) = await self._create_workflow_instance(task_config)

                if not llm_service:
                    logger.error("Workflow did not expose an LLMService.")
                    return "[ERROR] Missing LLM service", 0.0

                # ========================================================================
                # Stage 3: Build runtime input and execute workflow
                # ========================================================================
                (
                    result,
                    dag_summary,
                    adapter,
                    description,
                    io_instructions,
                    data_dir,
                    output_path,
                ) = await self._execute_task_adapter(
                    task,
                    workflow,
                    llm_service,
                    sandbox_service,
                    workspace_service,
                    task_config,
                )

                logger.info(f"Task '{task.task_id}' evaluation finished successfully.")

            except Exception as execution_error:
                logger.error(f"Task '{task.task_id}' failed: {execution_error}", exc_info=True)
                result = f"[ERROR] {execution_error.__class__.__name__}: {execution_error}"

            finally:
                # ========================================================================
                # Stage 4: Grade submission and persist metadata
                # ========================================================================
                ended_at = datetime.utcnow()
                duration_sec = round(time.perf_counter() - run_perf_start, 4)
                run_total_cost = llm_service.get_total_cost() if llm_service else 0.0

                try:
                    # Grade submission if applicable
                    if output_path:
                        result = await self._grade_submission(
                            task=task,
                            result=result,
                            output_path=output_path,
                            data_dir=data_dir,
                            llm_service=llm_service,
                        )
                except Exception as grade_error:
                    logger.warning(f"Grading failed: {grade_error}")

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
                        dag_summary=dag_summary.to_dict() if dag_summary else None,
                        started_at=run_started_at,
                        ended_at=ended_at,
                        duration_seconds=duration_sec,
                        total_cost=run_total_cost,
                    )
                except Exception as persist_error:
                    logger.error(
                        f"Failed to persist telemetry for task '{task.task_id}': {persist_error}",
                        exc_info=True,
                    )

                # Cleanup workspace
                if workspace_service:
                    failed = isinstance(result, str) and result.startswith("[ERROR]")
                    keep_on_fail = self.config.run.keep_workspace_on_failure
                    keep_all = self.config.run.keep_all_workspaces
                    workspace_service.cleanup(keep_workspace=keep_all or (failed and keep_on_fail))

                if adapter:
                    adapter.cleanup()

            # Note: run_total_cost is already set in the finally block above
            usage_summary = llm_service.get_usage_summary() if llm_service else {}
            if dag_summary:
                usage_summary["dag_runtime"] = dag_summary.to_dict()
            logger.info(f"Task '{task.task_id}' LLM cost: ${run_total_cost:.6f}")
            return result, run_total_cost, usage_summary

        return eval_function

    async def _prepare_task_execution(self, task: TaskDefinition) -> DSLightingConfig:
        """Prepare runtime environment for task execution.

        This method handles:
        1. Generating unique run name for the task
        2. Setting up task configuration with runtime parameters
        3. Resolving DAG runtime options
        4. Configuring LLM runtime limits

        Args:
            task: The task definition to prepare for execution.

        Returns:
            A configured DSLightingConfig instance ready for execution.
        """
        # Two-layer workspace: <session_run_name>/<task_id>_<uid>/
        # session_run_name comes from config.run.run_name (set by user or auto-generated as "agent_<workflow>")
        session_run_name = self.config.run.run_name
        safe_task_id = "".join(c if c.isalnum() else "_" for c in task.task_id)
        unique_suffix = uuid.uuid4().hex[:UNIQUE_SUFFIX_LENGTH]
        task_run_name = f"{safe_task_id}_{unique_suffix}"

        task_config = self.config.model_copy(deep=True)
        task_config.run.run_name = task_run_name

        # Inject session directory into workspace_base_dir so WorkspaceService sees:
        #   <base_dir>/<session_run_name>/<task_run_name>/
        if task_config.workflow is None:
            from dslighting.config import WorkflowConfig

            task_config.workflow = WorkflowConfig(name="aide", params={})
        workspace_base = (
            task_config.workflow.params.get("workspace_base_dir") or DEFAULT_WORKSPACE_DIR
        )
        task_config.workflow.params["workspace_base_dir"] = str(
            Path(workspace_base) / session_run_name
        )

        # Use RuntimeConfigParser to extract and apply runtime configuration
        config_parser = RuntimeConfigParser(task, task_config)
        runtime_hints = config_parser.parse_runtime_hints()
        task_config = config_parser.update_task_config_from_runtime_hints(runtime_hints)
        task_config = config_parser.apply_agent_task_context()

        dag_runtime_options = config_parser.parse_dag_options(runtime_hints)
        self._configure_llm_runtime_limits(
            task_id=task.task_id, task_config=task_config, dag_options=dag_runtime_options
        )
        log_resolved_runtime_config(
            logger,
            config=task_config,
            source=self.__class__.__name__,
            task_id=task.task_id,
        )

        return task_config

    async def _create_workflow_instance(
        self, task_config: DSLightingConfig
    ) -> tuple[BaseWorkflow, LLMService, Any, Any]:
        """Create workflow instance with all required services.

        This method handles:
        1. Creating the workflow instance via factory
        2. Extracting and validating required services (LLM, sandbox, workspace)
        3. Handling AFlow meta-optimization if applicable

        Args:
            task_config: The configured task configuration.

        Returns:
            A tuple of (workflow, llm_service, sandbox_service, workspace_service).
        """
        benchmark_instance = self.benchmark
        workflow = self.factory.create_workflow(task_config, benchmark=benchmark_instance)
        workspace_service = workflow.services.get("workspace")
        llm_service = workflow.services.get("llm")
        sandbox_service = workflow.services.get("sandbox")

        if isinstance(workflow, AFlowWorkflow):
            optimizer_name = "AFLOW"
            logger.info("Detected %s workflow. Running meta-optimization stage.", optimizer_name)
            best_workflow_code = await workflow.optimize()
            logger.info("Meta-optimization complete. Proceeding with final evaluation workflow.")

            if hasattr(benchmark_instance, "set_mode"):
                logger.info(
                    "Switching benchmark to 'test' mode for final %s evaluation.",
                    optimizer_name,
                )
                benchmark_instance.set_mode("test")

            dynamic_factory = DynamicWorkflowFactory(code_string=best_workflow_code)
            workflow = dynamic_factory.create_workflow(task_config, benchmark=benchmark_instance)
            llm_service = workflow.services.get("llm")
            sandbox_service = workflow.services.get("sandbox")
            workspace_service = workflow.services.get("workspace")
            logger.info("Final %s workflow instantiated and ready.", optimizer_name)

        workspace_service = workspace_service or workflow.services.get("workspace")
        llm_service = llm_service or workflow.services.get("llm")
        sandbox_service = sandbox_service or workflow.services.get("sandbox")

        return workflow, llm_service, sandbox_service, workspace_service

    async def _execute_task_adapter(
        self,
        task: TaskDefinition,
        workflow: BaseWorkflow,
        llm_service: LLMService,
        sandbox_service: Any,
        workspace_service: Any,
        task_config: DSLightingConfig,
    ) -> tuple[Any, DagRunSummary | None, BaseTaskAdapter, str, str, Path | None, Path | None]:
        """Build task runtime input and execute workflow.

        This method handles:
        1. Selecting and preparing the appropriate task adapter
        2. Linking data to workspace
        3. Executing the workflow (with or without DAG)
        4. Collecting output artifacts

        Args:
            task: The task definition to execute.
            workflow: The workflow instance to run.
            llm_service: The LLM service instance.
            sandbox_service: The sandbox service instance.
            workspace_service: The workspace service instance.
            task_config: The task configuration.

        Returns:
            A tuple of (result, dag_summary, adapter, description, io_instructions, data_dir, output_path).
        """
        adapter_class = self.adapter_classes.get(task.task_type)
        if not adapter_class:
            logger.error(f"No adapter registered for task type '{task.task_type}'.")
            return (
                f"[ERROR] Unsupported task type '{task.task_type}'",
                None,
                None,
                "",
                "",
                None,
                None,
            )

        adapter: BaseTaskAdapter = adapter_class(task_config)

        description, io_instructions = "", ""
        data_dir, output_path = None, None

        execution_spec = adapter.build_execution_spec(task)
        description = execution_spec.description_text
        io_instructions = execution_spec.io_instructions
        data_dir = execution_spec.agent_visible_dir
        output_path = execution_spec.output_path

        if workspace_service:
            try:
                workspace_service.link_data_to_workspace(data_dir)
            except Exception as link_error:
                raise WorkspaceError(
                    f"Failed to link data directory: {link_error}",
                    error_code="WSP-001",
                    details={"data_dir": str(data_dir) if data_dir else None},
                    suggestion="Check that the data directory exists and is accessible",
                ) from link_error
        else:
            logger.warning("WorkspaceService missing; skipping data linkage.")

        if data_dir is None or output_path is None:
            raise WorkflowError(
                "Task adapter returned empty data_dir or output_path.",
                error_code="WRK-002",
                details={
                    "data_dir": str(data_dir) if data_dir else None,
                    "output_path": str(output_path) if output_path else None,
                },
                suggestion="Check the task adapter implementation to ensure data_dir and output_path are properly set",
            )

        # Resolve DAG runtime options for execution
        # Use RuntimeConfigParser to extract and resolve DAG options
        config_parser = RuntimeConfigParser(task, task_config)
        runtime_hints = config_parser.parse_runtime_hints()
        dag_runtime_options = config_parser.parse_dag_options(runtime_hints)

        dag_summary = await self._execute_workflow_entrypoint(
            task_id=task.task_id,
            workflow=workflow,
            description=description,
            io_instructions=io_instructions,
            data_dir=data_dir,
            output_path=output_path,
            dag_options=dag_runtime_options,
        )

        # Collect output artifacts
        if workspace_service and output_path:
            output_path = self._collect_output_artifacts(
                workspace_service=workspace_service,
                output_path=output_path,
            )

        result = adapter.parse_output(output_path) if output_path else None

        return result, dag_summary, adapter, description, io_instructions, data_dir, output_path

    def _collect_output_artifacts(
        self,
        workspace_service: Any,
        output_path: Path,
    ) -> Path:
        """Collect produced artifacts from sandbox to designated output path.

        Args:
            workspace_service: The workspace service instance.
            output_path: The designated output path.

        Returns:
            The actual path where the output was found/collected.
        """
        sandbox_workdir = workspace_service.get_path("sandbox_workdir")
        generated_file, accepted_via_fallback = resolve_runner_output_candidate(
            sandbox_workdir=sandbox_workdir,
            output_path=output_path,
        )
        if accepted_via_fallback:
            logger.warning(
                f"Submission hash mismatch: expected '{output_path.name}', "
                f"found '{generated_file.name}' via fallback glob."
            )

        if is_valid_output_path(generated_file):
            # Only copy if output_path is an absolute path
            # If it's a relative path (just filename), keep it in workspace/sandbox
            if output_path.is_absolute():
                output_path.parent.mkdir(parents=True, exist_ok=True)
                if generated_file.resolve() != output_path.resolve():
                    logger.info(
                        f"Collecting produced artifact '{output_path.name}' from the sandbox."
                    )

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
                # Relative path - file stays in sandbox, use workspace path for result
                logger.info(
                    f"Output file '{output_path.name}' remains in workspace sandbox: {generated_file}"
                )
                # Update output_path to point to the actual file in workspace
                output_path = generated_file
        else:
            logger.warning(
                f"No output '{output_path.name}' found in sandbox '{sandbox_workdir}' after workflow execution."
            )
        return output_path

    async def _grade_submission(
        self,
        task: TaskDefinition,
        result: Any,
        output_path: Path,
        data_dir: Path | None,
        llm_service: LLMService | None,
    ) -> Any:
        """Grade submission and return score.

        This method handles:
        1. Grading via benchmark if available
        2. Direct grading from registry for Kaggle tasks
        3. Wrapping result with score information

        Args:
            task: The task definition.
            result: The current result (typically a Path).
            output_path: Path to the output file.
            data_dir: Path to the data directory.
            llm_service: The LLM service instance.

        Returns:
            The result possibly wrapped with score information.
        """
        benchmark_instance = self.benchmark

        # Grade via benchmark if available
        if benchmark_instance and hasattr(benchmark_instance, "grade") and isinstance(result, Path):
            try:
                logger.info(f"Grading submission: {result}")
                score = await benchmark_instance.grade(result, competition_id=task.task_id)
                logger.info(f"Grading complete | Score: {score}")
                # Return score as result
                return {"score": score, "submission_path": str(result)}
            except Exception as grade_error:
                raise BenchmarkError(
                    f"Benchmark grading failed for task '{task.task_id}': {grade_error}",
                    error_code="BMK-001",
                    details={"task_id": task.task_id},
                    suggestion="Check the benchmark grade.py implementation and ensure the submission format is correct",
                ) from grade_error
        elif isinstance(result, Path) and task.task_type == "kaggle":
            logger.info(f"Submission created at: {result}")
            payload_registry_dir = None
            if isinstance(task.payload, dict):
                payload_registry_dir = task.payload.get("registry_dir")
            score = await self.registry_grader.grade(
                task.task_id,
                result,
                data_dir=data_dir,
                registry_dir=payload_registry_dir,
            )
            logger.info(f"Direct grading complete | Score: {score}")
            return {"score": score, "submission_path": str(result)}

        return result

    def _configure_llm_runtime_limits(
        self,
        *,
        task_id: str,
        task_config: DSLightingConfig,
        dag_options: DagRuntimeOptions,
    ) -> None:
        run_parameters = dict(task_config.run.parameters or {})
        configured_global_cap = (
            dag_options.llm_global_max_concurrency
            or RuntimeConfigParser._coerce_positive_int(run_parameters.get("llm_max_concurrency"))
        )
        model_quotas = dict(dag_options.llm_model_quotas or {})

        try:
            api_keys = task_config.llm.get_api_keys()
        except Exception:  # pragma: no cover - defensive
            api_keys = []

        per_key_cap = RuntimeConfigParser._coerce_positive_int(
            getattr(task_config.llm, "max_concurrent_per_key", None)
        )
        theoretical_max = None
        if api_keys and per_key_cap:
            theoretical_max = len(api_keys) * per_key_cap

        if theoretical_max is not None:
            if configured_global_cap is None:
                global_cap = theoretical_max
            else:
                global_cap = min(configured_global_cap, theoretical_max)
                if global_cap < configured_global_cap:
                    logger.info(
                        "Clamping llm_global_max_concurrency from %s to %s based on key pool capacity (%s keys x %s per key).",
                        configured_global_cap,
                        global_cap,
                        len(api_keys),
                        per_key_cap,
                    )
        else:
            global_cap = configured_global_cap

        normalized_global_cap, normalized_model_quotas = LLMService.normalize_concurrency_limits(
            global_max_concurrency=global_cap,
            model_quotas=model_quotas,
        )
        signature = (
            normalized_global_cap,
            tuple(sorted(normalized_model_quotas.items())),
        )

        with self._llm_runtime_limits_lock:
            if self._llm_runtime_limit_signature is None:
                LLMService.configure_concurrency_limits(
                    global_max_concurrency=normalized_global_cap,
                    model_quotas=normalized_model_quotas,
                )
                self._llm_runtime_limit_signature = signature
                self._llm_runtime_limit_source_task = task_id
                logger.info(
                    "Configured run-scoped LLM concurrency limits | task=%s global=%s model_quotas=%s",
                    task_id,
                    normalized_global_cap,
                    normalized_model_quotas,
                )
                return

            if signature == self._llm_runtime_limit_signature:
                return

            first_task_id = self._llm_runtime_limit_source_task or "<unknown>"
            raise ConfigurationError(
                "Conflicting task-level LLM concurrency settings detected within the same run.",
                error_code="CFG-003",
                details={
                    "first_task_id": first_task_id,
                    "first_limits": self._format_llm_runtime_limit_signature(
                        self._llm_runtime_limit_signature
                    ),
                    "conflicting_task_id": task_id,
                    "conflicting_limits": self._format_llm_runtime_limit_signature(signature),
                },
                suggestion=(
                    "Use a single llm_global_max_concurrency/llm_model_quotas profile per run "
                    "or split tasks with different limits into separate runs."
                ),
            )

    def _build_dag_actor(
        self,
        *,
        task_id: str,
        workflow: BaseWorkflow,
        description: str,
        io_instructions: str,
        data_dir: Path,
        output_path: Path,
        dag_options: "DagRuntimeOptions" = None,
    ) -> Any:
        actor_strategy = str(getattr(dag_options, "dag_actor_strategy", "coarse")).strip().lower()

        if actor_strategy == "declarative":
            supports_declarative = getattr(workflow, "supports_declarative_dag", None)
            supported = callable(getattr(workflow, "build_operator_graph", None))
            if callable(supports_declarative):
                try:
                    supported = bool(supports_declarative())
                except Exception as support_error:
                    logger.warning(
                        "supports_declarative_dag() failed for workflow '%s': %s",
                        workflow.__class__.__name__,
                        support_error,
                    )
                    supported = False

            if supported:
                try:
                    return DeclarativeWorkflowActor(
                        task_id=task_id,
                        workflow=workflow,
                        description=description,
                        io_instructions=io_instructions,
                        data_dir=data_dir,
                        output_path=output_path,
                        dag_options=dag_options,
                    )
                except Exception as actor_error:
                    logger.warning(
                        "Declarative DAG actor build failed for task '%s': %s",
                        task_id,
                        actor_error,
                    )

        build_actor = getattr(workflow, "build_actor", None)
        if callable(build_actor):
            attempts = [
                {
                    "task_id": task_id,
                    "description": description,
                    "io_instructions": io_instructions,
                    "data_dir": data_dir,
                    "output_path": output_path,
                    "dag_options": dag_options,
                },
                {
                    "task_id": task_id,
                    "description": description,
                    "io_instructions": io_instructions,
                    "data_dir": data_dir,
                    "output_path": output_path,
                },
                {
                    "description": description,
                    "io_instructions": io_instructions,
                    "data_dir": data_dir,
                    "output_path": output_path,
                },
            ]
            for kwargs in attempts:
                try:
                    actor = build_actor(**kwargs)
                    if actor is not None:
                        return actor
                except TypeError:
                    continue
                except Exception as actor_error:
                    logger.warning("build_actor failed for task '%s': %s", task_id, actor_error)
                    break

        if dag_options and getattr(dag_options, "dag_mode", None) == "fine":
            try:
                from dslighting.workflows.search.aide_workflow import (
                    FineGrainedAIDEWorkflowDagActor,
                )

                return FineGrainedAIDEWorkflowDagActor(
                    task_id=task_id,
                    workflow=workflow,
                    description=description,
                    io_instructions=io_instructions,
                    output_path=output_path,
                    enable_debug_branch=getattr(dag_options, "enable_debug_branch", False),
                    max_retries=getattr(dag_options, "max_retries", 3),
                )
            except ImportError:
                logger.warning(
                    "FineGrainedAIDEWorkflowDagActor not found, falling back to SolveWorkflowActor"
                )

        return SolveWorkflowActor(
            task_id=task_id,
            workflow=workflow,
            description=description,
            io_instructions=io_instructions,
            data_dir=data_dir,
            output_path=output_path,
        )

    async def _execute_workflow_entrypoint(
        self,
        *,
        task_id: str,
        workflow: BaseWorkflow,
        description: str,
        io_instructions: str,
        data_dir: Path,
        output_path: Path,
        dag_options: DagRuntimeOptions,
    ) -> DagRunSummary | None:
        if not dag_options.enabled:
            await workflow.solve(
                description=description,
                io_instructions=io_instructions,
                data_dir=data_dir,
                output_path=output_path,
            )
            return None

        actor = self._build_dag_actor(
            task_id=task_id,
            workflow=workflow,
            description=description,
            io_instructions=io_instructions,
            data_dir=data_dir,
            output_path=output_path,
            dag_options=dag_options,
        )
        try:
            node_timeout_seconds = float(getattr(dag_options, "node_timeout_seconds", 300.0))
            if node_timeout_seconds <= 0:
                raise ValueError
        except (TypeError, ValueError):
            node_timeout_seconds = 300.0

        runtime_engine = str(getattr(dag_options, "runtime_engine", "standard")).strip().lower()
        if runtime_engine == "pipeline":
            runtime = create_pipeline_runtime(
                options=dag_options,
                enable_pipeline=True,
                prefetch_depth=max(1, int(getattr(dag_options, "parallel_drafts", 1))),
            )
            runtime.dispatcher = NodeDispatcher(default_timeout=node_timeout_seconds)
        else:
            runtime = DagRuntime(
                options=dag_options,
                dispatcher=NodeDispatcher(default_timeout=node_timeout_seconds),
            )

        summary = await runtime.run_actor(actor)
        final_result = getattr(summary, "final_result", None)
        if isinstance(final_result, dict):
            status = str(final_result.get("status", "")).strip().lower()
            has_error = bool(final_result.get("error"))
            if status and status != "success":
                raise WorkflowError(
                    final_result.get("error")
                    or f"DAG workflow reported status '{status}' for task '{task_id}'",
                    error_code="WRK-003",
                    details={
                        "task_id": task_id,
                        "final_result": final_result,
                        "dag_summary": summary.to_dict() if summary else None,
                    },
                    suggestion="Review workflow final_result status/error for the failing phase and retry.",
                )
            if has_error:
                raise WorkflowError(
                    final_result.get("error")
                    or f"DAG workflow reported an error for task '{task_id}'",
                    error_code="WRK-003",
                    details={
                        "task_id": task_id,
                        "final_result": final_result,
                        "dag_summary": summary.to_dict() if summary else None,
                    },
                    suggestion="Review workflow final_result error payload and execution logs.",
                )
        if not summary.success:
            raise WorkflowError(
                summary.last_error or f"DAG runtime execution failed for task '{task_id}'",
                error_code="WRK-003",
                details={"task_id": task_id, "dag_summary": summary.to_dict() if summary else None},
                suggestion="Review the workflow execution logs and check for errors in task implementation",
            )
        return summary

    def get_run_records(self) -> list[dict[str, Any]]:
        """
        Return a shallow copy of stored run metadata records for summary rendering.
        """
        return [record.copy() for record in self.run_records]

    @staticmethod
    def _redact_config_snapshot(config_snapshot: dict[str, Any]) -> dict[str, Any]:
        """
        Redact sensitive values in a config snapshot before persistence/exposure.
        """
        redacted = dict(config_snapshot)
        llm_section = redacted.get("llm")
        if isinstance(llm_section, dict):
            llm_copy = dict(llm_section)
            if "api_key" in llm_copy and llm_copy["api_key"]:
                llm_copy["api_key"] = "***REDACTED***"
            if isinstance(llm_copy.get("api_keys"), list):
                llm_copy["api_keys"] = ["***REDACTED***"] * len(llm_copy["api_keys"])
            redacted["llm"] = llm_copy
        return redacted

    def get_config_snapshot(self) -> dict[str, Any]:
        """
        Return the runner config snapshot with credentials redacted.
        """
        snapshot = self.config.model_dump()
        return self._redact_config_snapshot(snapshot)

    def _persist_run_metadata(
        self,
        *,
        workspace_service,
        task_config: DSLightingConfig,
        task: TaskDefinition,
        description: str,
        io_instructions: str,
        data_dir: Path | None,
        output_path: Path | None,
        result: Any,
        llm_service: LLMService | None,
        sandbox_service: Any | None,
        workflow: BaseWorkflow | None,
        dag_summary: dict[str, Any] | None,
        started_at: datetime,
        ended_at: datetime,
        duration_seconds: float,
        total_cost: float,
    ) -> None:
        """Orchestrate persistence of all run metadata to workspace.

        Delegates to focused helper methods for:
        - Metadata serialization
        - Code artifacts (final solution, model training code)
        - Telemetry artifacts (LLM calls, sandbox runs, search tree)
        - Evaluation results (CSV)
        - Metadata JSON and run history recording
        """
        # Extract runtime data from services
        runtime_data = self._extract_runtime_data(llm_service, sandbox_service, workflow)
        llm_calls = runtime_data["llm_calls"]
        sandbox_runs = runtime_data["sandbox_runs"]
        best_node = runtime_data["best_node"]

        # ========================================================================
        # Stage 1: Serialize run metadata
        # ========================================================================
        metadata = self._serialize_run_metadata(
            workspace_service=workspace_service,
            task_config=task_config,
            task=task,
            description=description,
            io_instructions=io_instructions,
            data_dir=data_dir,
            output_path=output_path,
            result=result,
            llm_service=llm_service,
            llm_calls=llm_calls,
            sandbox_runs=sandbox_runs,
            workflow=workflow,
            best_node=best_node,
            search_tree_data=None,  # Will be extracted in this method
            search_tree_info=None,
            dag_summary=dag_summary,
            started_at=started_at,
            ended_at=ended_at,
            duration_seconds=duration_seconds,
            total_cost=total_cost,
        )

        # ========================================================================
        # Stage 2: Save code artifacts
        # ========================================================================
        self._save_code_artifacts(
            workspace_service=workspace_service,
            task_config=task_config,
            task=task,
            result=result,
            best_node=best_node,
            metadata=metadata,
        )

        # ========================================================================
        # Stage 3: Save telemetry artifacts
        # ========================================================================
        telemetry_dir = "telemetry"
        search_tree_data, search_tree_info = self._extract_search_tree(workflow, best_node)
        detail_files = self._save_telemetry_artifacts(
            workspace_service=workspace_service,
            telemetry_dir=telemetry_dir,
            llm_calls=llm_calls,
            sandbox_runs=sandbox_runs,
            search_tree_data=search_tree_data,
            search_tree_info=search_tree_info,
        )

        # Update metadata with search tree info and detail files
        self._update_metadata_with_telemetry(
            metadata=metadata,
            search_tree_data=search_tree_data,
            search_tree_info=search_tree_info,
            detail_files=detail_files,
            telemetry_dir=telemetry_dir,
        )

        # ========================================================================
        # Stage 4: Save evaluation result
        # ========================================================================
        self._save_evaluation_result(
            workspace_service=workspace_service,
            task=task,
            result=result,
            total_cost=total_cost,
            duration_seconds=duration_seconds,
        )

        # ========================================================================
        # Stage 5: Persist metadata JSON and record entry
        # ========================================================================
        self._persist_metadata_and_record(
            workspace_service=workspace_service,
            task=task,
            metadata=metadata,
            telemetry_dir=telemetry_dir,
        )

    def _serialize_run_metadata(
        self,
        *,
        workspace_service,
        task_config: DSLightingConfig,
        task: TaskDefinition,
        description: str,
        io_instructions: str,
        data_dir: Path | None,
        output_path: Path | None,
        result: Any,
        llm_service: LLMService | None,
        llm_calls: list[dict[str, Any]],
        sandbox_runs: list[dict[str, Any]],
        workflow: BaseWorkflow | None,
        best_node: Any | None,
        search_tree_data: list[dict[str, Any]] | None,
        search_tree_info: dict[str, Any] | None,
        dag_summary: dict[str, Any] | None,
        started_at: datetime,
        ended_at: datetime,
        duration_seconds: float,
        total_cost: float,
    ) -> dict[str, Any]:
        """Serialize all run metadata to a dictionary.

        Args:
            workspace_service: Service for workspace file operations.
            task_config: The task configuration.
            task: The task definition.
            description: Task description from adapter/runtime spec.
            io_instructions: I/O instructions from adapter/runtime spec.
            data_dir: Path to data directory.
            output_path: Path to expected output file.
            result: The workflow execution result.
            llm_service: The LLM service instance.
            llm_calls: LLM call history.
            sandbox_runs: Sandbox execution history.
            workflow: The workflow instance.
            best_node: The best node from workflow state.
            search_tree_data: Serialized search tree nodes.
            search_tree_info: Search tree metadata.
            dag_summary: DAG runtime summary.
            started_at: Run start timestamp.
            ended_at: Run end timestamp.
            duration_seconds: Run duration in seconds.
            total_cost: Total LLM cost.

        Returns:
            A dictionary containing all serialized run metadata.
        """
        # ========================================================================
        # Stage 1: Collect run context
        # ========================================================================
        run_context = self._collect_run_context(
            workspace_service=workspace_service,
            task_config=task_config,
            llm_service=llm_service,
            best_node=best_node,
        )

        # ========================================================================
        # Stage 2: Build metadata dictionary
        # ========================================================================
        metadata = self._build_metadata_dict(
            task_config=task_config,
            task=task,
            description=description,
            io_instructions=io_instructions,
            data_dir=data_dir,
            output_path=output_path,
            result=result,
            llm_calls=llm_calls,
            sandbox_runs=sandbox_runs,
            best_node=best_node,
            search_tree_info=search_tree_info,
            dag_summary=dag_summary,
            started_at=started_at,
            ended_at=ended_at,
            duration_seconds=duration_seconds,
            total_cost=total_cost,
            run_context=run_context,
        )

        return metadata

    def _collect_run_context(
        self,
        *,
        workspace_service,
        task_config: DSLightingConfig,
        llm_service: LLMService | None,
        best_node: Any | None,
    ) -> dict[str, Any]:
        """Collect run context data from services.

        Args:
            workspace_service: Service for workspace file operations.
            task_config: The task configuration.
            llm_service: The LLM service instance.
            best_node: The best node from workflow state.

        Returns:
            A dictionary containing run context data.
        """
        workspace_dir = workspace_service.get_path("run_dir") if workspace_service else None
        usage_summary = llm_service.get_usage_summary() if llm_service else {}
        config_snapshot = self._redact_config_snapshot(task_config.model_dump())
        benchmark_snapshot = self._build_benchmark_snapshot()

        # Determine final code path
        final_code_path: str | None = None
        if workspace_service:
            final_candidate = (
                workspace_service.get_path("artifacts") / "final_submission" / "final_solution.py"
            )
            if final_candidate.exists():
                final_code_path = str(final_candidate)
            elif best_node:
                final_code_path = best_node.final_submission_path or best_node.code_artifact_path

        # Filter parameters
        filtered_parameters = {
            key: value
            for key, value in (task_config.run.parameters or {}).items()
            if value not in (None, "", [], {})
        }

        return {
            "workspace_dir": workspace_dir,
            "usage_summary": usage_summary,
            "config_snapshot": config_snapshot,
            "benchmark_snapshot": benchmark_snapshot,
            "final_code_path": final_code_path,
            "filtered_parameters": filtered_parameters,
        }

    def _build_metadata_dict(
        self,
        *,
        task_config: DSLightingConfig,
        task: TaskDefinition,
        description: str,
        io_instructions: str,
        data_dir: Path | None,
        output_path: Path | None,
        result: Any,
        llm_calls: list[dict[str, Any]],
        sandbox_runs: list[dict[str, Any]],
        best_node: Any | None,
        search_tree_info: dict[str, Any] | None,
        dag_summary: dict[str, Any] | None,
        started_at: datetime,
        ended_at: datetime,
        duration_seconds: float,
        total_cost: float,
        run_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Build the metadata dictionary from collected context.

        Args:
            task_config: The task configuration.
            task: The task definition.
            description: Task description from adapter/runtime spec.
            io_instructions: I/O instructions from adapter/runtime spec.
            data_dir: Path to data directory.
            output_path: Path to expected output file.
            result: The workflow execution result.
            llm_calls: LLM call history.
            sandbox_runs: Sandbox execution history.
            best_node: The best node from workflow state.
            search_tree_info: Search tree metadata.
            dag_summary: DAG runtime summary.
            started_at: Run start timestamp.
            ended_at: Run end timestamp.
            duration_seconds: Run duration in seconds.
            total_cost: Total LLM cost.
            run_context: Pre-collected run context data.

        Returns:
            A dictionary containing all serialized run metadata.
        """
        metadata = {
            "run_name": task_config.run.run_name,
            "workspace_dir": (
                str(run_context["workspace_dir"]) if run_context["workspace_dir"] else None
            ),
            "workflow": task_config.workflow.name if task_config.workflow else None,
            "parameters": run_context["filtered_parameters"],
            "benchmark": run_context["benchmark_snapshot"],
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
                "usage": run_context["usage_summary"],
                "cost_per_token": run_context["usage_summary"].get("cost_per_token"),
                "llm_call_count": len(llm_calls),
                "sandbox_run_count": len(sandbox_runs),
                "final_code": best_node.code if best_node else None,
                "final_code_path": run_context["final_code_path"],
                "best_node_id": best_node.id if best_node else None,
                "best_path_node_ids": (
                    search_tree_info.get("best_path") if search_tree_info else None
                ),
            },
            "config_snapshot": run_context["config_snapshot"],
        }

        if dag_summary:
            metadata["dag_runtime"] = dag_summary

        return metadata

    def _save_code_artifacts(
        self,
        *,
        workspace_service,
        task_config: DSLightingConfig,
        task: TaskDefinition,
        result: Any,
        best_node: Any | None,
        metadata: dict[str, Any],
    ) -> None:
        """Save generated code artifacts to the workspace.

        This method handles:
        1. Saving final_solution.py to run_dir
        2. Saving model training code with metadata to code_history directory

        Args:
            workspace_service: Service for workspace file operations.
            task_config: The task configuration.
            task: The task definition.
            result: The workflow execution result.
            best_node: The best node from workflow state.
            metadata: The metadata dictionary to update with code paths.
        """
        import re
        from datetime import datetime as dt

        # Save Final Code to a standard location
        if best_node and best_node.code:
            final_code_file = workspace_service.get_path("run_dir") / "final_solution.py"
            try:
                with open(final_code_file, "w", encoding="utf-8") as f:
                    f.write(best_node.code)
                metadata["summary"]["final_code_path"] = str(final_code_file)
                logger.info(f"Saved final solution to: {final_code_file}")
            except Exception as e:
                logger.warning(f"Failed to save final solution: {e}")

            # Save model training code to code_history directory
            try:
                code_history_dir = workspace_service.get_path("sandbox_workdir") / "code_history"
                code_history_dir.mkdir(parents=True, exist_ok=True)

                # Find next available number for model training code
                existing_model_codes = list(code_history_dir.glob("model_code_*.py"))
                if existing_model_codes:
                    numbers = []
                    for f in existing_model_codes:
                        match = re.search(r"model_code_(\d+)\.py", f.name)
                        if match:
                            numbers.append(int(match.group(1)))
                    next_num = max(numbers) + 1 if numbers else 1
                else:
                    next_num = 1

                # Save with formatted number and metadata
                model_code_filename = f"model_code_{next_num:0{CODE_FILENAME_ZERO_PADDING}d}.py"
                model_code_filepath = code_history_dir / model_code_filename

                # Add header with training metadata
                header = f"""# Code Type: MODEL TRAINING
# Workflow: {task_config.workflow.name if task_config.workflow else "Unknown"}
# Model: {task_config.llm.model if task_config.llm else "Unknown"}
# Generated: {dt.now().strftime("%Y-%m-%d %H:%M:%S")}
# Task ID: {task.task_id}
# Success: {not (isinstance(result, str) and result.startswith("[ERROR]"))}

"""
                model_code_filepath.write_text(header + best_node.code)
                logger.info(f"Saved model training code to workspace: {model_code_filepath}")
            except Exception as e:
                logger.warning(f"Failed to save model training code to code_history: {e}")

    def _save_telemetry_artifacts(
        self,
        *,
        workspace_service,
        telemetry_dir: str,
        llm_calls: list[dict[str, Any]],
        sandbox_runs: list[dict[str, Any]],
        search_tree_data: list[dict[str, Any]] | None,
        search_tree_info: dict[str, Any] | None,
    ) -> dict[str, str]:
        """Write telemetry artifacts to the workspace.

        This method saves:
        1. LLM calls history (JSONL format)
        2. Sandbox runs history (JSONL format)
        3. Search tree data (JSON format)

        Args:
            workspace_service: Service for workspace file operations.
            telemetry_dir: Directory name for telemetry files.
            llm_calls: LLM call history.
            sandbox_runs: Sandbox execution history.
            search_tree_data: Serialized search tree nodes.
            search_tree_info: Search tree metadata.

        Returns:
            A dictionary mapping artifact types to their relative paths.
        """
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
                json.dumps(self._to_json_safe(search_tree_data), ensure_ascii=False, indent=2),
                "artifacts",
                search_tree_path,
            )
            detail_files["search_tree"] = f"artifacts/{search_tree_path}"

        return detail_files

    def _save_evaluation_result(
        self,
        *,
        workspace_service,
        task: TaskDefinition,
        result: Any,
        total_cost: float,
        duration_seconds: float,
    ) -> None:
        """Save evaluation result to a CSV file in the workspace.

        Args:
            workspace_service: Service for workspace file operations.
            task: The task definition.
            result: The evaluation score or result.
            total_cost: Total LLM cost.
            duration_seconds: Run duration in seconds.
        """
        # Save Evaluation Result to a CSV in workspace
        if isinstance(result, (float, int, str)) and not str(result).startswith("[ERROR]"):
            try:
                res_file = workspace_service.get_path("run_dir") / "evaluation_result.csv"
                with open(res_file, "w") as f:
                    f.write("task_id,score,cost,duration\n")
                    f.write(f"{task.task_id},{result},{total_cost},{duration_seconds}\n")
                logger.info(f"Saved evaluation result to: {res_file}")
            except Exception:
                pass

    def _write_jsonl(
        self, workspace_service, relative_path: str, records: list[dict[str, Any]]
    ) -> None:
        """Write newline-delimited JSON records to an artifacts sub-path."""
        content = "\n".join(
            json.dumps(self._to_json_safe(record), ensure_ascii=False) for record in records
        )
        workspace_service.write_file(content, "artifacts", relative_path)

    def _format_result(self, result: Any) -> Any:
        """Return a serialization-friendly representation of the workflow result."""
        if isinstance(result, Path):
            return str(result)
        return result

    def _to_json_safe(self, value: Any) -> Any:
        """Recursively convert objects into JSON-serializable values."""
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, dict):
            return {str(key): self._to_json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._to_json_safe(item) for item in value]
        return value

    def _persist_metadata_and_record(
        self,
        *,
        workspace_service,
        task: TaskDefinition,
        metadata: dict[str, Any],
        telemetry_dir: str,
    ) -> None:
        """Persist metadata JSON to file and record entry in run history.

        Args:
            workspace_service: Service for workspace file operations.
            task: The task definition.
            metadata: The metadata dictionary to persist.
            telemetry_dir: Directory name for telemetry files.
        """
        metadata = self._to_json_safe(metadata)
        run_metadata_path = f"{telemetry_dir}/run_metadata.json"
        workspace_service.write_file(
            json.dumps(metadata, ensure_ascii=False, indent=2), "artifacts", run_metadata_path
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
            "dag_runtime": metadata.get("dag_runtime"),
        }
        self.run_records.append(record_entry)

    def _update_metadata_with_telemetry(
        self,
        *,
        metadata: dict[str, Any],
        search_tree_data: list[dict[str, Any]] | None,
        search_tree_info: dict[str, Any] | None,
        detail_files: dict[str, str],
        telemetry_dir: str,
    ) -> None:
        """Update metadata dictionary with search tree and telemetry file information.

        Args:
            metadata: The metadata dictionary to update.
            search_tree_data: Serialized search tree nodes.
            search_tree_info: Search tree metadata.
            detail_files: Dictionary of telemetry artifact file paths.
            telemetry_dir: Directory name for telemetry files.
        """
        if search_tree_data:
            metadata["search_tree"] = {
                "node_count": len(search_tree_data),
                "best_node_id": search_tree_info.get("best_node_id") if search_tree_info else None,
                "best_path_node_ids": (
                    search_tree_info.get("best_path") if search_tree_info else None
                ),
                "file": f"artifacts/{telemetry_dir}/search_tree.json",
            }
        else:
            metadata["search_tree"] = None

        if detail_files:
            metadata["detail_files"] = detail_files

    def _extract_runtime_data(
        self,
        llm_service: LLMService | None,
        sandbox_service: Any | None,
        workflow: BaseWorkflow | None,
    ) -> dict[str, Any]:
        """Extract runtime data from services.

        Args:
            llm_service: The LLM service instance.
            sandbox_service: The sandbox service instance.
            workflow: The workflow instance.

        Returns:
            Dictionary with llm_calls, sandbox_runs, and best_node.
        """
        return {
            "llm_calls": llm_service.get_call_history() if llm_service else [],
            "sandbox_runs": sandbox_service.get_execution_history() if sandbox_service else [],
            "best_node": self._get_best_node(workflow),
        }

    def _get_best_node(self, workflow: BaseWorkflow | None):
        if not workflow or not hasattr(workflow, "state"):
            return None
        state = workflow.state
        if isinstance(state, JournalState):
            return state.get_best_node()
        return None

    def _extract_search_tree(self, workflow: BaseWorkflow | None, best_node: Any | None):
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

    def _extract_best_path(self, state: JournalState, best_node: Any | None) -> list[str] | None:
        if not best_node:
            return None
        path: list[str] = []
        current = best_node
        while current:
            path.append(current.id)
            current = state.get_node(current.parent_id) if current.parent_id else None
        return list(reversed(path))

    def _build_benchmark_snapshot(self) -> dict[str, Any] | None:
        if not self.benchmark:
            return None
        snapshot: dict[str, Any] = {"name": getattr(self.benchmark, "name", None)}
        data_dir = getattr(self.benchmark, "data_dir", None)
        if data_dir is not None:
            snapshot["data_dir"] = str(data_dir)
        config_value = getattr(self.benchmark, "config", None)
        if isinstance(config_value, dict):
            snapshot["config"] = config_value
        return snapshot
