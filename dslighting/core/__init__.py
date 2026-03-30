"""
DSLighting Core Modules

Internal module; prefer importing from the package root (`dslighting`) for the single public entrypoint.
"""

from importlib import import_module
from typing import Dict, Tuple

_LAZY_EXPORTS: Dict[str, Tuple[str, str]] = {
    "AgentResult": ("dslighting.core.interfaces", "AgentResult"),
    "AgentInterface": ("dslighting.core.interfaces", "AgentInterface"),
    "DataLoader": ("dslighting.core.data", "DataLoader"),
    "TaskContext": ("dslighting.core.data", "TaskContext"),
    "TaskDetector": ("dslighting.core.detection", "TaskDetector"),
    "ConfigBuilder": ("dslighting.core.config", "ConfigBuilder"),
}


def __getattr__(name: str):
    if name in _LAZY_EXPORTS:
        module_name, attr_name = _LAZY_EXPORTS[name]
        module = import_module(module_name)
        value = getattr(module, attr_name)
        globals()[name] = value
        return value

    try:
        module = import_module(f"dslighting.core.{name}")
        globals()[name] = module
        return module
    except ImportError:
        pass

    raise AttributeError(f"module 'dslighting.core' has no attribute '{name}'")

__all__ = [
    "DataLoader",
    "TaskContext",
    "AgentResult",
    "AgentInterface",
    "TaskDetector",
    "ConfigBuilder",
]
