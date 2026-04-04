from __future__ import annotations

import pytest

from dslighting.core.interfaces import WorkflowFactoryInterface
from dslighting.workflows.factory.base import BaseWorkflowFactory
from dslighting.workflows.factory.registry import WorkflowRegistry, default_workflow_registry


EXPECTED_WORKFLOWS = {
    "aide",
    "automind",
    "dsagent",
    "data_interpreter",
    "autokaggle",
    "deepanalyze",
    "react",
    "aflow",
    "my_custom_agent",
}


def test_registry_resolves_all_builtins() -> None:
    names = set(default_workflow_registry.list_workflows())
    assert names == EXPECTED_WORKFLOWS

    for name in names:
        factory = default_workflow_registry.resolve(name)
        assert isinstance(factory, BaseWorkflowFactory)
        assert isinstance(factory, WorkflowFactoryInterface)


def test_registry_rejects_non_base_factory_subclass() -> None:
    class NotAFactory:
        pass

    registry = WorkflowRegistry()
    with pytest.raises(TypeError, match="BaseWorkflowFactory"):
        registry.register("bad", NotAFactory)  # type: ignore[arg-type]
