"""
Default configurations for DSLighting simplified API.

This module defines sensible defaults that can be overridden by:
1. User parameters (highest priority)
2. Environment variables
3. These defaults (lowest priority)

NOTE: This is the PRIMARY source for default configuration values.
This module is the single source of truth for configuration defaults.
constants.py may re-export selected values for backward compatibility.
Any default-value changes should be made here first.
"""

from __future__ import annotations

from typing import Dict, List, Any


# ============================================================================
# LLM Defaults
# ============================================================================

DEFAULT_LLM_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_RETRIES = 3
DEFAULT_API_BASE = "https://api.openai.com/v1"


# ============================================================================
# Workflow Defaults
# ============================================================================

DEFAULT_WORKFLOW = "aide"
DEFAULT_MAX_ITERATIONS = 5
DEFAULT_NUM_DRAFTS = 5


# ============================================================================
# Sandbox Defaults
# ============================================================================

DEFAULT_SANDBOX_TIMEOUT = 6 * 3600  # 6 hours


# ============================================================================
# Workspace Defaults
# ============================================================================

DEFAULT_WORKSPACE_DIR = "./runs/dslighting_workspace"
DEFAULT_KEEP_WORKSPACE_ON_FAILURE = True
DEFAULT_KEEP_ALL_WORKSPACES = False


# ============================================================================
# Runtime / Scheduling Defaults
# ============================================================================

DEFAULT_TOTAL_STEPS = 4
DEFAULT_DEBUG_PROBABILITY = 0.8
DEFAULT_SUCCESS_THRESHOLD = 3.0
DEFAULT_MAX_ROUNDS = 10
DEFAULT_MAX_INFLIGHT_NODES = 256
DEFAULT_CACHE_TTL_SECONDS = 3600
DEFAULT_CACHE_MAX_ENTRIES = 512


# ============================================================================
# Workflow Recommendations
# ============================================================================

"""
Workflow recommendations based on task type and data characteristics.

This mapping helps auto-select the best workflow for a given task.
Users can override this by explicitly specifying the workflow.
"""

WORKFLOW_RECOMMENDATIONS: Dict[str, Dict[str, Any]] = {
    "kaggle_competition": {
        "tabular": ["autokaggle", "aide"],
        "time_series": ["aide", "automind"],
        "default": "aide"
    },
    "open_ended": {
        "analysis": ["deepanalyze", "automind"],
        "modeling": ["aide", "deepanalyze"],
        "default": "deepanalyze"
    },
    "quick_analysis": {
        "eda": ["data_interpreter"],
        "debugging": ["data_interpreter"],
        "default": "data_interpreter"
    },
    "qa": {
        "default": "aide"
    },
    "datasci": {
        "default": "aide"
    }
}


# ============================================================================
# Full Default Configuration
# ============================================================================

"""
Complete default configuration structure.

This can be merged with user parameters and environment variables
to create the final DSLightingConfig.
"""

DEFAULT_CONFIG: Dict[str, Any] = {
    "llm": {
        "model": DEFAULT_LLM_MODEL,
        "temperature": DEFAULT_TEMPERATURE,
        "max_retries": DEFAULT_MAX_RETRIES,
        "max_concurrent_per_key": 20,
        "api_base": DEFAULT_API_BASE,
        "api_key": None,  # Will be loaded from env
    },
    "workflow": {
        "name": DEFAULT_WORKFLOW,
        "params": {}
    },
    "run": {
        "run_name": "dslighting_run",  # Default sentinel; DSLightingRunner always generates two-layer workspace: <run_name>/<task_id>_<uid>/
        "total_steps": DEFAULT_MAX_ITERATIONS,
        "keep_all_workspaces": DEFAULT_KEEP_ALL_WORKSPACES,
        "keep_workspace_on_failure": DEFAULT_KEEP_WORKSPACE_ON_FAILURE,
        "parameters": {},
    },
    "sandbox": {
        "timeout": DEFAULT_SANDBOX_TIMEOUT,
    },
    "data_analysis": {
        "enabled": True,
        "cache_enabled": True,
        "cache_dir": None,
        "cache_max_entries": DEFAULT_CACHE_MAX_ENTRIES,
        "cache_debug_metrics": False,
        "analyzer_version": None,
        "profile": "balanced",
        "max_artifacts": 12,
        "max_report_chars": 14000,
        "document_preview_lines": 12,
        "enable_document_inspection": True,
        "enable_database_inspection": True,
        "tabular_tolerant_fallback": True,
    },
    "scheduler": {
        "max_concurrency": None,
        "scheduler_policy": "full_parallel",
        "queue_policy": "fifo",
        "workload_mode": "auto",
        "gpu_policy": "auto",
        "gpu_ids": None,
        "gpu_max_tasks_per_device": None,
        "gpu_memory_utilization_target": 0.85,
        "gpu_reserved_memory_gb": 2.0,
        "enable_monitoring": False,
        "enable_adaptive_concurrency": False,
        "adaptive_target_p95_seconds": 60.0,
        "oom_max_retries": 1,
        "oom_retry_backoff_seconds": 2.0,
        "oom_retry_memory_growth": 1.35,
        "sandbox_memory_mode": "off",
        "sandbox_default_memory_gb": 6.0,
        "llm_max_concurrency": None,
        "cpu_worker_pool_size": None,
        "exp_name": None,
        "monitor_language": None,
        "enable_file_sharing": True,
        "checkpoint_resume_enabled": False,
        "run_id": None,
    },
    "agent": {
        "search": {
            "num_drafts": DEFAULT_NUM_DRAFTS,
            "max_iterations": DEFAULT_MAX_ITERATIONS,
            "debug_prob": 0.8,
            "max_debug_depth": 10,
        },
        "max_retries": 10,
        "autokaggle": {
            "max_attempts_per_phase": 10,
            "success_threshold": 3.0,
        }
    }
}


# ============================================================================
# Environment Variable Names
# ============================================================================

"""
Environment variables that DSLighting reads.

These can be set in .env file or exported in the shell.
"""

ENV_API_KEY = "API_KEY"
ENV_API_BASE = "API_BASE"
ENV_LLM_MODEL = "LLM_MODEL"
ENV_LLM_PROVIDER = "LLM_PROVIDER"
ENV_LLM_MODEL_CONFIGS = "LLM_MODEL_CONFIGS"
ENV_LLM_TEMPERATURE = "LLM_TEMPERATURE"

ENV_DSLIGHTING_DEFAULT_WORKFLOW = "DSLIGHTING_DEFAULT_WORKFLOW"
ENV_DSLIGHTING_WORKSPACE_DIR = "DSLIGHTING_WORKSPACE_DIR"
