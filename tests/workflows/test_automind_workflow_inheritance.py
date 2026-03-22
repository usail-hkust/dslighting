from __future__ import annotations

from dslighting.workflows.search.aide_workflow import AIDEWorkflow
from dslighting.workflows.search.automind_workflow import AutoMindWorkflow


def test_automind_explicitly_inherits_aide_workflow() -> None:
    assert issubclass(AutoMindWorkflow, AIDEWorkflow)


def test_automind_init_uses_aide_contract() -> None:
    operators = {
        "execute": object(),
        "generate": object(),
        "review": object(),
    }
    services = {
        "state": object(),
        "sandbox": object(),
        "llm": object(),
        "workspace": object(),
        "vdb": None,
    }

    workflow = AutoMindWorkflow(
        operators=operators,
        services=services,
        agent_config={},
        benchmark=None,
    )

    assert isinstance(workflow, AIDEWorkflow)
    assert workflow.state is services["state"]
    assert workflow.execute_op is operators["execute"]
    assert workflow.generate_op is operators["generate"]
    assert workflow.review_op is operators["review"]
    assert workflow.vdb_service is None
    assert workflow.context_manager.llm_service is services["llm"]
    assert callable(getattr(workflow, "solve"))
    assert callable(getattr(workflow, "build_actor"))
    assert callable(getattr(workflow, "_select_node_to_expand"))
