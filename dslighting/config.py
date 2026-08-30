# dslighting/config.py

from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from dslighting.benchmark import RuntimeSchedulerOptions

from dslighting.core.visualization_policy import VisualizationPolicy
from dslighting.utils.constants import DEFAULT_CACHE_MAX_ENTRIES


class LLMConfig(BaseModel):
    """LLM service settings."""

    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    api_key: Optional[str] = Field(
        None, description="API key (single key or first from list). For key rotation, use api_keys."
    )
    api_keys: Optional[List[str]] = Field(
        None,
        description="List of API keys for rotation. If both api_key and api_keys are set, api_keys takes precedence.",
    )
    api_base: Optional[str] = "https://api.openai.com/v1"
    provider: Optional[str] = Field(
        None, description="Optional LiteLLM provider alias, e.g. 'siliconflow'."
    )
    default_headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional HTTP headers included with every LLM request.",
    )
    max_retries: int = 3
    max_concurrent_per_key: int = 20

    def get_api_keys(self) -> List[str]:
        """
        Get list of API keys for rotation.

        Returns:
            List of API keys. Priority: api_keys > api_key > []
        """
        if self.api_keys:
            return self.api_keys
        elif self.api_key:
            return [self.api_key]
        else:
            return []


class SandboxConfig(BaseModel):
    """Code execution sandbox settings."""

    timeout: int = 6 * 3600
    backend: str = "local"  # Sandbox backend: local, e2b, ds_sandbox
    backend_type: str = "docker"  # Backend type for ds_sandbox: docker, local
    api_key: Optional[str] = None  # API key for e2b


class DataAnalysisConfig(BaseModel):
    """Settings for DataAnalyzer runtime behavior."""

    enabled: bool = True
    cache_enabled: bool = True
    cache_dir: Optional[str] = None
    cache_max_entries: int = DEFAULT_CACHE_MAX_ENTRIES
    cache_debug_metrics: bool = False
    analyzer_version: Optional[str] = None
    profile: Literal["fast", "balanced", "full"] = "balanced"
    max_artifacts: int = 12
    max_report_chars: Optional[int] = 14000
    document_preview_lines: int = 12
    enable_document_inspection: bool = True
    enable_database_inspection: bool = True
    tabular_tolerant_fallback: bool = True


class AgentRuntimeObservationConfig(BaseModel):
    """Shared observation-window settings for agent workflows."""

    max_tokens: int = 4000
    head_tokens: int = 2000
    tail_tokens: int = 2000
    max_chars: Optional[int] = None


class AgentRuntimeContextConfig(BaseModel):
    """Shared prompt-history window settings for agent workflows."""

    strategy: Literal["recent_turns", "summarize_old_turns", "hybrid"] = "hybrid"
    max_history_chars: int = 48000
    keep_recent_turns: int = 14
    max_observation_chars: int = 16000
    summary_trigger_turns: int = 18
    summary_max_chars: int = 4000
    keep_latest_feedback_only: bool = True
    max_feedback_retries: int = 2
    recent_observation_window: int = 8
    max_feedback_chars: int = 1200


class AgentRuntimeConfig(BaseModel):
    """Shared runtime settings consumed by agent workflows."""

    max_steps: int = 10
    observation: AgentRuntimeObservationConfig = Field(
        default_factory=AgentRuntimeObservationConfig
    )
    context: AgentRuntimeContextConfig = Field(default_factory=AgentRuntimeContextConfig)


class OutputContractConfig(BaseModel):
    """Shared output artifact contract settings."""

    require_output_before_completion: bool = False
    missing_output_feedback_retries: int = 0
    max_preview_rows: int = 3
    max_candidate_files: int = 20
    allow_runner_fallback: bool = True


class TaskConfig(BaseModel):
    """Defines the problem to be solved."""

    goal: str = "Solve the given data science task."
    eval_metric: Optional[str] = None
    data_dir: Optional[str] = None


