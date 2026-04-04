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
    "configure_logging": ("dslighting.logging", "configure_logging"),
    # Core config
    "DSLightingConfig": ("dslighting.config", "DSLightingConfig"),
    # Advanced architecture namespace
    "arch": ("dslighting.arch", None),
}


def __getattr__(name: str):
    if name == "DSBenchmark":
        raise AttributeError(
            "DSBenchmark is no longer exported from the dslighting root package. "
            "Use 'from dslighting.api import DSBenchmark' instead."
        )

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
        ("ReAct", "Reasoning + acting workflow with strict tags"),
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
    "configure_logging",
    "DSLightingConfig",
    # Advanced architecture namespace
    "arch",
    "help",
    "list_workflows",
    "list_prompts",
    "list_operators",
    "explore",
]
