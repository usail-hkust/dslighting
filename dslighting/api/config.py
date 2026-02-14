"""
Configuration classes for DSLighting unified API.

This module provides a clean, layered configuration system for DSLighting benchmarks:
- AgentSettingsConfig: How the agent works (model, workflow, iterations)
- RuntimeConfig: How tasks are scheduled (GPU, concurrency, DAG settings)
"""

import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional

# Type-only import to avoid exposing benchmark internals in API layer
if TYPE_CHECKING:
    from dslighting.benchmark import RuntimeSchedulerOptions

# Import shared workflow utilities
from dslighting.core.config.shared import get_workflow_for_benchmark


@dataclass
class AgentSettingsConfig:
    """
    Agent configuration (Second Layer: How the Agent works).

    This configuration defines how the AI agent processes tasks, including
    LLM settings, workflow selection, and search parameters.
    """

    # LLM Configuration
    model: Optional[str] = None
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    provider: Optional[str] = None
    temperature: Optional[float] = None

    # Workflow Configuration
    workflow: Optional[str] = None
    max_iterations: Optional[int] = None
    num_drafts: Optional[int] = None

    def get_model(self) -> str:
        """Get model name with environment variable fallback."""
        if self.model:
            return self.model
        return os.getenv("LLM_MODEL", "gpt-4o-mini")

    def get_workflow(self, benchmark_name: str) -> str:
        """Get workflow name based on benchmark type."""
        if self.workflow:
            return self.workflow
        return get_workflow_for_benchmark(benchmark_name, default="aide")

    def get_max_iterations(self) -> int:
        """Get maximum iterations with intelligent default."""
        return self.max_iterations or 5

    def get_temperature(self) -> Optional[float]:
        """Get temperature setting."""
        return self.temperature

    def get_num_drafts(self) -> Optional[int]:
        """Get number of drafts."""
        return self.num_drafts


