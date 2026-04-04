from __future__ import annotations

from dslighting.debug.context import debug_scope, get_effective_debug_context
from dslighting.debug.models import NodeDebugContext, RunDebugContext


def test_get_effective_debug_context_creates_implicit_run_context() -> None:
    context = get_effective_debug_context("session_1")
    assert context.run is not None
    assert context.run.session_id == "session_1"
    assert context.run.run_id.startswith("adhoc_")


def test_debug_scope_overrides_run_and_node_context() -> None:
    run = RunDebugContext(session_id="session_2", run_id="run_123", task_id="task_a", workflow_name="aide")
    node = NodeDebugContext(node_id="node_1", operator_name="planner", op_type="llm", node_attempt=2)

    with debug_scope(run=run, node=node):
        context = get_effective_debug_context("session_2")
        assert context.run == run
        assert context.node == node
