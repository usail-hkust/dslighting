"""
Configuration building and management.

This module handles merging of default configurations, environment variables,
and user parameters to create the final DSLightingConfig. It also provides
configuration version management and migration support.
"""

import logging
import os
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from typing_extensions import ClassVar

from dslighting.config import (
    DSLightingConfig,
    AgentRuntimeConfig,
    DataAnalysisConfig,
    LLMConfig,
    OutputContractConfig,
    RunConfig,
    WorkflowConfig,
    AgentConfig,
    SandboxConfig,
    SchedulerConfig,
)
from dslighting.error import ConfigurationError

from dslighting.utils.defaults import (
    DEFAULT_CONFIG,
    DEFAULT_WORKSPACE_DIR,
    ENV_DSLIGHTING_DEFAULT_WORKFLOW,
    ENV_DSLIGHTING_WORKSPACE_DIR,
)
from dslighting.core.config.llm_resolution import build_llm_config
from dslighting.core.visualization_policy import (
    VISUALIZATION_POLICY_KEY,
    coerce_visualization_policy,
    consume_visualization_policy,
)
from dslighting.core.config.runtime_params import (
    LEGACY_REACT_RUNTIME_KEYS,
    normalize_agent_runtime_params,
    normalize_output_contract_params,
)

# Import shared config utilities
from dslighting.core.config.shared import (
    VALID_WORKFLOW_NAMES,
    WORKFLOW_TO_CONFIG_KEY,
    deep_merge,
    is_valid_workflow_name,
    get_config_key_for_workflow,
)

from .versioning import (
    ConfigVersionManager,
    get_version_manager,
    detect_config_version,
    migrate_config,
    is_config_compatible,
)

logger = logging.getLogger(__name__)


