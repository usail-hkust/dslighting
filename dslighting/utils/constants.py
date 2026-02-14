"""Constants module for dslighting.

This module centralizes all magic number constants used throughout
the dslighting project to improve code maintainability and reduce
hardcoded values across the codebase.

NOTE: Some configuration defaults (e.g., DEFAULT_TEMPERATURE) are duplicated
in defaults.py for backward compatibility. The defaults.py module is the PRIMARY
source of truth for configuration defaults. This constants.py module contains
both operational constants and a subset of configuration defaults.
When in doubt, prefer importing from defaults.py for configuration values.
"""

from __future__ import annotations

from typing import Final

# =============================================================================
# LLM Service Constants
# =============================================================================

DEFAULT_MAX_CONCURRENT_PER_KEY: Final[int] = 20
"""Maximum concurrent requests per API key."""

DEFAULT_POOL_SIZE: Final[int] = 10
"""Default connection pool size for LLM clients."""

KEEPALIVE_TIMEOUT_SECONDS: Final[float] = 300.0
"""Keep-alive timeout for HTTP connections in seconds."""

# =============================================================================
# Sandbox Service Constants
# =============================================================================

DEFAULT_FLUSH_INTERVAL: Final[float] = 1.0
"""Default flush interval for batch processing in seconds."""

DEFAULT_MAX_BATCH_SIZE: Final[int] = 100
"""Maximum number of items per batch."""

DEFAULT_POOL_SIZE_SANDBOX: Final[int] = 4
"""Default pool size for sandbox workers."""

WORKER_TIMEOUT_SECONDS: Final[int] = 120
"""Timeout for worker operations in seconds."""

# =============================================================================
# Data Analyzer Constants
# =============================================================================

DEFAULT_MAX_DEPTH: Final[int] = 5
"""Maximum directory traversal depth."""

DEFAULT_MAX_FILES: Final[int] = 100
"""Maximum number of files to analyze."""

DEFAULT_MAX_ITEMS_PER_DIR: Final[int] = 20
"""Maximum items per directory during scanning."""

DEFAULT_CACHE_MAX_ENTRIES: Final[int] = 512
"""Maximum entries in analysis cache."""

FINGERPRINT_MAX_FILES: Final[int] = 20000
"""Maximum files for fingerprint generation."""

# =============================================================================
# Runner Constants
# =============================================================================

UNIQUE_SUFFIX_LENGTH: Final[int] = 8
"""Length of unique identifier suffix for generated files."""

CODE_FILENAME_ZERO_PADDING: Final[int] = 3
"""Zero padding width for numbered code filenames."""

# =============================================================================
# Configuration Constants
# =============================================================================
# NOTE: DEFAULT_TEMPERATURE, DEFAULT_NUM_DRAFTS, and SANDBOX_TIMEOUT_SECONDS
# are defined in defaults.py as the primary source of truth.
# For backward compatibility, these values are also available from this module
# via re-export from defaults.py (see dslighting.utils.__init__.py).

DEFAULT_TOTAL_STEPS: Final[int] = 4
"""Default number of total steps in workflow."""

DEFAULT_DEBUG_PROBABILITY: Final[float] = 0.8
"""Default probability for debug mode."""

DEFAULT_SUCCESS_THRESHOLD: Final[float] = 3.0
"""Default success threshold for evaluations."""

DEFAULT_MAX_ROUNDS: Final[int] = 10
"""Default maximum number of workflow rounds."""

DEFAULT_MAX_INFLIGHT_NODES: Final[int] = 256
"""Default maximum number of in-flight execution nodes."""

# =============================================================================
# Cache TTL Constants
# =============================================================================

DEFAULT_CACHE_TTL_SECONDS: Final[int] = 3600
"""Default cache time-to-live in seconds (1 hour)."""

# =============================================================================
# Sandbox Resource Limits
# =============================================================================

MAX_MEMORY_MB: Final[int] = 4096
"""Maximum memory allocation for sandbox processes in megabytes."""

CPU_TIMEOUT_SECONDS: Final[int] = 300
"""CPU timeout for sandbox execution in seconds."""

# =============================================================================
# HTTP Client Timeout
# =============================================================================

LLM_HTTP_CLIENT_TIMEOUT: Final[int] = 120
"""Timeout for LLM HTTP client connections in seconds."""

# =============================================================================
# Data Analysis Limits
# =============================================================================

FINGERPRINT_SCAN_DEPTH: Final[int] = 3
"""Depth limit for directory fingerprint scanning."""

DEEP_DISCOVERY_MAX_DIRS: Final[int] = 200
"""Maximum directories to explore in deep discovery mode."""

DEEP_DISCOVERY_MAX_FILES: Final[int] = 8
"""Maximum files to analyze in deep discovery mode."""

PER_DIR_LIMIT: Final[int] = 200
"""Maximum items to sample per directory during scanning."""

MAX_ROWS_PER_FILE: Final[int] = 5000
"""Maximum rows to read per file for schema analysis."""
