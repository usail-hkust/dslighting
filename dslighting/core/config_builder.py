"""
Configuration building and management.

This module handles merging of default configurations, environment variables,
and user parameters to create the final DSATConfig.
"""

import json
import logging
import os
from typing import Any, Dict, Optional

from dsat.config import (
    DSATConfig,
    LLMConfig,
    RunConfig,
    WorkflowConfig,
    AgentConfig,
    SandboxConfig,
)

from dslighting.utils.defaults import (
    DEFAULT_CONFIG,
    DEFAULT_WORKSPACE_DIR,
    ENV_API_KEY,
    ENV_API_BASE,
    ENV_LLM_MODEL,
    ENV_LLM_PROVIDER,
    ENV_LLM_MODEL_CONFIGS,
    ENV_LLM_TEMPERATURE,
    ENV_DSLIGHTING_DEFAULT_WORKFLOW,
    ENV_DSLIGHTING_WORKSPACE_DIR,
)

logger = logging.getLogger(__name__)


class ConfigBuilder:
    """
    Build DSATConfig by merging defaults, environment variables, and user parameters.

    Priority order (highest to lowest):
    1. User parameters (function arguments)
    2. Environment variables
    3. Default configuration
    """

    def __init__(self):
        self.logger = logger

    def build_config(
        self,
        workflow: str = None,
        model: str = None,
        api_key: str = None,
        api_base: str = None,
        provider: str = None,
        temperature: float = None,
        max_iterations: int = None,
        num_drafts: int = None,
        workspace_dir: str = None,
        run_name: str = None,
        keep_workspace: bool = None,
        keep_workspace_on_failure: bool = None,
        **kwargs
    ) -> DSATConfig:
        """
        Build DSATConfig by merging all configuration sources.

        Args:
            workflow: Workflow name (aide, autokaggle, etc.)
            model: LLM model name
            api_key: API key for LLM
            api_base: API base URL
            provider: LLM provider (for LiteLLM)
            temperature: LLM temperature
            max_iterations: Maximum agent iterations
            num_drafts: Number of drafts to generate
            workspace_dir: Workspace directory
            run_name: Name for this run
            keep_workspace: Keep workspace after completion
            keep_workspace_on_failure: Keep workspace on failure
            **kwargs: Additional parameters

        Returns:
            DSATConfig with all configurations merged
        """
        # 1. Start with defaults
        config = DEFAULT_CONFIG.copy()

        # 2. Load environment overrides
        env_config = self._load_env_config()
        config = self._deep_merge(config, env_config)

        # 3. Apply user parameters
        user_config = self._build_user_config(
            workflow=workflow,
            model=model,
            api_key=api_key,
            api_base=api_base,
            provider=provider,
            temperature=temperature,
            max_iterations=max_iterations,
            num_drafts=num_drafts,
            workspace_dir=workspace_dir,
            run_name=run_name,
            keep_workspace=keep_workspace,
            keep_workspace_on_failure=keep_workspace_on_failure,
            **kwargs
        )
        config = self._deep_merge(config, user_config)

        # 4. Load model-specific configs if any
        model_name = config.get("llm", {}).get("model")
        if model_name:
            model_configs = self._load_model_configs()
            if model_name in model_configs:
                model_override = model_configs[model_name]
                # Model configs have lower priority than direct user params
                config["llm"] = self._deep_merge(config["llm"], model_override)

        # 5. Convert to DSATConfig objects
        return self._create_dsat_config(config)

    def _load_env_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}

        # LLM settings
        if os.getenv(ENV_API_KEY):
            config.setdefault("llm", {})["api_key"] = os.getenv(ENV_API_KEY)

        if os.getenv(ENV_API_BASE):
            config.setdefault("llm", {})["api_base"] = os.getenv(ENV_API_BASE)

        if os.getenv(ENV_LLM_MODEL):
            config.setdefault("llm", {})["model"] = os.getenv(ENV_LLM_MODEL)

        if os.getenv(ENV_LLM_PROVIDER):
            config.setdefault("llm", {})["provider"] = os.getenv(ENV_LLM_PROVIDER)

        if os.getenv(ENV_LLM_TEMPERATURE):
            try:
                temp = float(os.getenv(ENV_LLM_TEMPERATURE))
                config.setdefault("llm", {})["temperature"] = temp
            except ValueError:
                logger.warning(f"Invalid {ENV_LLM_TEMPERATURE} value")

        # DSLighting settings
        if os.getenv(ENV_DSLIGHTING_DEFAULT_WORKFLOW):
            config.setdefault("workflow", {})["name"] = os.getenv(
                ENV_DSLIGHTING_DEFAULT_WORKFLOW
            )

        if os.getenv(ENV_DSLIGHTING_WORKSPACE_DIR):
            config.setdefault("run", {}).setdefault("parameters", {})["workspace_dir"] = \
                os.getenv(ENV_DSLIGHTING_WORKSPACE_DIR)

        return config

    def _load_model_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Load per-model overrides from LLM_MODEL_CONFIGS env var.

        Expected format (JSON object):
          {
            "<model_name>": {
              "api_key": "sk-..." | ["sk-1", "sk-2"],
              "api_base": "https://.../v1",
              "provider": "siliconflow",
              "temperature": 0.7
            }
          }
        """
        raw = os.getenv(ENV_LLM_MODEL_CONFIGS)
        if not raw:
            return {}

        try:
            parsed = json.loads(raw)
        except Exception as exc:
            logger.warning(f"Failed to parse LLM_MODEL_CONFIGS as JSON: {exc}")
            return {}

        if not isinstance(parsed, dict):
            logger.warning("LLM_MODEL_CONFIGS must be a JSON object")
            return {}

        # Process each model config
        result = {}
        for k, v in parsed.items():
            if not isinstance(k, str) or not isinstance(v, dict):
                continue

            # Handle api_key as list (take the first one)
            if "api_key" in v and isinstance(v["api_key"], list):
                if len(v["api_key"]) > 0:
                    v = v.copy()  # Shallow copy to avoid mutating original
                    v["api_key"] = v["api_key"][0]
                    logger.debug(f"Model '{k}': using first API key from list of {len(v['api_key'])}")

            result[k] = v

        return result

    def _build_user_config(
        self,
        workflow: str = None,
        model: str = None,
        api_key: str = None,
        api_base: str = None,
        provider: str = None,
        temperature: float = None,
        max_iterations: int = None,
        num_drafts: int = None,
        workspace_dir: str = None,
        run_name: str = None,
        keep_workspace: bool = None,
        keep_workspace_on_failure: bool = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Build user configuration from parameters.

        Supports both:
        1. Nested dictionary format (recommended, v1.9.0+):
           agent = dslighting.Agent(
               workflow="autokaggle",
               autokaggle={"max_attempts_per_phase": 5}
           )

        2. Flat format (backward compatible):
           agent = dslighting.Agent(
               workflow="autokaggle",
               autokaggle_max_attempts_per_phase=5
           )
        """
        config = {}

        # ========== Workflow-specific parameters (nested dict) ==========
        workflow_specific_params = {}
        remaining_kwargs = {}

        for key, value in kwargs.items():
            if key in ['aide', 'autokaggle', 'data_interpreter', 'automind', 'dsagent', 'deepanalyze']:
                # Nested dictionary format (v1.9.0+)
                if isinstance(value, dict):
                    workflow_specific_params[key] = value
            else:
                remaining_kwargs[key] = value

        # Process workflow-specific nested parameters
        for wf_name, wf_params in workflow_specific_params.items():
            if wf_name == 'autokaggle':
                # AutoKaggle parameters → agent.autokaggle
                config.setdefault("agent", {})["autokaggle"] = wf_params
            elif wf_name == 'aide':
                # AIDE parameters → agent.search
                config.setdefault("agent", {}).setdefault("search", {}).update(wf_params)
            elif wf_name in ['automind', 'dsagent']:
                # AutoMind/DS-Agent parameters → workflow.params
                config.setdefault("workflow", {}).setdefault("params", {}).update(wf_params)
            elif wf_name == 'data_interpreter':
                # DataInterpreter parameters → agent.search (for max_iterations)
                config.setdefault("agent", {}).setdefault("search", {}).update(wf_params)
            elif wf_name == 'deepanalyze':
                # DeepAnalyze parameters → agent.search
                config.setdefault("agent", {}).setdefault("search", {}).update(wf_params)

        # ========== Common parameters ==========
        if workflow is not None:
            config.setdefault("workflow", {})["name"] = workflow

        if model is not None:
            config.setdefault("llm", {})["model"] = model

        if api_key is not None:
            config.setdefault("llm", {})["api_key"] = api_key

        if api_base is not None:
            config.setdefault("llm", {})["api_base"] = api_base

        if provider is not None:
            config.setdefault("llm", {})["provider"] = provider

        if temperature is not None:
            config.setdefault("llm", {})["temperature"] = temperature

        if max_iterations is not None:
            config.setdefault("agent", {}).setdefault("search", {})["max_iterations"] = max_iterations
            config.setdefault("run", {})["total_steps"] = max_iterations

        if num_drafts is not None:
            config.setdefault("agent", {}).setdefault("search", {})["num_drafts"] = num_drafts

        if run_name is not None:
            config.setdefault("run", {})["name"] = run_name

        if workspace_dir is not None:
            config.setdefault("workflow", {}).setdefault("params", {})["workspace_base_dir"] = workspace_dir

        if keep_workspace is not None:
            config.setdefault("run", {})["keep_all_workspaces"] = keep_workspace

        if keep_workspace_on_failure is not None:
            config.setdefault("run", {})["keep_workspace_on_failure"] = keep_workspace_on_failure

        # ========== Legacy flat parameters (backward compatible) ==========
        if remaining_kwargs:
            # Handle legacy flat format: autokaggle_max_attempts_per_phase
            for key, value in remaining_kwargs.items():
                if key.startswith('autokaggle_'):
                    param_name = key.replace('autokaggle_', '')
                    config.setdefault("agent", {}).setdefault("autokaggle", {})[param_name] = value
                elif key.startswith('aide_'):
                    param_name = key.replace('aide_', '')
                    config.setdefault("agent", {}).setdefault("search", {})[param_name] = value
                elif key.startswith('automind_'):
                    param_name = key.replace('automind_', '')
                    config.setdefault("workflow", {}).setdefault("params", {})[param_name] = value
                elif key.startswith('dsagent_'):
                    param_name = key.replace('dsagent_', '')
                    config.setdefault("workflow", {}).setdefault("params", {})[param_name] = value
                else:
                    # Other parameters → run.parameters
                    config.setdefault("run", {}).setdefault("parameters", {})[key] = value

        return config

    def _create_dsat_config(self, config_dict: Dict[str, Any]) -> DSATConfig:
        """Convert configuration dict to DSATConfig object."""
        # Extract LLM config
        llm_dict = config_dict.get("llm", {})
        llm_config = LLMConfig(**llm_dict)

        # Extract workflow config
        workflow_dict = config_dict.get("workflow", {})
        workflow_config = WorkflowConfig(**workflow_dict)

        # Extract run config
        run_dict = config_dict.get("run", {})
        run_config = RunConfig(**run_dict)

        # Extract agent config
        agent_dict = config_dict.get("agent", {})
        agent_config = AgentConfig(**agent_dict)

        # Extract sandbox config
        sandbox_dict = config_dict.get("sandbox", {})
        sandbox_config = SandboxConfig(**sandbox_dict)

        # Create DSATConfig
        return DSATConfig(
            llm=llm_config,
            workflow=workflow_config,
            run=run_config,
            agent=agent_config,
            sandbox=sandbox_config,
        )

    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        """
        Deep merge two dictionaries.

        Args:
            base: Base dictionary
            update: Dictionary with updates (higher priority)

        Returns:
            Merged dictionary
        """
        result = base.copy()

        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result
