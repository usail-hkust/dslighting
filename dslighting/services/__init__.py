"""Service namespace with lazy imports to avoid heavy import side effects."""

from importlib import import_module
from typing import Dict, Tuple

_LAZY_EXPORTS: Dict[str, Tuple[str, str]] = {
    "LLMService": ("dslighting.services.llm", "LLMService"),
    "SandboxService": ("dslighting.services.sandbox", "SandboxService"),
    "NotebookExecutor": ("dslighting.services.sandbox", "NotebookExecutor"),
    "ProcessIsolatedNotebookExecutor": (
        "dslighting.services.sandbox",
        "ProcessIsolatedNotebookExecutor",
    ),
    "WorkspaceService": ("dslighting.services.workspace", "WorkspaceService"),
    "VDBService": ("dslighting.services.vdb", "VDBService"),
}


def __getattr__(name: str):
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module 'dslighting.services' has no attribute '{name}'")
    module_name, attr_name = _LAZY_EXPORTS[name]
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(list(globals().keys()) + list(_LAZY_EXPORTS.keys()))


__all__ = list(_LAZY_EXPORTS.keys())
