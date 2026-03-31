"""
Utility modules for DSLighting.

This module contains truly generic utility functions and constants that are
used throughout the DSLighting project:

- defaults.py: Default configurations and settings
- parsing.py: Helper functions for parsing structured content from LLM responses
- typing.py: Pydantic types and models for common data structures
- dynamic_import.py: Utilities for dynamic class imports from code strings
- constants.py: Centralized magic number and string constants

Note: Other utilities like monitoring, checkpoint, context, and error formatting
have been moved to their own dedicated modules (dslighting.monitoring,
dslighting.checkpoint, dslighting.state.context, dslighting.error).
"""

from dslighting.utils.defaults import (
    DEFAULT_WORKFLOW,
    DEFAULT_LLM_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_ITERATIONS,
    WORKFLOW_RECOMMENDATIONS,
    DEFAULT_CONFIG,
    DEFAULT_MAX_RETRIES,
    DEFAULT_API_BASE,
    DEFAULT_SANDBOX_TIMEOUT,
    DEFAULT_WORKSPACE_DIR,
    DEFAULT_KEEP_WORKSPACE_ON_FAILURE,
    DEFAULT_KEEP_ALL_WORKSPACES,
    DEFAULT_NUM_DRAFTS,
    ENV_API_KEY,
    ENV_API_BASE,
    ENV_LLM_MODEL,
    ENV_LLM_PROVIDER,
    ENV_LLM_MODEL_CONFIGS,
    ENV_LLM_TEMPERATURE,
    ENV_DSLIGHTING_DEFAULT_WORKFLOW,
    ENV_DSLIGHTING_WORKSPACE_DIR,
)

from dslighting.utils.parsing import (
    parse_plan_and_code,
)

from dslighting.utils.typing import (
    ExecutionResult,
)

from dslighting.utils.dynamic_import import (
    import_workflow_from_string,
    DynamicImportError,
)

from dslighting.utils.constants import (
    DEFAULT_MAX_CONCURRENT_PER_KEY,
    DEFAULT_POOL_SIZE,
    KEEPALIVE_TIMEOUT_SECONDS,
    DEFAULT_FLUSH_INTERVAL,
    DEFAULT_MAX_BATCH_SIZE,
    DEFAULT_POOL_SIZE_SANDBOX,
    WORKER_TIMEOUT_SECONDS,
    DEFAULT_MAX_DEPTH,
    DEFAULT_MAX_FILES,
    DEFAULT_MAX_ITEMS_PER_DIR,
    DEFAULT_CACHE_MAX_ENTRIES,
    FINGERPRINT_MAX_FILES,
    UNIQUE_SUFFIX_LENGTH,
    CODE_FILENAME_ZERO_PADDING,
    DEFAULT_TOTAL_STEPS,
    DEFAULT_DEBUG_PROBABILITY,
    DEFAULT_SUCCESS_THRESHOLD,
    DEFAULT_MAX_ROUNDS,
    DEFAULT_MAX_INFLIGHT_NODES,
    DEFAULT_CACHE_TTL_SECONDS,
    MAX_MEMORY_MB,
    CPU_TIMEOUT_SECONDS,
    LLM_HTTP_CLIENT_TIMEOUT,
    FINGERPRINT_SCAN_DEPTH,
    DEEP_DISCOVERY_MAX_DIRS,
    DEEP_DISCOVERY_MAX_FILES,
    PER_DIR_LIMIT,
    MAX_ROWS_PER_FILE,
)

# Re-export configuration defaults from defaults.py
from dslighting.utils.defaults import (
    DEFAULT_TEMPERATURE,
    DEFAULT_NUM_DRAFTS,
    DEFAULT_SANDBOX_TIMEOUT as SANDBOX_TIMEOUT_SECONDS,
)

from dslighting.logging import (
    configure_logging,
    LoggingConfig,
    LoggingController,
)

from dslighting.utils.package_detector import (
    PackageDetector,
    detect_and_save_packages,
)

from dslighting.utils.data_preloader import (
    DatasetPreloader,
    preload_datasets_async,
)

from dslighting.utils.file_monitor import (
    FileSharedMonitor,
    get_file_monitor,
)

__all__ = [
    # defaults
    "DEFAULT_WORKFLOW",
    "DEFAULT_LLM_MODEL",
    "DEFAULT_TEMPERATURE",
    "DEFAULT_MAX_ITERATIONS",
    "WORKFLOW_RECOMMENDATIONS",
    "DEFAULT_CONFIG",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_API_BASE",
    "DEFAULT_SANDBOX_TIMEOUT",
    "DEFAULT_WORKSPACE_DIR",
    "DEFAULT_KEEP_WORKSPACE_ON_FAILURE",
    "DEFAULT_KEEP_ALL_WORKSPACES",
    "DEFAULT_NUM_DRAFTS",
    "ENV_API_KEY",
    "ENV_API_BASE",
    "ENV_LLM_MODEL",
    "ENV_LLM_PROVIDER",
    "ENV_LLM_MODEL_CONFIGS",
    "ENV_LLM_TEMPERATURE",
    "ENV_DSLIGHTING_DEFAULT_WORKFLOW",
    "ENV_DSLIGHTING_WORKSPACE_DIR",
    # parsing
    "parse_plan_and_code",
    # typing
    "ExecutionResult",
    # dynamic_import
    "import_workflow_from_string",
    "DynamicImportError",
    # constants
    "DEFAULT_MAX_CONCURRENT_PER_KEY",
    "DEFAULT_POOL_SIZE",
    "KEEPALIVE_TIMEOUT_SECONDS",
    "DEFAULT_FLUSH_INTERVAL",
    "DEFAULT_MAX_BATCH_SIZE",
    "DEFAULT_POOL_SIZE_SANDBOX",
    "WORKER_TIMEOUT_SECONDS",
    "DEFAULT_MAX_DEPTH",
    "DEFAULT_MAX_FILES",
    "DEFAULT_MAX_ITEMS_PER_DIR",
    "DEFAULT_CACHE_MAX_ENTRIES",
    "FINGERPRINT_MAX_FILES",
    "UNIQUE_SUFFIX_LENGTH",
    "CODE_FILENAME_ZERO_PADDING",
    "SANDBOX_TIMEOUT_SECONDS",
    "DEFAULT_TOTAL_STEPS",
    "DEFAULT_DEBUG_PROBABILITY",
    "DEFAULT_SUCCESS_THRESHOLD",
    "DEFAULT_MAX_ROUNDS",
    "DEFAULT_MAX_INFLIGHT_NODES",
    "DEFAULT_CACHE_TTL_SECONDS",
    "MAX_MEMORY_MB",
    "CPU_TIMEOUT_SECONDS",
    "LLM_HTTP_CLIENT_TIMEOUT",
    "FINGERPRINT_SCAN_DEPTH",
    "DEEP_DISCOVERY_MAX_DIRS",
    "DEEP_DISCOVERY_MAX_FILES",
    "PER_DIR_LIMIT",
    "MAX_ROWS_PER_FILE",
    # unified logging
    "configure_logging",
    "LoggingConfig",
    "LoggingController",
    # package_detector
    "PackageDetector",
    "detect_and_save_packages",
    # data_preloader
    "DatasetPreloader",
    "preload_datasets_async",
    # file_monitor
    "FileSharedMonitor",
    "get_file_monitor",
]