@dataclass
class RuntimeConfig:
    """
    Runtime configuration (Third Layer: How tasks are scheduled).

    This configuration defines how benchmark tasks are executed, including:
    - Task scheduling (concurrency, GPU allocation)
    - DAG runtime settings (enabled, mode, inflight nodes)
    - OOM handling and resource management
    - Monitoring and adaptive concurrency

    All settings map directly to RuntimeSchedulerOptions.

    Attributes:
        # Task Scheduling
            max_concurrency: Maximum number of concurrent tasks
            scheduler_policy: Scheduling policy
            queue_policy: Queue policy
            workload_mode: Workload mode

        # DAG Runtime
            dag_enabled: Enable DAG runtime
            dag_mode: DAG mode ("coarse", "fine")
            max_inflight_nodes: Maximum nodes in flight
            dag_node_timeout_seconds: Timeout for one DAG node execution (seconds)
            ready_queue_policy: Ready queue policy
            llm_global_max_concurrency: Global LLM concurrency
            llm_model_quotas: Per-model LLM quotas
            dag_max_retries: DAG node max retries

        # GPU Configuration
            gpu_policy: GPU allocation policy
            gpu_ids: Manual GPU ID list
            gpu_max_tasks_per_device: Max tasks per GPU
            gpu_memory_utilization_target: Target GPU memory utilization
            gpu_reserved_memory_gb: Reserved GPU memory in GB

        # Monitoring and Adaptation
            enable_monitoring: Enable system monitoring
            enable_adaptive_concurrency: Enable adaptive concurrency
            adaptive_target_p95_seconds: Target P95 runtime for adaptation

        # OOM Handling
            oom_max_retries: Max retries on OOM
            oom_retry_backoff_seconds: Backoff time between retries
            oom_retry_memory_growth: Memory growth factor on retry

        # Resource Management
            sandbox_memory_mode: Sandbox memory mode
            sandbox_default_memory_gb: Default sandbox memory in GB
            llm_max_concurrency: Max LLM API concurrency
            llm_max_concurrent_per_key: Max concurrent requests per API key
            cpu_worker_pool_size: CPU worker pool size

        # Experiment Identification
            exp_name: Experiment name for monitoring identification
            monitor_language: Language for monitoring dashboard display (e.g., "zh", "en")

        # Checkpoint and Resume
            checkpoint_resume_enabled: Enable checkpoint/resume functionality
            run_id: Unique identifier for the run (used for checkpoint/resume)
    """

    # =====================================================================
    # Task Scheduling
    # =====================================================================
    max_concurrency: Optional[int] = None
    scheduler_policy: str = "full_parallel"
    queue_policy: str = "fifo"
    workload_mode: str = "auto"

    # =====================================================================
    # DAG Runtime (affects config.run.dag_runtime)
    # =====================================================================
    dag_enabled: bool = True
    dag_mode: str = "coarse"
    max_inflight_nodes: int = 18
    dag_node_timeout_seconds: float = 300.0
    ready_queue_policy: str = "fifo"
    llm_global_max_concurrency: Optional[int] = None
    llm_model_quotas: Dict[str, int] = field(default_factory=dict)
    dag_max_retries: int = 3
    enable_debug_branch: bool = False
    dag_actor_strategy: str = "coarse"
    dag_runtime_engine: str = "standard"
    dag_parallel_drafts: int = 1
    dag_branch_budget: Optional[int] = None
    dag_node_timeout_policy: str = "fixed"
    dag_node_timeout_by_op: Dict[str, float] = field(default_factory=dict)

    # =====================================================================
    # GPU Configuration
    # =====================================================================
    gpu_policy: str = "auto"
    gpu_ids: Optional[List[int]] = None
    gpu_max_tasks_per_device: Optional[int] = None
    gpu_memory_utilization_target: float = 0.85
    gpu_reserved_memory_gb: float = 2.0

    # =====================================================================
    # Monitoring and Adaptation
    # =====================================================================
    enable_monitoring: bool = False
    enable_adaptive_concurrency: bool = False
    adaptive_target_p95_seconds: float = 60.0

    # =====================================================================
    # OOM Handling
    # =====================================================================
    oom_max_retries: int = 1
    oom_retry_backoff_seconds: float = 2.0
    oom_retry_memory_growth: float = 1.35

    # =====================================================================
    # Resource Management
    # =====================================================================
    sandbox_memory_mode: str = "off"
    sandbox_default_memory_gb: float = 6.0
    sandbox_backend: str = "local"  # Sandbox backend: local, e2b, ds_sandbox
    sandbox_backend_type: str = "docker"  # Backend type for ds_sandbox: docker, local
    sandbox_api_key: Optional[str] = None  # API key for e2b
    llm_max_concurrency: Optional[int] = None
    llm_max_concurrent_per_key: Optional[int] = 20
    cpu_worker_pool_size: Optional[int] = None

    # =====================================================================
    # Experiment Identification (for monitoring and tracking)
    # =====================================================================
    exp_name: Optional[str] = None  # Experiment name for monitoring identification
    monitor_language: Optional[str] = None  # Language for monitoring dashboard display (e.g., "zh", "en")
    enable_file_sharing: bool = True  # Enable file-based metric sharing for cross-process monitoring

    # =====================================================================
    # Checkpoint and Resume
    # =====================================================================
    checkpoint_resume_enabled: bool = False  # Enable checkpoint/resume functionality
    run_id: Optional[str] = None  # Unique identifier for the run (used for checkpoint/resume)

    def to_runtime_options(self) -> "RuntimeSchedulerOptions":
        """Convert to RuntimeSchedulerOptions."""
        # Lazy import to avoid exposing benchmark internals at module level
        from dslighting.benchmark import RuntimeSchedulerOptions

        kwargs = {
            "max_concurrency": self.max_concurrency,
            "scheduler_policy": self.scheduler_policy,
            "queue_policy": self.queue_policy,
            "workload_mode": self.workload_mode,
            "gpu_policy": self.gpu_policy,
            "gpu_ids": self.gpu_ids,
            "gpu_max_tasks_per_device": self.gpu_max_tasks_per_device,
            "gpu_memory_utilization_target": self.gpu_memory_utilization_target,
            "gpu_reserved_memory_gb": self.gpu_reserved_memory_gb,
            "enable_monitoring": self.enable_monitoring,
            "enable_adaptive_concurrency": self.enable_adaptive_concurrency,
            "adaptive_target_p95_seconds": self.adaptive_target_p95_seconds,
            "oom_max_retries": self.oom_max_retries,
            "oom_retry_backoff_seconds": self.oom_retry_backoff_seconds,
            "oom_retry_memory_growth": self.oom_retry_memory_growth,
            "sandbox_memory_mode": self.sandbox_memory_mode,
            "sandbox_default_memory_gb": self.sandbox_default_memory_gb,
            "llm_max_concurrency": self.llm_max_concurrency,
            "cpu_worker_pool_size": self.cpu_worker_pool_size,
            "exp_name": self.exp_name,
            "monitor_language": self.monitor_language,
            "enable_file_sharing": self.enable_file_sharing,
            "checkpoint_resume_enabled": self.checkpoint_resume_enabled,
            "run_id": self.run_id,
        }
        # Create RuntimeSchedulerOptions with all kwargs
        options = RuntimeSchedulerOptions(**kwargs)
        return options

    def apply_dag_to_config(self, config):
        """Apply DAG settings to DSLightingConfig."""
        config.run.dag_runtime.enabled = self.dag_enabled
        config.run.dag_runtime.dag_mode = self.dag_mode
        config.run.dag_runtime.max_inflight_nodes = self.max_inflight_nodes
        config.run.dag_runtime.node_timeout_seconds = self.dag_node_timeout_seconds
        config.run.dag_runtime.ready_queue_policy = self.ready_queue_policy
        config.run.dag_runtime.llm_global_max_concurrency = self.llm_global_max_concurrency
        config.run.dag_runtime.llm_model_quotas = self.llm_model_quotas
        config.run.dag_runtime.max_retries = self.dag_max_retries
        config.run.dag_runtime.enable_debug_branch = self.enable_debug_branch
        config.run.dag_runtime.dag_actor_strategy = self.dag_actor_strategy
        config.run.dag_runtime.runtime_engine = self.dag_runtime_engine
        config.run.dag_runtime.parallel_drafts = self.dag_parallel_drafts
        config.run.dag_runtime.branch_budget = self.dag_branch_budget
        config.run.dag_runtime.node_timeout_policy = self.dag_node_timeout_policy
        config.run.dag_runtime.node_timeout_by_op = dict(self.dag_node_timeout_by_op or {})
        if self.llm_max_concurrent_per_key is not None:
            config.llm.max_concurrent_per_key = max(1, int(self.llm_max_concurrent_per_key))

    def apply_sandbox_to_config(self, config):
        """Apply sandbox backend settings to DSLightingConfig."""
        config.sandbox.backend = self.sandbox_backend
        config.sandbox.backend_type = self.sandbox_backend_type
        config.sandbox.api_key = self.sandbox_api_key
