# dslighting/config.py

from typing import Dict, Any, Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator


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

    name: str = "dslighting_run"
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


class AgentSearchConfig(BaseModel):
    """Parameters for Paradigm 2 (AIDE/AutoMind) search."""

    num_drafts: int = 5
    debug_prob: float = 0.8
    max_iterations: int = 5
    max_debug_depth: int = 10
    # Shared policy knob exposed to all agent configs; currently enforced in AutoKaggle.
    enforce_no_plotting: bool = True


class AutoKaggleConfig(BaseModel):
    """Parameters for the AutoKaggle SOP workflow."""

    max_attempts_per_phase: int = 10
    success_threshold: float = 3.0
    enforce_no_plotting: bool = True


class AgentConfig(BaseModel):
    """Configuration for a specific agent's behavior."""

    search: AgentSearchConfig = Field(default_factory=AgentSearchConfig)
    max_retries: int = 10
    autokaggle: AutoKaggleConfig = Field(default_factory=AutoKaggleConfig)


class OptimizerConfig(BaseModel):
    """Parameters for Paradigm 3 (AFlow) meta-optimization."""

    max_rounds: int = 10
    validation_runs_per_candidate: int = 1
    top_k_selection: int = 2


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

    # Paradigm-specific configurations
    workflow: Optional[WorkflowConfig] = None
    agent: AgentConfig = Field(default_factory=AgentConfig)
    optimizer: Optional[OptimizerConfig] = None

    model_config = ConfigDict(
        extra="forbid"  # Pydantic configuration
    )