class DagRuntimeConfig(BaseModel):
    """Dynamic DAG runtime settings."""

    enabled: bool = False
    max_inflight_nodes: int = 256
    node_timeout_seconds: float = 300.0
    ready_queue_policy: Literal["fifo", "priority", "lpt_backfill"] = "priority"
    llm_global_max_concurrency: Optional[int] = None
    llm_model_quotas: Dict[str, int] = Field(default_factory=dict)
    enable_speculative_branches: bool = False
    dag_mode: Literal["coarse", "fine"] = "coarse"
    enable_debug_branch: bool = False
    max_retries: int = 3
    dag_actor_strategy: Literal["coarse", "declarative"] = "coarse"
    runtime_engine: Literal["standard", "pipeline"] = "standard"
    parallel_drafts: int = 1
    branch_budget: Optional[int] = None
    node_timeout_policy: Literal["fixed", "adaptive"] = "fixed"
    node_timeout_by_op: Dict[str, float] = Field(default_factory=dict)


class RunConfig(BaseModel):
    """Settings for a specific execution run."""

    run_name: str = "dslighting_run"
    total_steps: int = 4
    keep_all_workspaces: bool = Field(
        False, description="If True, do not delete any workspace after execution."
    )
    keep_workspace_on_failure: bool = Field(
        True, description="If True, keep the workspace only if the task execution fails."
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary runtime parameters saved for telemetry."
    )
    dag_runtime: DagRuntimeConfig = Field(default_factory=DagRuntimeConfig)


class SchedulerConfig(BaseModel):
    """Task scheduling and runtime resource settings."""

    max_concurrency: Optional[int] = None
    scheduler_policy: str = "full_parallel"
    queue_policy: str = "fifo"
    workload_mode: str = "auto"
    gpu_policy: str = "auto"
    gpu_ids: Optional[List[int]] = None
    gpu_max_tasks_per_device: Optional[int] = None
    gpu_memory_utilization_target: float = 0.85
    gpu_reserved_memory_gb: float = 2.0
    enable_monitoring: bool = False
    enable_adaptive_concurrency: bool = False
    adaptive_target_p95_seconds: float = 60.0
    oom_max_retries: int = 1
    oom_retry_backoff_seconds: float = 2.0
    oom_retry_memory_growth: float = 1.35
    sandbox_memory_mode: str = "off"
    sandbox_default_memory_gb: float = 6.0
    llm_max_concurrency: Optional[int] = None
    cpu_worker_pool_size: Optional[int] = None
    exp_name: Optional[str] = None
    monitor_language: Optional[str] = None
    enable_file_sharing: bool = True
    checkpoint_resume_enabled: bool = False
    run_id: Optional[str] = None
    enable_task_rate_limiting: Optional[bool] = None
    llm_task_start_rate: Optional[float] = None
    sandbox_task_start_rate: Optional[float] = None
    task_rate_burst_factor: Optional[float] = None

    def to_runtime_options(self) -> "RuntimeSchedulerOptions":
        """Convert scheduler settings to RuntimeSchedulerOptions."""
        from dslighting.benchmark import RuntimeSchedulerOptions

        return RuntimeSchedulerOptions(
            max_concurrency=self.max_concurrency,
            scheduler_policy=self.scheduler_policy,
            queue_policy=self.queue_policy,
            workload_mode=self.workload_mode,
            gpu_policy=self.gpu_policy,
            gpu_ids=self.gpu_ids,
            gpu_max_tasks_per_device=self.gpu_max_tasks_per_device,
            gpu_memory_utilization_target=self.gpu_memory_utilization_target,
            gpu_reserved_memory_gb=self.gpu_reserved_memory_gb,
            enable_monitoring=self.enable_monitoring,
            enable_adaptive_concurrency=self.enable_adaptive_concurrency,
            adaptive_target_p95_seconds=self.adaptive_target_p95_seconds,
            oom_max_retries=self.oom_max_retries,
            oom_retry_backoff_seconds=self.oom_retry_backoff_seconds,
            oom_retry_memory_growth=self.oom_retry_memory_growth,
            sandbox_memory_mode=self.sandbox_memory_mode,
            sandbox_default_memory_gb=self.sandbox_default_memory_gb,
            llm_max_concurrency=self.llm_max_concurrency,
            cpu_worker_pool_size=self.cpu_worker_pool_size,
            exp_name=self.exp_name,
            monitor_language=self.monitor_language,
            enable_file_sharing=self.enable_file_sharing,
            checkpoint_resume_enabled=self.checkpoint_resume_enabled,
            run_id=self.run_id,
            enable_task_rate_limiting=self.enable_task_rate_limiting,
            llm_task_start_rate=self.llm_task_start_rate,
            sandbox_task_start_rate=self.sandbox_task_start_rate,
            task_rate_burst_factor=self.task_rate_burst_factor,
        )


