"""
Configuration management module.

This module provides configuration building, validation, version management,
and file watching with hot reload support.
"""

from .builder import ConfigBuilder
from . import api_key_manager
from . import versioning
from .shared import (
    VALID_WORKFLOW_NAMES,
    WORKFLOW_TO_CONFIG_KEY,
    deep_merge,
    is_valid_workflow_name,
    get_config_key_for_workflow,
    get_workflow_for_benchmark,
    apply_env_overrides,
)
from .runtime_logging import log_resolved_runtime_config
from .llm_roles import (
    ENV_JUDGE_IMAGE_MODEL,
    ENV_JUDGE_MODEL,
    ROLE_IMAGE_JUDGE,
    ROLE_PRIMARY,
    ROLE_TEXT_JUDGE,
    resolve_image_judge_llm_config,
    resolve_llm_config_for_role,
    resolve_primary_llm_config,
    resolve_role_model_name,
    resolve_text_judge_llm_config,
)
from .validation import (
    ConfigValidator,
    ValidationError,
    ValidationResult,
)
from .watch import (
    ConfigWatcher,
    ConfigWatcherManager,
    WatchedFile,
    ReloadEvent,
    FileFormat,
    ReloadMode,
    ConfigWatcherError,
    WatcherNotStartedError,
    InvalidFileError,
    get_watcher_manager,
    watch_config,
)
import importlib

# Import from global.py (global is a Python keyword, so we use importlib)
_global_module = importlib.import_module('.global', package='dslighting.core.config')
global_config = _global_module.global_config
get_global_config = _global_module.get_global_config

APIKeyManager = api_key_manager.APIKeyManager

# Versioning exports
from .versioning import (
    ConfigVersionManager,
    ConfigVersionManagerFactory,
    get_version_manager,
    detect_config_version,
    migrate_config,
    is_config_compatible,
    ConfigVersionError,
    MigrationNotSupportedError,
    InvalidVersionError,
)

__all__ = [
    # Builder
    "ConfigBuilder",
    "ENV_JUDGE_IMAGE_MODEL",
    "ENV_JUDGE_MODEL",
    # Shared utilities
    "ROLE_IMAGE_JUDGE",
    "ROLE_PRIMARY",
    "ROLE_TEXT_JUDGE",
    "VALID_WORKFLOW_NAMES",
    "WORKFLOW_TO_CONFIG_KEY",
    "deep_merge",
    "is_valid_workflow_name",
    "get_config_key_for_workflow",
    "get_workflow_for_benchmark",
    "apply_env_overrides",
    "resolve_image_judge_llm_config",
    "resolve_llm_config_for_role",
    "log_resolved_runtime_config",
    "resolve_primary_llm_config",
    "resolve_role_model_name",
    "resolve_text_judge_llm_config",
    # Validation
    "ConfigValidator",
    "ValidationError",
    "ValidationResult",
    # Global config
    "global_config",
    "get_global_config",
    # API Key Manager
    "APIKeyManager",
    # Versioning
    "ConfigVersionManager",
    "ConfigVersionManagerFactory",
    "get_version_manager",
    "detect_config_version",
    "migrate_config",
    "is_config_compatible",
    "ConfigVersionError",
    "MigrationNotSupportedError",
    "InvalidVersionError",
    # Config Watcher (Hot Reload)
    "ConfigWatcher",
    "ConfigWatcherManager",
    "WatchedFile",
    "ReloadEvent",
    "FileFormat",
    "ReloadMode",
    "ConfigWatcherError",
    "WatcherNotStartedError",
    "InvalidFileError",
    "get_watcher_manager",
    "watch_config",
]
