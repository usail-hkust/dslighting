"""ReAct workflow package with lazy exports to avoid import cycles."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

__all__ = [
    "ReActContextConfig",
    "ReActContextManager",
    "ReActTurnResult",
    "ReActWorkflow",
    "build_react_context_config",
    "normalize_react_context_params",
    "validate_react_operator_params",
]

if TYPE_CHECKING:
    from dslighting.workflows.search.react.context_manager import (
        ReActContextConfig,
        ReActContextManager,
        build_react_context_config,
        normalize_react_context_params,
    )
    from dslighting.workflows.search.react.protocol import ReActTurnResult
    from dslighting.workflows.search.react.validation import (
        validate_react_operator_params,
    )
    from dslighting.workflows.search.react.workflow import ReActWorkflow


_EXPORT_MAP = {
    "ReActContextConfig": (
        "dslighting.workflows.search.react.context_manager",
        "ReActContextConfig",
    ),
    "ReActContextManager": (
        "dslighting.workflows.search.react.context_manager",
        "ReActContextManager",
    ),
    "build_react_context_config": (
        "dslighting.workflows.search.react.context_manager",
        "build_react_context_config",
    ),
    "normalize_react_context_params": (
        "dslighting.workflows.search.react.context_manager",
        "normalize_react_context_params",
    ),
    "ReActTurnResult": (
        "dslighting.workflows.search.react.protocol",
        "ReActTurnResult",
    ),
    "validate_react_operator_params": (
        "dslighting.workflows.search.react.validation",
        "validate_react_operator_params",
    ),
    "ReActWorkflow": (
        "dslighting.workflows.search.react.workflow",
        "ReActWorkflow",
    ),
}


def __getattr__(name: str) -> Any:
    target = _EXPORT_MAP.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attr_name = target
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value