class ConfigBuilder:
    """
    Build DSLightingConfig by merging defaults, environment variables, and user parameters.

    Priority order (highest to lowest):
    1. User parameters (function arguments)
    2. Environment variables
    3. Default configuration

    Attributes:
        VALID_WORKFLOW_NAMES: Set of valid workflow names (imported from shared).
        WORKFLOW_TO_CONFIG_KEY: Mapping of workflow names to config keys (imported from shared).
    """

    # Valid workflow names constant (imported from shared module)
    VALID_WORKFLOW_NAMES: ClassVar[frozenset[str]] = VALID_WORKFLOW_NAMES

    # Workflow to config key mapping (imported from shared module)
    WORKFLOW_TO_CONFIG_KEY: ClassVar[Dict[str, str]] = WORKFLOW_TO_CONFIG_KEY
    _LEGACY_REACT_PARAM_KEYS: ClassVar[frozenset[str]] = LEGACY_REACT_RUNTIME_KEYS

    def build_config(
        self,
        workflow: str = None,
        model: str = None,
        api_key: Union[str, List[str], None] = None,
        api_keys: Optional[List[str]] = None,
        api_base: str = None,
        provider: str = None,
        temperature: float = None,
        data_analysis: Optional[Dict[str, Any]] = None,
        agent_runtime: Optional[Dict[str, Any]] = None,
        output_contract: Optional[Dict[str, Any]] = None,
        max_iterations: int = None,
        num_drafts: int = None,
        workspace_dir: str = None,
        run_name: str = None,
        keep_workspace: bool = None,
        keep_workspace_on_failure: bool = None,
        visualization_policy: Optional[str] = None,
        **kwargs,
    ) -> DSLightingConfig:
        """
        Build DSLightingConfig by merging all configuration sources.

        Args:
            workflow: Workflow name (aide, autokaggle, etc.)
            model: LLM model name
            api_key: API key for LLM
            api_base: API base URL
            provider: LLM provider (for LiteLLM)
            temperature: LLM temperature
            data_analysis: Shared data analysis settings
            agent_runtime: Shared agent runtime settings
            output_contract: Shared output artifact contract settings
            max_iterations: Maximum agent iterations
            num_drafts: Number of drafts to generate
            workspace_dir: Workspace directory
            run_name: Name for this run
            keep_workspace: Keep workspace after completion
            keep_workspace_on_failure: Keep workspace on failure
            **kwargs: Additional parameters

        Returns:
            DSLightingConfig with all configurations merged
        """
        # 1. Start with defaults
        config = DEFAULT_CONFIG.copy()

        # 2. Load non-LLM environment overrides
        env_config = self._load_non_llm_env_config()
        config = self._deep_merge(config, env_config)

        # 3. Apply user parameters
        user_config = self._build_user_config(
            workflow=workflow,
            model=model,
            api_key=api_key,
            api_keys=api_keys,
            api_base=api_base,
            provider=provider,
            temperature=temperature,
            data_analysis=data_analysis,
            agent_runtime=agent_runtime,
            output_contract=output_contract,
            max_iterations=max_iterations,
            num_drafts=num_drafts,
            workspace_dir=workspace_dir,
            run_name=run_name,
            keep_workspace=keep_workspace,
            keep_workspace_on_failure=keep_workspace_on_failure,
            visualization_policy=visualization_policy,
            **kwargs,
        )
        config = self._deep_merge(config, user_config)

        llm_config = build_llm_config(
            model=model,
            api_key=api_key,
            api_keys=api_keys,
            api_base=api_base,
            provider=provider,
            temperature=temperature,
        )

        # 5. Convert to DSLightingConfig objects
        return self._create_dslighting_config(config, llm_config=llm_config)

    def _load_non_llm_env_config(self) -> Dict[str, Any]:
        """Load non-LLM configuration from environment variables."""
        config = {}

        # DSLighting settings
        if os.getenv(ENV_DSLIGHTING_DEFAULT_WORKFLOW):
            config.setdefault("workflow", {})["name"] = os.getenv(ENV_DSLIGHTING_DEFAULT_WORKFLOW)

        if os.getenv(ENV_DSLIGHTING_WORKSPACE_DIR):
            config.setdefault("run", {}).setdefault("parameters", {})["workspace_dir"] = os.getenv(
                ENV_DSLIGHTING_WORKSPACE_DIR
            )

        return config

    def _build_user_config(
        self,
        workflow: str = None,
        model: str = None,
        api_key: Union[str, List[str], None] = None,
        api_keys: Optional[List[str]] = None,
        api_base: str = None,
        provider: str = None,
        temperature: float = None,
        data_analysis: Optional[Dict[str, Any]] = None,
        agent_runtime: Optional[Dict[str, Any]] = None,
        output_contract: Optional[Dict[str, Any]] = None,
        max_iterations: int = None,
        num_drafts: int = None,
        workspace_dir: str = None,
        run_name: str = None,
        keep_workspace: bool = None,
        keep_workspace_on_failure: bool = None,
        visualization_policy: Optional[str] = None,
        **kwargs,
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
            if key == "react":
                raise ConfigurationError(
                    "`react` runtime config is no longer supported. Use "
                    "`agent_runtime={...}` for max steps/observation/context settings "
                    "and `output_contract={...}` for output artifact gating.",
                    error_code="CFG-002",
                )
            if key in [
                "aide",
                "autokaggle",
                "data_interpreter",
                "automind",
                "dsagent",
                "deepanalyze",
            ]:
                # Nested dictionary format (v1.9.0+)
                if isinstance(value, dict):
                    workflow_specific_params[key] = value
            else:
                remaining_kwargs[key] = value

        # Process workflow-specific nested parameters
        for wf_name, wf_params in workflow_specific_params.items():
            wf_params = dict(wf_params)
            wf_visualization_policy = consume_visualization_policy(wf_params)
            if wf_visualization_policy is not None:
                config.setdefault("agent", {}).setdefault("visualization", {})[
                    "policy"
                ] = wf_visualization_policy

            if wf_name == "autokaggle":
                # AutoKaggle parameters → agent.autokaggle
                config.setdefault("agent", {})["autokaggle"] = wf_params
            elif wf_name == "aide":
                # AIDE parameters → agent.search
                config.setdefault("agent", {}).setdefault("search", {}).update(wf_params)
            elif wf_name in ["automind", "dsagent"]:
                # AutoMind/DS-Agent parameters → workflow.params
                config.setdefault("workflow", {}).setdefault("params", {}).update(wf_params)
            elif wf_name == "data_interpreter":
                # DataInterpreter parameters → agent.search (for max_iterations)
                config.setdefault("agent", {}).setdefault("search", {}).update(wf_params)
            elif wf_name == "deepanalyze":
                # DeepAnalyze parameters → agent.search
                config.setdefault("agent", {}).setdefault("search", {}).update(wf_params)

        # ========== Common parameters ==========
        if workflow is not None:
            config.setdefault("workflow", {})["name"] = workflow

        if model is not None:
            config.setdefault("llm", {})["model"] = model

        if api_key is not None:
            config.setdefault("llm", {})["api_key"] = api_key

        if api_keys is not None:
            config.setdefault("llm", {})["api_keys"] = api_keys

        if api_base is not None:
            config.setdefault("llm", {})["api_base"] = api_base

        if provider is not None:
            config.setdefault("llm", {})["provider"] = provider

        if temperature is not None:
            config.setdefault("llm", {})["temperature"] = temperature

        if data_analysis is not None:
            if not isinstance(data_analysis, dict):
                raise ConfigurationError(
                    "`data_analysis` must be a dictionary matching DataAnalysisConfig",
                    error_code="CFG-002",
                )
            config.setdefault("data_analysis", {}).update(data_analysis)

        if agent_runtime is not None:
            try:
                config.setdefault("agent_runtime", {}).update(
                    normalize_agent_runtime_params(agent_runtime)
                )
            except (TypeError, ValueError) as exc:
                raise ConfigurationError(str(exc), error_code="CFG-002") from None

        if output_contract is not None:
            try:
                config.setdefault("output_contract", {}).update(
                    normalize_output_contract_params(output_contract)
                )
            except (TypeError, ValueError) as exc:
                raise ConfigurationError(str(exc), error_code="CFG-002") from None

        if max_iterations is not None:
            config.setdefault("agent", {}).setdefault("search", {})[
                "max_iterations"
            ] = max_iterations
            config.setdefault("run", {})["total_steps"] = max_iterations

        if num_drafts is not None:
            config.setdefault("agent", {}).setdefault("search", {})["num_drafts"] = num_drafts

        if run_name is not None:
            config.setdefault("run", {})["run_name"] = run_name

        if workspace_dir is not None:
            config.setdefault("workflow", {}).setdefault("params", {})[
                "workspace_base_dir"
            ] = workspace_dir

        if keep_workspace is not None:
            config.setdefault("run", {})["keep_all_workspaces"] = keep_workspace

        if keep_workspace_on_failure is not None:
            config.setdefault("run", {})["keep_workspace_on_failure"] = keep_workspace_on_failure

        if visualization_policy is not None:
            config.setdefault("agent", {}).setdefault("visualization", {})["policy"] = (
                coerce_visualization_policy(visualization_policy)
            )

        flat_visualization_policy = consume_visualization_policy(remaining_kwargs)
        if flat_visualization_policy is not None:
            config.setdefault("agent", {}).setdefault("visualization", {})[
                "policy"
            ] = flat_visualization_policy

        if workflow == "react":
            self._reject_legacy_react_flat_kwargs(remaining_kwargs)

        # Warn about unused kwargs (legacy flat parameter format no longer supported)
        if remaining_kwargs:
            logger.warning(
                f"Unknown configuration parameters (legacy flat format not supported): "
                f"{list(remaining_kwargs.keys())}. Please use nested config format instead "
                f"(e.g., agent={{'autokaggle': {{'max_attempts_per_phase': 10}}}})."
            )

        return config

    def _create_dslighting_config(
        self,
        config_dict: Dict[str, Any],
        *,
        llm_config: Optional[LLMConfig] = None,
    ) -> DSLightingConfig:
        """Convert configuration dict to DSLightingConfig object."""
        if llm_config is None:
            # Extract LLM config
            llm_dict = config_dict.get("llm", {}).copy()

            # If both api_key and api_keys exist, prefer api_keys (key pool takes priority)
            if "api_keys" in llm_dict and "api_key" in llm_dict:
                logger.debug(
                    "Both api_key and api_keys present. Removing api_key in favor of api_keys for key rotation."
                )
                del llm_dict["api_key"]

            llm_config = LLMConfig(**llm_dict)

        # Extract workflow config
        workflow_dict = config_dict.get("workflow", {})
        workflow_config = WorkflowConfig(**workflow_dict)

        # Extract run config
        run_dict = config_dict.get("run", {})
        run_config = RunConfig(**run_dict)

        # Extract agent config
        agent_dict = config_dict.get("agent", {})
        if isinstance(agent_dict, dict):
            agent_dict = dict(agent_dict)
            visualization_dict = dict(agent_dict.get("visualization") or {})
            if "policy" not in visualization_dict:
                search_dict = agent_dict.get("search")
                autokaggle_dict = agent_dict.get("autokaggle")
                legacy_value = None
                if isinstance(search_dict, dict) and "enforce_no_plotting" in search_dict:
                    legacy_value = search_dict.pop("enforce_no_plotting")
                if isinstance(autokaggle_dict, dict) and "enforce_no_plotting" in autokaggle_dict:
                    legacy_value = autokaggle_dict.pop("enforce_no_plotting")
                if legacy_value is not None:
                    visualization_dict["policy"] = "no_display" if legacy_value else "allow"
            if visualization_dict:
                agent_dict["visualization"] = visualization_dict
        agent_config = AgentConfig(**agent_dict)

        # Extract sandbox config
        sandbox_dict = config_dict.get("sandbox", {})
        sandbox_config = SandboxConfig(**sandbox_dict)

        # Extract data-analysis config
        data_analysis_dict = config_dict.get("data_analysis", {})
        data_analysis_config = DataAnalysisConfig(**data_analysis_dict)

        # Extract shared agent runtime config
        agent_runtime_dict = config_dict.get("agent_runtime", {})
        agent_runtime_config = AgentRuntimeConfig(**agent_runtime_dict)

        # Extract shared output contract config
        output_contract_dict = config_dict.get("output_contract", {})
        output_contract_config = OutputContractConfig(**output_contract_dict)

        # Extract scheduler config
        scheduler_dict = config_dict.get("scheduler", {})
        scheduler_config = SchedulerConfig(**scheduler_dict)

        # Create DSLightingConfig
        return DSLightingConfig(
            llm=llm_config,
            workflow=workflow_config,
            run=run_config,
            agent=agent_config,
            sandbox=sandbox_config,
            data_analysis=data_analysis_config,
            agent_runtime=agent_runtime_config,
            output_contract=output_contract_config,
            scheduler=scheduler_config,
        )

    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        """
        Deep merge two dictionaries.

        Uses the shared deep_merge function from dslighting.core.config.shared.

        Args:
            base: Base dictionary
            update: Dictionary with updates (higher priority)

        Returns:
            Merged dictionary
        """
        return deep_merge(base, update)

    def _reject_legacy_react_flat_kwargs(self, remaining_kwargs: Dict[str, Any]) -> None:
        invalid_flat = sorted(
            key for key in self._LEGACY_REACT_PARAM_KEYS if key in remaining_kwargs
        )
        if invalid_flat:
            raise ConfigurationError(
                "Legacy ReAct runtime parameters are no longer supported. "
                "Use `agent_runtime={...}` with nested `observation` and `context` settings. "
                f"Invalid flat keys: {invalid_flat}",
                error_code="CFG-002",
            )

        if "react" in remaining_kwargs:
            raise ConfigurationError(
                "`react` runtime config is no longer supported. Use `agent_runtime={...}`.",
                error_code="CFG-002",
            )

    def _validate_config_dict(self, config_dict: Dict[str, Any]) -> None:
        """Validate configuration dictionary structure and types.

        Args:
            config_dict: Configuration dictionary to validate.

        Raises:
            ConfigurationError: If configuration is invalid.
        """
        if not isinstance(config_dict, dict):
            raise ConfigurationError(
                "Configuration must be a dictionary",
                error_code="CFG-001",
                suggestion="Ensure the configuration is passed as a valid dictionary object",
            )

        # Validate workflow name
        workflow_name = config_dict.get("workflow", {}).get("name")
        if workflow_name is not None:
            if not is_valid_workflow_name(workflow_name):
                raise ConfigurationError(
                    f"Invalid workflow name: '{workflow_name}'. "
                    f"Must be one of: {', '.join(sorted(VALID_WORKFLOW_NAMES))}",
                    error_code="CFG-002",
                    details={
                        "workflow_name": workflow_name,
                        "valid_workflows": list(VALID_WORKFLOW_NAMES),
                    },
                    suggestion=f"Use one of the valid workflow names: {', '.join(sorted(VALID_WORKFLOW_NAMES))}",
                )
            if workflow_name == "react":
                workflow_params = config_dict.get("workflow", {}).get("params", {}) or {}
                run_parameters = config_dict.get("run", {}).get("parameters", {}) or {}
                if not isinstance(workflow_params, dict):
                    raise ConfigurationError(
                        "`workflow.params` must be a dictionary for workflow='react'",
                        error_code="CFG-002",
                    )

                allowed_keys = {"workspace_base_dir"}
                unknown = sorted(key for key in workflow_params if key not in allowed_keys)
                if unknown:
                    raise ConfigurationError(
                        f"Unknown workflow.params keys for workflow='react': {unknown}. "
                        "Runtime settings must use `agent_runtime={...}`.",
                        error_code="CFG-002",
                    )

                invalid_run_keys = []
                if "react" in run_parameters:
                    invalid_run_keys.append("run.parameters.react")
                invalid_run_keys.extend(
                    f"run.parameters.{key}"
                    for key in self._LEGACY_REACT_PARAM_KEYS
                    if key in run_parameters
                )
                if invalid_run_keys:
                    raise ConfigurationError(
                        "Legacy ReAct runtime parameter paths are no longer supported. "
                        "Use `agent_runtime` instead. "
                        f"Invalid keys: {sorted(invalid_run_keys)}",
                        error_code="CFG-002",
                    )

        agent_runtime_config = config_dict.get("agent_runtime")
        if agent_runtime_config is not None:
            try:
                normalize_agent_runtime_params(agent_runtime_config)
            except (TypeError, ValueError) as exc:
                raise ConfigurationError(str(exc), error_code="CFG-002") from None

        output_contract_config = config_dict.get("output_contract")
        if output_contract_config is not None:
            try:
                normalize_output_contract_params(output_contract_config)
            except (TypeError, ValueError) as exc:
                raise ConfigurationError(str(exc), error_code="CFG-002") from None

        # Validate LLM config mutual exclusion
        llm_config = config_dict.get("llm", {})
        if isinstance(llm_config, dict):
            if "api_key" in llm_config and "api_keys" in llm_config:
                raise ConfigurationError(
                    "Only one of 'api_key' or 'api_keys' can be set, not both",
                    error_code="CFG-003",
                    details={
                        "has_api_key": "api_key" in llm_config,
                        "has_api_keys": "api_keys" in llm_config,
                    },
                    suggestion="Remove either 'api_key' or 'api_keys' from the LLM configuration",
                )

    def _coerce_types(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Coerce string values to correct types.

        Handles type coercion for configuration values that may be passed
        as strings from environment variables or CLI arguments.

        Args:
            config_dict: Configuration dictionary to coerce.

        Returns:
            Dictionary with types coerced where applicable.

        Examples:
            - "true"/"false" -> bool
            - "128" -> int
            - "0.5" -> float
        """

        def _coerce_bool(value: Any) -> bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            normalized = str(value).strip().lower()
            if normalized in {"1", "true", "t", "yes", "y", "on"}:
                return True
            if normalized in {"0", "false", "f", "no", "n", "off"}:
                return False
            raise ValueError(f"Unsupported boolean literal: {value}")

        type_mappings: Dict[str, Tuple[Callable[[Any], Any], str]] = {
            "temperature": (float, "temperature"),
            "max_iterations": (int, "max_iterations"),
            "num_drafts": (int, "num_drafts"),
            "max_retries": (int, "max_retries"),
            "max_concurrent_per_key": (int, "max_concurrent_per_key"),
            "timeout": (int, "timeout"),
            "success_threshold": (float, "success_threshold"),
            "debug_prob": (float, "debug_prob"),
            "max_debug_depth": (int, "max_debug_depth"),
            "max_attempts_per_phase": (int, "max_attempts_per_phase"),
            "max_steps": (int, "max_steps"),
            "max_tokens": (int, "max_tokens"),
            "head_tokens": (int, "head_tokens"),
            "tail_tokens": (int, "tail_tokens"),
            "max_chars": (int, "max_chars"),
            "max_history_chars": (int, "max_history_chars"),
            "keep_recent_turns": (int, "keep_recent_turns"),
            "max_observation_chars": (int, "max_observation_chars"),
            "summary_trigger_turns": (int, "summary_trigger_turns"),
            "summary_max_chars": (int, "summary_max_chars"),
            "recent_observation_window": (int, "recent_observation_window"),
            "max_feedback_chars": (int, "max_feedback_chars"),
            "max_feedback_retries": (int, "max_feedback_retries"),
            "keep_latest_feedback_only": (_coerce_bool, "keep_latest_feedback_only"),
            "enforce_no_plotting": (_coerce_bool, "enforce_no_plotting"),
            VISUALIZATION_POLICY_KEY: (coerce_visualization_policy, VISUALIZATION_POLICY_KEY),
            "enabled": (_coerce_bool, "enabled"),
            "cache_enabled": (_coerce_bool, "cache_enabled"),
            "cache_max_entries": (int, "cache_max_entries"),
            "cache_debug_metrics": (_coerce_bool, "cache_debug_metrics"),
            "require_output_before_completion": (_coerce_bool, "require_output_before_completion"),
            "missing_output_feedback_retries": (int, "missing_output_feedback_retries"),
            "max_preview_rows": (int, "max_preview_rows"),
            "max_candidate_files": (int, "max_candidate_files"),
            "allow_runner_fallback": (_coerce_bool, "allow_runner_fallback"),
        }

        coerced = config_dict.copy()

        sections: List[Dict[str, Any]] = []

        llm_config = coerced.get("llm", {})
        if isinstance(llm_config, dict):
            sections.append(llm_config)

        agent_config = coerced.get("agent", {})
        if isinstance(agent_config, dict):
            search_config = agent_config.get("search", {})
            autokaggle_config = agent_config.get("autokaggle", {})
            visualization_config = agent_config.get("visualization", {})
            if isinstance(search_config, dict):
                sections.append(search_config)
            if isinstance(autokaggle_config, dict):
                sections.append(autokaggle_config)
            if isinstance(visualization_config, dict):
                sections.append(visualization_config)

        data_analysis_config = coerced.get("data_analysis", {})
        if isinstance(data_analysis_config, dict):
            sections.append(data_analysis_config)

        agent_runtime_config = coerced.get("agent_runtime", {})
        if isinstance(agent_runtime_config, dict):
            sections.append(agent_runtime_config)
            observation_config = agent_runtime_config.get("observation", {})
            context_config = agent_runtime_config.get("context", {})
            if isinstance(observation_config, dict):
                sections.append(observation_config)
            if isinstance(context_config, dict):
                sections.append(context_config)

        output_contract_config = coerced.get("output_contract", {})
        if isinstance(output_contract_config, dict):
            sections.append(output_contract_config)

        for section in sections:
            for key, (coercer, _) in type_mappings.items():
                if key in section and isinstance(section[key], str):
                    try:
                        section[key] = coercer(section[key])
                    except (ValueError, TypeError):
                        logger.warning(
                            f"Cannot coerce '{key}' to expected type, keeping original value"
                        )

        return coerced

    # =====================================================================
    # Version Migration Methods
    # =====================================================================

    @property
    def version_manager(self) -> ConfigVersionManager:
        """Get the configuration version manager."""
        if not hasattr(self, "_version_manager"):
            self._version_manager = get_version_manager()
        return self._version_manager

    def load_config_from_dict(
        self,
        config_dict: Dict[str, Any],
        *,
        skip_migration: bool = False,
    ) -> DSLightingConfig:
        """
        Load configuration from a dictionary with version migration support.

        This method handles:
        1. Version detection
        2. Configuration migration (if needed)
        3. Type coercion
        4. Validation
        5. Conversion to DSLightingConfig objects

        Args:
            config_dict: Configuration dictionary to load.
            skip_migration: If True, skip migration (useful for testing).

        Returns:
            DSLightingConfig object with migrated configuration.

        Raises:
            ConfigurationError: If configuration is invalid or migration fails.

        Examples:
            >>> # Load legacy config (will be auto-migrated)
            >>> legacy = {"model": "gpt-4", "temperature": 0.7}
            >>> config = builder.load_config_from_dict(legacy)
            >>> config.llm.model
            'gpt-4'
        """
        try:
            # 1. Detect version
            version = detect_config_version(config_dict)
            logger.debug(f"Detected config version: {version}")

            # 2. Migrate if needed
            if not skip_migration and version != self.version_manager.VERSION:
                logger.info(
                    f"Migrating config from version {version} to " f"{self.version_manager.VERSION}"
                )
                config_dict = migrate_config(config_dict)
                logger.info("Config migration completed successfully")

            # 3. Apply type coercion
            config_dict = self._coerce_types(config_dict)

            # 4. Validate
            self._validate_config_dict(config_dict)

            # 5. Convert to DSLightingConfig
            return self._create_dslighting_config(config_dict)

        except Exception as exc:
            logger.error(f"Failed to load configuration: {exc}")
            raise ConfigurationError(f"Configuration error: {exc}") from exc

    def load_config_from_file(
        self,
        file_path: str,
        *,
        file_format: str = "auto",
        skip_migration: bool = False,
    ) -> DSLightingConfig:
        """
        Load configuration from a file with version migration support.

        Supports YAML, JSON, and TOML formats (auto-detected by default).

        Args:
            file_path: Path to the configuration file.
            file_format: Explicit format specification ("yaml", "json", "toml")
                        or "auto" for automatic detection.
            skip_migration: If True, skip migration.

        Returns:
            DSLightingConfig object with migrated configuration.

        Raises:
            ConfigurationError: If file cannot be read or parsed.

        Examples:
            >>> # Auto-detect format from file extension
            >>> config = builder.load_config_from_file("config.yaml")

            >>> # Explicit JSON format
            >>> config = builder.load_config_from_file("config.json", file_format="json")
        """
        import os

        if not os.path.exists(file_path):
            raise ConfigurationError(f"Config file not found: {file_path}")

        # Determine format if auto
        if file_format == "auto":
            ext = os.path.splitext(file_path)[1].lower()
            if ext in (".yaml", ".yml"):
                file_format = "yaml"
            elif ext == ".json":
                file_format = "json"
            elif ext in (".toml",):
                file_format = "toml"
            else:
                raise ConfigurationError(
                    f"Cannot auto-detect format for extension '{ext}'. "
                    f"Please specify format explicitly."
                )

        # Parse file content
        try:
            if file_format == "yaml":
                import yaml

                with open(file_path, "r", encoding="utf-8") as f:
                    config_dict = yaml.safe_load(f) or {}
            elif file_format == "json":
                with open(file_path, "r", encoding="utf-8") as f:
                    import json

                    config_dict = json.load(f)
            elif file_format == "toml":
                import toml

                with open(file_path, "r", encoding="utf-8") as f:
                    config_dict = toml.load(f)
            else:
                raise ConfigurationError(f"Unsupported format: {file_format}")
        except Exception as exc:
            logger.error(f"Failed to parse config file: {exc}")
            raise ConfigurationError(f"Config file parse error: {exc}") from exc

        logger.info(f"Loaded configuration from {file_path}")
        return self.load_config_from_dict(config_dict, skip_migration=skip_migration)

    def validate_config_compatibility(
        self,
        config: Dict[str, Any],
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate configuration compatibility with current version.

        Args:
            config: Configuration dictionary to validate.

        Returns:
            Tuple of (is_compatible: bool, message: Optional[str]).
            If not compatible, message contains the reason.
        """
        if is_config_compatible(config):
            version = detect_config_version(config)
            if version != self.version_manager.VERSION:
                return (
                    False,
                    f"Config version '{version}' is not current. "
                    f"Run `migrate_config()` to upgrade to "
                    f"version '{self.version_manager.VERSION}'.",
                )
            return True, None

        version = detect_config_version(config)
        return (
            False,
            f"Config version '{version}' is no longer supported. "
            f"Please migrate to a newer version.",
        )

    def get_config_version_info(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed version information for a configuration.

        Args:
            config: Configuration dictionary.

        Returns:
            Dictionary with version information including:
            - current_version: Detected version
            - target_version: Current manager version
            - needs_migration: Whether migration is needed
            - is_compatible: Whether config is compatible
            - migration_history: List of past migrations
        """
        current_version = detect_config_version(config)
        target_version = self.version_manager.VERSION

        return {
            "current_version": current_version,
            "target_version": target_version,
            "needs_migration": current_version != target_version,
            "is_compatible": is_config_compatible(config),
            "migration_history": config.get("_migration_history", []),
        }
