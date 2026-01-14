# dsat/config.py

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class LLMConfig(BaseModel):
    """LLM service settings."""
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    api_key: Optional[str] = Field(None, description="API key, defaults to API_KEY env var if not set.")
    api_base: Optional[str] = "https://api.openai.com/v1"
    provider: Optional[str] = Field(None, description="Optional LiteLLM provider alias, e.g. 'siliconflow'.")
    max_retries: int = 3

class SandboxConfig(BaseModel):
    """Code execution sandbox settings."""
    timeout: int = 6 * 3600

class TaskConfig(BaseModel):
    """Defines the problem to be solved."""
    goal: str = "Solve the given data science task."
    eval_metric: Optional[str] = None
    data_dir: Optional[str] = None

class RunConfig(BaseModel):
    """Settings for a specific execution run."""
    name: str = "dsat_run"
    total_steps: int = 4
    keep_all_workspaces: bool = Field(False, description="If True, do not delete any workspace after execution.")
    keep_workspace_on_failure: bool = Field(True, description="If True, keep the workspace only if the task execution fails.")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary runtime parameters saved for telemetry.")

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

class DSATConfig(BaseModel):
    """The root configuration model for the entire DSAT application."""
    run: RunConfig = Field(default_factory=RunConfig)
    task: TaskConfig = Field(default_factory=TaskConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    
    # Paradigm-specific configurations
    workflow: Optional[WorkflowConfig] = None
    agent: AgentConfig = Field(default_factory=AgentConfig)
    optimizer: Optional[OptimizerConfig] = None

    class Config:
        """Pydantic configuration."""
        extra = 'forbid'
