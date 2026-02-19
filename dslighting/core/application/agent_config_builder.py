"""Build DSLightingConfig for Agent facade runs."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dslighting.config import DSLightingConfig, LLMConfig, RunConfig, SandboxConfig, WorkflowConfig


class AgentConfigBuilder:
    """Map Agent inputs/kwargs into a normalized DSLightingConfig."""

    def __init__(
        self,
        *,
        workflow_name: str,
        model: str,
        api_key: Optional[str],
        api_base: Optional[str],
        provider: Optional[str],
        temperature: Optional[float],
        timeout: int,
        keep_workspace: bool,
        init_kwargs: Dict[str, Any],
    ) -> None:
        self.workflow_name = workflow_name
        self.model = model
        self.api_key = api_key
        self.api_base = api_base
        self.provider = provider
        self.temperature = temperature
        self.timeout = timeout
        self.keep_workspace = keep_workspace
        self.init_kwargs = dict(init_kwargs)

    def build(self, *, task_id: str, run_kwargs: Dict[str, Any]) -> DSLightingConfig:
        llm_kwargs: Dict[str, Any] = {"model": self.model}
        if self.api_key is not None:
            llm_kwargs["api_key"] = self.api_key
        if self.api_base is not None:
            llm_kwargs["api_base"] = self.api_base
        if self.provider is not None:
            llm_kwargs["provider"] = self.provider
        if self.temperature is not None:
            llm_kwargs["temperature"] = self.temperature

        config = DSLightingConfig(
            run=RunConfig(
                name=f"agent_{self.workflow_name}_{task_id}",
                keep_all_workspaces=self.keep_workspace,
                keep_workspace_on_failure=self.keep_workspace,
            ),
            workflow=WorkflowConfig(name=self.workflow_name, params={}),
            llm=LLMConfig(**llm_kwargs),
            sandbox=SandboxConfig(timeout=self.timeout),
        )

        # Keep legacy precedence: call-time kwargs override init-time kwargs.
        merged = {**self.init_kwargs, **run_kwargs}

        search_keys = {"num_drafts", "debug_prob", "max_iterations", "max_debug_depth"}
        if self.workflow_name != "autokaggle":
            search_keys.add("enforce_no_plotting")
        for key in search_keys:
            if key in merged:
                setattr(config.agent.search, key, merged.pop(key))

        autokaggle_keys = {"max_attempts_per_phase", "success_threshold"}
        if self.workflow_name == "autokaggle":
            autokaggle_keys.add("enforce_no_plotting")
        for key in autokaggle_keys:
            if key in merged:
                setattr(config.agent.autokaggle, key, merged.pop(key))

        if merged:
            config.run.parameters.update(merged)

        return config