class AgentSearchConfig(BaseModel):
    """Parameters for Paradigm 2 (AIDE/AutoMind) search."""

    num_drafts: int = 5
    debug_prob: float = 0.8
    max_iterations: int = 5
    max_debug_depth: int = 10


class AutoKaggleConfig(BaseModel):
    """Parameters for the AutoKaggle SOP workflow."""

    max_attempts_per_phase: int = 10
    success_threshold: float = 3.0


class AgentVisualizationConfig(BaseModel):
    """Shared visualization policy for all code-writing agents."""

    policy: VisualizationPolicy = VisualizationPolicy.NO_DISPLAY


class AgentConfig(BaseModel):
    """Configuration for a specific agent's behavior."""

    search: AgentSearchConfig = Field(default_factory=AgentSearchConfig)
    max_retries: int = 10
    autokaggle: AutoKaggleConfig = Field(default_factory=AutoKaggleConfig)
    visualization: AgentVisualizationConfig = Field(default_factory=AgentVisualizationConfig)
    task_context: Dict[str, Any] = Field(default_factory=dict)


class OptimizerConfig(BaseModel):
    """Parameters for Paradigm 3 (AFlow) meta-optimization."""

    max_rounds: int = 10
    validation_runs_per_candidate: int = 1
    top_k_selection: int = 2


class DSFlowConfig(BaseModel):
    """Parameters for DSFlow's two-stage workflow meta-optimization."""

    best_workflow_path: Optional[str] = Field(
        None,
        description=(
            "Optional saved best_workflow.py. When set, skip meta-optimization "
            "and evaluate this workflow directly."
        ),
    )
    max_rounds: int = 4
    top_k_selection: int = 2
    fine_evaluate_each_generation: bool = False

    task_sample_size: int = 3
    task_sample_strategy: Literal["first", "random"] = "first"

    operator_library_enabled: bool = True
    operator_library_path: str = "runs/dsflow_operator_library.json"
    operator_library_max_ops_in_prompt: int = 15

    # Persisting generated operators in the JSON operator library is enough for
    # packaged installs. Source-file synchronization remains opt-in because an
    # installed package may be read-only.
    auto_sync_custom_operators: bool = False
    progress_enabled: bool = True

    coarse_capture: Literal["plan", "code"] = "code"
    coarse_max_llm_calls: int = 6
    workflow_generation_max_attempts: int = 2
    operator_generation_max_attempts: int = 2

    final_selection_mode: Literal["fine", "weighted"] = "weighted"
    weight_fine: float = 0.5
    weight_coarse: float = 0.5
    final_fine_normalization: Literal["none", "minmax", "rank"] = "rank"


class WorkflowConfig(BaseModel):
    """Specifies which workflow to run and its parameters."""

    name: str
    params: Dict[str, Any] = Field(default_factory=dict)
    # This field is populated at runtime by main.py, not from the YAML file.
    class_ref: Optional[Any] = Field(None, exclude=True)


class DSLightingConfig(BaseModel):
    """The root configuration model for the entire DSLighting application."""

    run: RunConfig = Field(default_factory=RunConfig)
    task: TaskConfig = Field(default_factory=TaskConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    data_analysis: DataAnalysisConfig = Field(default_factory=DataAnalysisConfig)
    agent_runtime: AgentRuntimeConfig = Field(default_factory=AgentRuntimeConfig)
    output_contract: OutputContractConfig = Field(default_factory=OutputContractConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)

    # Paradigm-specific configurations
    workflow: Optional[WorkflowConfig] = None
    agent: AgentConfig = Field(default_factory=AgentConfig)
    optimizer: Optional[OptimizerConfig] = None
    dsflow: DSFlowConfig = Field(default_factory=DSFlowConfig)

    model_config = ConfigDict(extra="forbid")  # Pydantic configuration
