"""Workflow factory registry with lazy builtin resolution."""

from __future__ import annotations

from importlib import import_module
from typing import Dict, Type

from .base import BaseWorkflowFactory

FactoryTarget = Type[BaseWorkflowFactory] | tuple[str, str]

_BUILTIN_FACTORY_TARGETS: dict[str, FactoryTarget] = {
    "aide": ("dslighting.workflows.factory.builtin", "AIDEWorkflowFactory"),
    "automind": ("dslighting.workflows.factory.builtin", "AutoMindWorkflowFactory"),
    "dsagent": ("dslighting.workflows.factory.builtin", "DSAgentWorkflowFactory"),
    "data_interpreter": ("dslighting.workflows.factory.builtin", "DataInterpreterWorkflowFactory"),
    "autokaggle": ("dslighting.workflows.factory.builtin", "AutoKaggleWorkflowFactory"),
    "deepanalyze": ("dslighting.workflows.factory.builtin", "DeepAnalyzeWorkflowFactory"),
    "aflow": ("dslighting.workflows.factory.builtin", "AFlowWorkflowFactory"),
    "react": ("dslighting.workflows.factory.builtin", "ReActWorkflowFactory"),
    "my_custom_agent": ("dslighting.workflows.factory.builtin", "MyCustomAgentWorkflowFactory"),
}


class WorkflowRegistry:
    """Single source of truth for workflow->factory mapping."""

    def __init__(self, factory_classes: dict[str, FactoryTarget] | None = None) -> None:
        self._factory_classes: Dict[str, FactoryTarget] = dict(factory_classes or _BUILTIN_FACTORY_TARGETS)

    @staticmethod
    def _validate_factory_class(factory_class: type[object]) -> None:
        if not isinstance(factory_class, type) or not issubclass(factory_class, BaseWorkflowFactory):
            raise TypeError(
                "Workflow registry only accepts BaseWorkflowFactory subclasses, "
                f"got: {factory_class!r}"
            )

    @classmethod
    def _materialize_factory_class(cls, factory_target: FactoryTarget) -> Type[BaseWorkflowFactory]:
        if isinstance(factory_target, type):
            cls._validate_factory_class(factory_target)
            return factory_target

        module_name, attr_name = factory_target
        module = import_module(module_name)
        factory_class = getattr(module, attr_name)
        cls._validate_factory_class(factory_class)
        return factory_class

    def register(self, workflow_name: str, factory_class: Type[BaseWorkflowFactory]) -> None:
        """Register or overwrite a workflow factory mapping."""
        self._validate_factory_class(factory_class)
        self._factory_classes[workflow_name.strip().lower()] = factory_class

    def resolve(self, workflow_name: str) -> BaseWorkflowFactory:
        """Create the concrete workflow factory for a name."""
        normalized = (workflow_name or "").strip().lower()
        factory_target = self._factory_classes.get(normalized)
        if factory_target is None:
            available = ", ".join(sorted(self._factory_classes.keys()))
            raise ValueError(
                f"Unknown workflow '{workflow_name}'. Available workflows: [{available}]"
            )

        factory_class = self._materialize_factory_class(factory_target)
        self._factory_classes[normalized] = factory_class
        return factory_class()

    def list_workflows(self) -> list[str]:
        """List registered workflow names."""
        return sorted(self._factory_classes.keys())


default_workflow_registry = WorkflowRegistry()
