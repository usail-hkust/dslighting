"""
Workflow factory package.
"""

from typing import Dict, Type

from .base import BaseWorkflowFactory
from .standard import (
    WorkflowFactory,
    AIDEWorkflowFactory,
    AutoMindWorkflowFactory,
    DSAgentWorkflowFactory,
    DataInterpreterWorkflowFactory,
    AutoKaggleWorkflowFactory,
    DeepAnalyzeWorkflowFactory,
    MyCustomAgentWorkflowFactory,
    AFlowWorkflowFactory,
    DynamicWorkflowFactory,
)

_WORKFLOW_FACTORY_CLASSES: Dict[str, Type[WorkflowFactory]] = {
    "aide": AIDEWorkflowFactory,
    "automind": AutoMindWorkflowFactory,
    "dsagent": DSAgentWorkflowFactory,
    "data_interpreter": DataInterpreterWorkflowFactory,
    "autokaggle": AutoKaggleWorkflowFactory,
    "deepanalyze": DeepAnalyzeWorkflowFactory,
    "aflow": AFlowWorkflowFactory,
    "my_custom_agent": MyCustomAgentWorkflowFactory,
}


def get_workflow_factory(workflow_name: str) -> WorkflowFactory:
    """
    Resolve a workflow name to its concrete workflow factory instance.
    """
    normalized = (workflow_name or "").strip().lower()
    factory_class = _WORKFLOW_FACTORY_CLASSES.get(normalized)
    if factory_class is None:
        available = ", ".join(sorted(_WORKFLOW_FACTORY_CLASSES.keys()))
        raise ValueError(
            f"Unknown workflow '{workflow_name}'. Available workflows: [{available}]"
        )
    return factory_class()


__all__ = [
    "BaseWorkflowFactory",
    "WorkflowFactory",
    "get_workflow_factory",
    "AIDEWorkflowFactory",
    "AutoMindWorkflowFactory",
    "DSAgentWorkflowFactory",
    "DataInterpreterWorkflowFactory",
    "AutoKaggleWorkflowFactory",
    "DeepAnalyzeWorkflowFactory",
    "MyCustomAgentWorkflowFactory",
    "AFlowWorkflowFactory",
    "DynamicWorkflowFactory",
]
