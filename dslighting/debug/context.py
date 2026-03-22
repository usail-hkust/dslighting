"""Context propagation for debug observability."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Iterator
from uuid import uuid4

from dslighting.debug.models import LLMCallContext, NodeDebugContext, RunDebugContext

_run_context_var: ContextVar[RunDebugContext | None] = ContextVar("dslighting_debug_run_context", default=None)
_node_context_var: ContextVar[NodeDebugContext | None] = ContextVar("dslighting_debug_node_context", default=None)
_llm_context_var: ContextVar[LLMCallContext | None] = ContextVar("dslighting_debug_llm_context", default=None)
_implicit_run_context_var: ContextVar[RunDebugContext | None] = ContextVar(
    "dslighting_debug_implicit_run_context", default=None
)


@dataclass(frozen=True)
class DebugContextState:
    run: RunDebugContext | None = None
    node: NodeDebugContext | None = None
    llm: LLMCallContext | None = None


def get_current_debug_context() -> DebugContextState:
    return DebugContextState(
        run=_run_context_var.get(),
        node=_node_context_var.get(),
        llm=_llm_context_var.get(),
    )


def get_effective_debug_context(session_id: str | None = None) -> DebugContextState:
    run = _run_context_var.get()
    if run is None and session_id:
        implicit = _implicit_run_context_var.get()
        if implicit is None or implicit.session_id != session_id:
            implicit = RunDebugContext(
                session_id=session_id,
                run_id=f"adhoc_{uuid4().hex[:8]}",
                workflow_name="adhoc",
            )
            _implicit_run_context_var.set(implicit)
        run = implicit
    return DebugContextState(
        run=run,
        node=_node_context_var.get(),
        llm=_llm_context_var.get(),
    )


def push_run_context(run: RunDebugContext) -> Token[RunDebugContext | None]:
    return _run_context_var.set(run)


def push_node_context(node: NodeDebugContext) -> Token[NodeDebugContext | None]:
    return _node_context_var.set(node)


def push_llm_context(llm: LLMCallContext) -> Token[LLMCallContext | None]:
    return _llm_context_var.set(llm)


def pop_context(token: Token[object]) -> None:
    token.var.reset(token)


@contextmanager
def debug_scope(
    *,
    run: RunDebugContext | None = None,
    node: NodeDebugContext | None = None,
    llm: LLMCallContext | None = None,
) -> Iterator[None]:
    tokens: list[Token[object]] = []
    try:
        if run is not None:
            tokens.append(push_run_context(run))
        if node is not None:
            tokens.append(push_node_context(node))
        if llm is not None:
            tokens.append(push_llm_context(llm))
        yield
    finally:
        for token in reversed(tokens):
            pop_context(token)
