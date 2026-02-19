"""Workflow factory registry."""

from __future__ import annotations

from typing import Dict, Type

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
)


class WorkflowRegistry:
    """Single source of truth for workflow->factory mapping."""

    def __init__(self) -> None:
        self._factory_classes: Dict[str, Type[WorkflowFactory]] = {
            "aide": AIDEWorkflowFactory,
            "automind": AutoMindWorkflowFactory,
            "dsagent": DSAgentWorkflowFactory,
            "data_interpreter": DataInterpreterWorkflowFactory,
            "autokaggle": AutoKaggleWorkflowFactory,
            "deepanalyze": DeepAnalyzeWorkflowFactory,
            "aflow": AFlowWorkflowFactory,
            "my_custom_agent": MyCustomAgentWorkflowFactory,
        }

    def register(self, workflow_name: str, factory_class: Type[WorkflowFactory]) -> None:
        """Register or overwrite a workflow factory mapping."""
        self._factory_classes[workflow_name.strip().lower()] = factory_class

    def resolve(self, workflow_name: str) -> WorkflowFactory:
        """Create the concrete workflow factory for a name."""
        normalized = (workflow_name or "").strip().lower()
        factory_class = self._factory_classes.get(normalized)
        if factory_class is None:
            available = ", ".join(sorted(self._factory_classes.keys()))
            raise ValueError(
                f"Unknown workflow '{workflow_name}'. Available workflows: [{available}]"
            )
        return factory_class()

    def list_workflows(self) -> list[str]:
        """List registered workflow names."""
        return sorted(self._factory_classes.keys())


default_workflow_registry = WorkflowRegistry()

