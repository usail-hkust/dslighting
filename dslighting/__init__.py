"""
DSLighting - Data Science Agent Framework

A comprehensive framework for building autonomous data science agents that can
perform exploratory data analysis, feature engineering, machine learning, and more.

The package root intentionally keeps imports lightweight. Public objects are
loaded lazily on first access to minimize startup time.

Example:
    >>> from dslighting import run_agent
    >>> result = run_agent(task_id="bike-sharing-demand")
"""

from importlib import import_module
from importlib.metadata import PackageNotFoundError, version as package_version
from typing import Dict, Tuple
import warnings

try:
    __version__ = package_version("dslighting")
except PackageNotFoundError:
    __version__ = "2.7.9"

__author__ = "DSLighting Team"


_LAZY_EXPORTS: Dict[str, Tuple[str, str]] = {
    # User-facing API
    "Agent": ("dslighting.api.agent", "Agent"),
    "AgentResult": ("dslighting.core.interfaces", "AgentResult"),
    "run_agent": ("dslighting.api.convenience", "run_agent"),
    "load_data": ("dslighting.api.convenience", "load_data"),
    "setup": ("dslighting.api.convenience", "setup"),
    "analyze": ("dslighting.api.convenience", "analyze"),
    "process": ("dslighting.api.convenience", "process"),
    "model": ("dslighting.api.convenience", "model"),
    "DSBenchmark": ("dslighting.api.benchmark", "DSBenchmark"),
    # i18n utilities
    "DEFAULT_LANGUAGE": ("dslighting.utils.i18n", "DEFAULT_LANGUAGE"),
    "SUPPORTED_LANGUAGES": ("dslighting.utils.i18n", "SUPPORTED_LANGUAGES"),
    # Data API
    "DataLoader": ("dslighting.core.data", "DataLoader"),
    "TaskContext": ("dslighting.core.data", "TaskContext"),
    "DatasetInfo": ("dslighting.core.data", "DatasetInfo"),
    "load_dataset": ("dslighting.core.data", "load_dataset"),
    # Workflow API
    "BaseWorkflow": ("dslighting.workflows.base", "BaseWorkflow"),
    "BaseWorkflowFactory": ("dslighting.workflows.factory.base", "BaseWorkflowFactory"),
    "AIDE": ("dslighting.workflows.presets", "AIDE"),
    "AutoKaggle": ("dslighting.workflows.presets", "AutoKaggle"),
    "DataInterpreter": ("dslighting.workflows.presets", "DataInterpreter"),
    "DeepAnalyze": ("dslighting.workflows.presets", "DeepAnalyze"),
    "DSAgent": ("dslighting.workflows.presets", "DSAgent"),
    "AutoMind": ("dslighting.workflows.presets", "AutoMind"),
    "AFlow": ("dslighting.workflows.presets", "AFlow"),
    # Config and task types
    "DSLightingConfig": ("dslighting.config", "DSLightingConfig"),
    "LLMConfig": ("dslighting.config", "LLMConfig"),
    "SchedulerConfig": ("dslighting.config", "SchedulerConfig"),
    "DagRuntimeConfig": ("dslighting.config", "DagRuntimeConfig"),
    "TaskConfig": ("dslighting.config", "TaskConfig"),
    "ConfigBuilder": ("dslighting.core.config", "ConfigBuilder"),
    "DSLightingRunner": ("dslighting.runner", "DSLightingRunner"),
    "Runner": ("dslighting.runner", "DSLightingRunner"),
    "DagRuntime": ("dslighting.runtime", "DagRuntime"),
    "DagRuntimeOptions": ("dslighting.runtime", "DagRuntimeOptions"),
    "OpNode": ("dslighting.runtime", "OpNode"),
    "NodeResult": ("dslighting.runtime", "NodeResult"),
    "DABenchmark": ("dslighting.benchmark", "DABenchmark"),
    "BenchmarkFactory": ("dslighting.benchmark", "BenchmarkFactory"),
    # Datasets
    "datasets": ("dslighting.datasets", None),
    # Advanced architecture namespace
    "arch": ("dslighting.arch", None),
    "TaskDefinition": ("dslighting.core.types", "TaskDefinition"),
    "TaskType": ("dslighting.core.types", "TaskType"),
    "TaskMode": ("dslighting.core.types", "TaskMode"),
    "WorkflowCandidate": ("dslighting.core.types", "WorkflowCandidate"),
    "ReviewResult": ("dslighting.core.types", "ReviewResult"),
    "Plan": ("dslighting.core.types", "Plan"),
    "MLETaskLoader": ("dslighting.core.tasks", "MLETaskLoader"),
    # Error handling (new unified module)
    "DSLightingError": ("dslighting.error.exceptions", "DSLightingError"),
    "ConfigurationError": ("dslighting.error.exceptions", "ConfigurationError"),
    "WorkflowError": ("dslighting.error.exceptions", "WorkflowError"),
    "BenchmarkError": ("dslighting.error.exceptions", "BenchmarkError"),
    "LLMServiceError": ("dslighting.error.exceptions", "LLMServiceError"),
    "TaskError": ("dslighting.error.exceptions", "TaskError"),
    "WorkspaceError": ("dslighting.error.exceptions", "WorkspaceError"),
    "FormattedError": ("dslighting.error.formatter", "FormattedError"),
    "ErrorRegistry": ("dslighting.error.formatter", "ErrorRegistry"),
    "ErrorDefinition": ("dslighting.error.formatter", "ErrorDefinition"),
    "format_error": ("dslighting.error.formatter", "format_error"),
    "safe_format": ("dslighting.error.formatter", "safe_format"),
    # Checkpoint
    "CheckpointManager": ("dslighting.checkpoint.checkpoint", "CheckpointManager"),
}


