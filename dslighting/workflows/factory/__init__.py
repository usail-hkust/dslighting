"""Workflow factory package with lazy exports."""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "BaseWorkflowFactory",
    "WorkflowRegistry",
    "default_workflow_registry",
    "get_workflow_factory",
    "AIDEWorkflowFactory",
    "AutoMindWorkflowFactory",
    "DSAgentWorkflowFactory",
    "DataInterpreterWorkflowFactory",
    "AutoKaggleWorkflowFactory",
    "DeepAnalyzeWorkflowFactory",
    "MyCustomAgentWorkflowFactory",
    "AFlowWorkflowFactory",
    "ReActWorkflowFactory",
    "DynamicWorkflowFactory",
]

_EXPORT_MAP = {
    "BaseWorkflowFactory": ("dslighting.workflows.factory.base", "BaseWorkflowFactory"),
    "WorkflowRegistry": ("dslighting.workflows.factory.registry", "WorkflowRegistry"),
    "default_workflow_registry": (
        "dslighting.workflows.factory.registry",
        "default_workflow_registry",
    ),
    "AIDEWorkflowFactory": ("dslighting.workflows.factory.builtin", "AIDEWorkflowFactory"),
    "AutoMindWorkflowFactory": ("dslighting.workflows.factory.builtin", "AutoMindWorkflowFactory"),
    "DSAgentWorkflowFactory": ("dslighting.workflows.factory.builtin", "DSAgentWorkflowFactory"),
    "DataInterpreterWorkflowFactory": (
        "dslighting.workflows.factory.builtin",
        "DataInterpreterWorkflowFactory",
    ),
    "AutoKaggleWorkflowFactory": (
        "dslighting.workflows.factory.builtin",
        "AutoKaggleWorkflowFactory",
    ),
    "DeepAnalyzeWorkflowFactory": (
        "dslighting.workflows.factory.builtin",
        "DeepAnalyzeWorkflowFactory",
    ),
    "MyCustomAgentWorkflowFactory": (
        "dslighting.workflows.factory.builtin",
        "MyCustomAgentWorkflowFactory",
    ),
    "AFlowWorkflowFactory": ("dslighting.workflows.factory.builtin", "AFlowWorkflowFactory"),
    "ReActWorkflowFactory": ("dslighting.workflows.factory.builtin", "ReActWorkflowFactory"),
    "DynamicWorkflowFactory": ("dslighting.workflows.factory.builtin", "DynamicWorkflowFactory"),
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


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + list(_EXPORT_MAP.keys()))


def get_workflow_factory(workflow_name: str):
    """Resolve a workflow name to its concrete workflow factory instance."""
    from dslighting.workflows.factory.registry import default_workflow_registry

    return default_workflow_registry.resolve(workflow_name)
