"""
Default configurations for DSLighting simplified API.

This module defines sensible defaults that can be overridden by:
1. User parameters (highest priority)
2. Environment variables
3. These defaults (lowest priority)
"""

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

DEFAULT_WORKSPACE_DIR = "./runs/dslighting"
DEFAULT_KEEP_WORKSPACE_ON_FAILURE = True
DEFAULT_KEEP_ALL_WORKSPACES = False


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
to create the final DSATConfig.
"""

DEFAULT_CONFIG: Dict[str, Any] = {
    "llm": {
        "model": DEFAULT_LLM_MODEL,
        "temperature": DEFAULT_TEMPERATURE,
        "max_retries": DEFAULT_MAX_RETRIES,
        "api_base": DEFAULT_API_BASE,
        "api_key": None,  # Will be loaded from env
    },
    "workflow": {
        "name": DEFAULT_WORKFLOW,
        "params": {}
    },
    "run": {
        "name": "dsat_run",  # Use "dsat_run" to let DSATRunner auto-generate: dsat_run_{task_id}_{uid}
        "total_steps": DEFAULT_MAX_ITERATIONS,
        "keep_all_workspaces": DEFAULT_KEEP_ALL_WORKSPACES,
        "keep_workspace_on_failure": DEFAULT_KEEP_WORKSPACE_ON_FAILURE,
        "parameters": {},
    },
    "sandbox": {
        "timeout": DEFAULT_SANDBOX_TIMEOUT,
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