def __getattr__(name: str):
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module 'dslighting' has no attribute '{name}'")

    module_name, attr_name = _LAZY_EXPORTS[name]
    try:
        module = import_module(module_name)
        if attr_name is None:
            # Export the module itself
            value = module
        else:
            value = getattr(module, attr_name)
    except ImportError as e:
        warnings.warn(
            f"Failed to lazy-load attribute '{name}' from module '{module_name}': {e}",
            ImportWarning,
            stacklevel=2,
        )
        raise

    globals()[name] = value
    return value


def __dir__():
    return sorted(list(globals().keys()) + list(_LAZY_EXPORTS.keys()))


def list_workflows() -> None:
    """Print available built-in workflows."""
    workflows = [
        ("AIDE", "Adaptive Iteration and Debugging Enhancement"),
        ("AutoKaggle", "Competition-solving workflow"),
        ("DataInterpreter", "EDA and analysis workflow"),
        ("DeepAnalyze", "Deep analysis workflow"),
        ("DSAgent", "Structured operator workflow"),
        ("AutoMind", "Planning workflow with knowledge retrieval"),
        ("AFlow", "Meta-optimization workflow"),
    ]

    print("DSLighting workflows:")
    for name, desc in workflows:
        print(f"  {name:<16} {desc}")


def help() -> None:
    """Show minimal quick-start instructions."""
    print("DSLighting quick start:")
    print("  from dslighting import run_agent")
    print("  result = run_agent(task_id='bike-sharing-demand')")
    print("")
    print("Inspect available workflows via:")
    print("  dslighting.list_workflows()")


def list_prompts(category: str = "all"):
    """List available prompt functions by category."""
    try:
        from dslighting.prompts import list_available_prompts

        return list_available_prompts(category)
    except ImportError as e:
        warnings.warn(
            f"Failed to load prompts module: {e}",
            ImportWarning,
            stacklevel=2,
        )
        return {}


def list_operators(category: str = "all"):
    """List available operators by category."""
    try:
        from dslighting.ops import list_available_operators

        return list_available_operators(category)
    except ImportError as e:
        warnings.warn(
            f"Failed to load operators module: {e}",
            ImportWarning,
            stacklevel=2,
        )
        return {}


def explore() -> None:
    """Print high-level package discovery information."""
    print("Workflows:")
    list_workflows()
    print("")
    print("Prompt categories:", ", ".join(sorted(list_prompts().keys())))
    print("Operator categories:", ", ".join(sorted(list_operators().keys())))


__all__ = [
    "__version__",
    "__author__",
    "Agent",
    "AgentResult",
    "run_agent",
    "load_data",
    "setup",
    "analyze",
    "process",
    "model",
    "DSBenchmark",
    "DataLoader",
    "TaskContext",
    "DatasetInfo",
    "load_dataset",
    "BaseWorkflow",
    "BaseWorkflowFactory",
    "AIDE",
    "AutoKaggle",
    "DataInterpreter",
    "DeepAnalyze",
    "DSAgent",
    "AutoMind",
    "AFlow",
    "DSLightingConfig",
    "LLMConfig",
    "SchedulerConfig",
    "DagRuntimeConfig",
    "TaskConfig",
    "ConfigBuilder",
    "DSLightingRunner",
    "Runner",
    "DagRuntime",
    "DagRuntimeOptions",
    "OpNode",
    "NodeResult",
    "DABenchmark",
    "BenchmarkFactory",
    "TaskDefinition",
    "TaskType",
    "TaskMode",
    "WorkflowCandidate",
    "ReviewResult",
    "Plan",
    "MLETaskLoader",
    # i18n utilities
    "DEFAULT_LANGUAGE",
    "SUPPORTED_LANGUAGES",
    # Error handling
    "DSLightingError",
    "ConfigurationError",
    "WorkflowError",
    "BenchmarkError",
    "LLMServiceError",
    "TaskError",
    "WorkspaceError",
    "FormattedError",
    "ErrorRegistry",
    "ErrorDefinition",
    "format_error",
    "safe_format",
    # Checkpoint
    "CheckpointManager",
    # Datasets
    "datasets",
    # Advanced architecture namespace
    "arch",
    "help",
    "list_workflows",
    "list_prompts",
    "list_operators",
    "explore",
]
