"""Reducer interfaces for DAG actor state updates."""

from __future__ import annotations

from typing import Any, Dict, Protocol

from dslighting.runtime.dag.types import NodeResult


class Reducer(Protocol):
    """Reducer protocol for actor state transitions."""

    def apply(self, *, state: Any, node_result: NodeResult) -> Any:
        """Return next state after applying one node result."""


class CompactStateReducer:
    """Unified lightweight reducer for DAG runtime state updates.

    It updates the state in place and stores compact per-node traces by default,
    avoiding repeated full-dict copies and large output payload duplication.
    """

    TRACE_KEY = "__dag_node_trace__"

    def __init__(self, *, include_outputs: bool = False):
        self.include_outputs = bool(include_outputs)

    def apply(self, *, state: Any, node_result: NodeResult) -> Dict[str, Any]:
        next_state: Dict[str, Any]
        if isinstance(state, dict):
            next_state = state
        else:
            next_state = {}

        trace = next_state.get(self.TRACE_KEY)
        if not isinstance(trace, dict):
            trace = {}
            next_state[self.TRACE_KEY] = trace

        entry: Dict[str, Any] = {
            "status": node_result.status,
            "error": node_result.error,
            "metrics": dict(node_result.metrics),
            "attempt": node_result.attempt,
        }
        if self.include_outputs:
            entry["outputs"] = dict(node_result.outputs)

        trace[node_result.node_id] = entry
        return next_state
