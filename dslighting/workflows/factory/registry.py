"""Workflow factory registry."""

from __future__ import annotations

from typing import Dict, Type

from .base import BaseWorkflowFactory
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
)


class WorkflowRegistry:
    """Single source of truth for workflow->factory mapping."""

    def __init__(self) -> None:
        self._factory_classes: Dict[str, Type[BaseWorkflowFactory]] = {
            "aide": AIDEWorkflowFactory,
            "automind": AutoMindWorkflowFactory,
            "dsagent": DSAgentWorkflowFactory,
            "data_interpreter": DataInterpreterWorkflowFactory,
            "autokaggle": AutoKaggleWorkflowFactory,
            "deepanalyze": DeepAnalyzeWorkflowFactory,
            "aflow": AFlowWorkflowFactory,
            "react": ReActWorkflowFactory,
            "my_custom_agent": MyCustomAgentWorkflowFactory,
        }
        for factory_class in self._factory_classes.values():
            self._validate_factory_class(factory_class)

    @staticmethod
    def _validate_factory_class(factory_class: type[object]) -> None:
        if not isinstance(factory_class, type) or not issubclass(factory_class, BaseWorkflowFactory):
            raise TypeError(
                "Workflow registry only accepts BaseWorkflowFactory subclasses, "
                f"got: {factory_class!r}"
            )

    def register(self, workflow_name: str, factory_class: Type[BaseWorkflowFactory]) -> None:
        """Register or overwrite a workflow factory mapping."""
        self._validate_factory_class(factory_class)
        self._factory_classes[workflow_name.strip().lower()] = factory_class

    def resolve(self, workflow_name: str) -> BaseWorkflowFactory:
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
