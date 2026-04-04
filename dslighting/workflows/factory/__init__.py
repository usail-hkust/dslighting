"""Workflow factory package."""

from .base import BaseWorkflowFactory
from .registry import WorkflowRegistry, default_workflow_registry
from .builtin import (
    AIDEWorkflowFactory,
    AutoMindWorkflowFactory,
    DSAgentWorkflowFactory,
    DataInterpreterWorkflowFactory,
    AutoKaggleWorkflowFactory,
    DeepAnalyzeWorkflowFactory,
    MyCustomAgentWorkflowFactory,
    AFlowWorkflowFactory,
    ReActWorkflowFactory,
    DynamicWorkflowFactory,
)


def get_workflow_factory(workflow_name: str) -> BaseWorkflowFactory:
    """Resolve a workflow name to its concrete workflow factory instance."""
    return default_workflow_registry.resolve(workflow_name)


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
