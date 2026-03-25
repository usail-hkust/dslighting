"""Build DSLightingConfig for Agent facade runs."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Union

from dslighting.config import (
    DSLightingConfig,
    DataAnalysisConfig,
    RunConfig,
    SandboxConfig,
    WorkflowConfig,
)
from dslighting.core.config.llm_resolution import build_llm_config
from dslighting.error import ConfigurationError


class AgentConfigBuilder:
    """Map Agent inputs/kwargs into a normalized DSLightingConfig."""

    def __init__(
        self,
        *,
        workflow_name: str,
        model: str,
        api_key: Optional[Union[str, List[str]]],
        api_keys: Optional[List[str]],
        api_base: Optional[str],
        provider: Optional[str],
        temperature: Optional[float],
        timeout: int,
        keep_workspace: bool,
        sandbox_backend: Optional[str],
        sandbox_backend_type: Optional[str],
        sandbox_timeout: Optional[int],
        sandbox_api_key: Optional[str],
        init_kwargs: Dict[str, Any],
    ) -> None:
        self.workflow_name = workflow_name
        self.model = model
        self.api_key = api_key
        self.api_keys = api_keys
        self.api_base = api_base
        self.provider = provider
        self.temperature = temperature
        self.timeout = timeout
        self.keep_workspace = keep_workspace
        self.sandbox_backend = sandbox_backend
        self.sandbox_backend_type = sandbox_backend_type
        self.sandbox_timeout = sandbox_timeout
        self.sandbox_api_key = sandbox_api_key
        self.init_kwargs = dict(init_kwargs)

    def build(self, *, task_id: str, run_kwargs: Dict[str, Any]) -> DSLightingConfig:
        if self.api_key is not None and self.api_keys is not None:
            raise ConfigurationError(
                "Only one of `api_key` or `api_keys` may be provided.",
                error_code="CFG-002",
            )

        llm_config = build_llm_config(
            model=self.model,
            api_key=self.api_key,
            api_keys=self.api_keys,
            api_base=self.api_base,
            provider=self.provider,
            temperature=self.temperature,
        )

        config = DSLightingConfig(
            run=RunConfig(
                run_name=f"agent_{self.workflow_name}",
                keep_all_workspaces=self.keep_workspace,
                keep_workspace_on_failure=self.keep_workspace,
            ),
            workflow=WorkflowConfig(name=self.workflow_name, params={}),
            llm=llm_config,
            sandbox=SandboxConfig(timeout=self.timeout),
        )

        # Keep legacy precedence: call-time kwargs override init-time kwargs.
        merged = {**self.init_kwargs, **run_kwargs}
        self._apply_data_analysis_overrides(config, merged)
        self._apply_sandbox_overrides(config, merged)

        if self.workflow_name in self._RAG_WORKFLOWS:
            namespaced = merged.pop(self.workflow_name, None)
            if namespaced is not None:
                if not isinstance(namespaced, dict):
                    raise ConfigurationError(
                        f"`{self.workflow_name}` must be a dict when provided",
                        error_code="CFG-002",
                    )
                config.workflow.params.update(namespaced)

            invalid_flat = sorted(key for key in self._RAG_KEYS if key in merged)
            if invalid_flat:
                raise ConfigurationError(
                    "RAG parameters must be passed via workflow namespace, e.g. "
                    f"`{self.workflow_name}={{'enable_rag': True, 'case_dir': './experience_replay'}}`. "
                    f"Invalid flat keys: {invalid_flat}",
                    error_code="CFG-002",
                )

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
    _RAG_WORKFLOWS = {"automind", "dsagent"}
    _RAG_KEYS = {"enable_rag", "case_dir"}
    _VALID_SANDBOX_BACKENDS = {"local", "e2b", "ds_sandbox"}
    _VALID_DS_SANDBOX_BACKEND_TYPES = {"docker", "local"}

    def _apply_data_analysis_overrides(self, config: DSLightingConfig, merged: Dict[str, Any]) -> None:
        raw = merged.pop("data_analysis", None)
        if raw is None:
            return
        if not isinstance(raw, dict):
            raise ConfigurationError(
                "`data_analysis` must be a dict matching DataAnalysisConfig",
                error_code="CFG-002",
            )
        config.data_analysis = DataAnalysisConfig(**raw)

    def _apply_sandbox_overrides(self, config: DSLightingConfig, merged: Dict[str, Any]) -> None:
        backend = merged.pop("sandbox_backend", self.sandbox_backend)
        if backend is None:
            backend = os.getenv("SANDBOX_BACKEND")
        if backend is not None:
            if not isinstance(backend, str):
                raise ConfigurationError(
                    "`sandbox_backend` must be a string",
                    error_code="CFG-002",
                )
            backend = backend.strip()
            if backend not in self._VALID_SANDBOX_BACKENDS:
                raise ConfigurationError(
                    "`sandbox_backend` must be one of: local, e2b, ds_sandbox",
                    error_code="CFG-002",
                )
            config.sandbox.backend = backend

        backend_type = merged.pop("sandbox_backend_type", self.sandbox_backend_type)
        if backend_type is None:
            backend_type = os.getenv("SANDBOX_BACKEND_TYPE")
        if backend_type is not None:
            if not isinstance(backend_type, str):
                raise ConfigurationError(
                    "`sandbox_backend_type` must be a string",
                    error_code="CFG-002",
                )
            backend_type = backend_type.strip()
            if backend_type not in self._VALID_DS_SANDBOX_BACKEND_TYPES:
                raise ConfigurationError(
                    "`sandbox_backend_type` must be one of: docker, local",
                    error_code="CFG-002",
                )
            config.sandbox.backend_type = backend_type

        timeout = merged.pop("sandbox_timeout", self.sandbox_timeout)
        if timeout is None:
            env_timeout = os.getenv("SANDBOX_TIMEOUT")
            if env_timeout is not None and env_timeout.strip():
                timeout = env_timeout.strip()
        if timeout is not None:
            try:
                timeout_int = int(timeout)
            except (TypeError, ValueError):
                raise ConfigurationError(
                    "`sandbox_timeout` must be an integer",
                    error_code="CFG-002",
                ) from None
            if timeout_int <= 0:
                raise ConfigurationError(
                    "`sandbox_timeout` must be > 0",
                    error_code="CFG-002",
                )
            config.sandbox.timeout = timeout_int

        api_key = merged.pop("sandbox_api_key", self.sandbox_api_key)
        if api_key is None:
            api_key = os.getenv("E2B_API_KEY")
        if api_key:
            config.sandbox.api_key = api_key

        if config.sandbox.backend == "ds_sandbox":
            if config.sandbox.backend_type not in self._VALID_DS_SANDBOX_BACKEND_TYPES:
                raise ConfigurationError(
                    "When sandbox_backend=ds_sandbox, sandbox_backend_type must be docker or local",
                    error_code="CFG-002",
                )

        if config.sandbox.backend == "e2b" and not (config.sandbox.api_key or os.getenv("E2B_API_KEY")):
            raise ConfigurationError(
                "sandbox_backend='e2b' requires E2B API key. "
                "Set sandbox_api_key or environment variable E2B_API_KEY.",
                error_code="CFG-002",
            )
