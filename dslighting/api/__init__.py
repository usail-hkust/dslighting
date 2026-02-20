"""Layered API namespace for DSLighting (lazy-loaded)."""

from importlib import import_module
from typing import Dict, Optional, Tuple

_LAZY_EXPORTS: Dict[str, Tuple[str, Optional[str]]] = {
    "public": ("dslighting.api.public", None),
    "internal": ("dslighting.api.internal", None),
    "Agent": ("dslighting.api.agent", "Agent"),
    "AgentResult": ("dslighting.core.interfaces", "AgentResult"),
    "DataLoader": ("dslighting.core.data", "DataLoader"),
    "TaskContext": ("dslighting.core.data", "TaskContext"),
    "run_agent": ("dslighting.api.convenience", "run_agent"),
    "load_data": ("dslighting.api.convenience", "load_data"),
    "setup": ("dslighting.api.convenience", "setup"),
    "DSBenchmark": ("dslighting.api.benchmark", "DSBenchmark"),
    "DSLightingConfig": ("dslighting.config", "DSLightingConfig"),
    "TaskLoader": ("dslighting.api.task_loader", "TaskLoader"),
    "print_benchmark_banner": ("dslighting.api.utils", "print_benchmark_banner"),
    "print_benchmark_info": ("dslighting.api.utils", "print_benchmark_info"),
    "validate_paths": ("dslighting.api.utils", "validate_paths"),
}


def __getattr__(name: str):
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module 'dslighting.api' has no attribute '{name}'")
    module_name, attr_name = _LAZY_EXPORTS[name]
    try:
        module = import_module(module_name)
    except ModuleNotFoundError as exc:
        if name == "DSBenchmark":
            raise ImportError(
                "DSBenchmark requires benchmark dependencies (for example: pandas). "
                "Install missing packages and retry."
            ) from exc
        raise
    value = module if attr_name is None else getattr(module, attr_name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(list(globals().keys()) + list(_LAZY_EXPORTS.keys()))


__all__ = list(_LAZY_EXPORTS.keys())
