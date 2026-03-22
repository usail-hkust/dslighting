"""Node execution dispatch for DAG runtime.

This module provides the NodeDispatcher class for executing nodes in the DAG runtime.
The dispatcher is designed to be extensible - custom operator handlers can be registered
for different operator types (llm, sandbox, io, parse, workflow, custom).
"""

from __future__ import annotations

import asyncio
import inspect
import time
from typing import Any, Callable, Dict, Optional

from dslighting.debug import debug_scope
from dslighting.debug.models import NodeDebugContext
from dslighting.runtime.dag.types import NodeResult, OpNode


class NodeDispatcher:
    """Execute one node with resolved input bindings.

    The NodeDispatcher supports extensible operator handlers. By default, only
    'custom' operators (using payload.callable) are supported. To add support
    for other operator types, register a handler using register_handler().

    Example:
        dispatcher = NodeDispatcher()
        dispatcher.register_handler("llm", my_llm_handler)
    """

    def __init__(self, *, default_timeout: float = 300.0):
        """Initialize dispatcher.

        Args:
            default_timeout: Default timeout in seconds for node execution
        """
        self.default_timeout = default_timeout
        self._handlers: Dict[str, Callable[..., Any]] = {}

    def register_handler(self, op_type: str, handler: Callable[..., Any]) -> None:
        """Register a custom operator handler.

        Args:
            op_type: The operator type to handle (e.g., 'llm', 'sandbox', 'io', 'parse')
            handler: Async or sync callable that takes (node, resolved_inputs) and returns outputs dict
        """
        self._handlers[op_type] = handler

    def _get_handler(self, op_type: str) -> Optional[Callable[..., Any]]:
        """Get handler for the given operator type."""
        return self._handlers.get(op_type)

    async def execute(
        self,
        node: OpNode,
        *,
        resolved_inputs: Dict[str, Any],
        attempt: int = 0,
        timeout: Optional[float] = None,
    ) -> NodeResult:
        """Execute a node with optional timeout.

        Args:
            node: The node to execute
            resolved_inputs: Resolved input bindings
            attempt: Current retry attempt
            timeout: Optional override for node timeout
        """
        timeout_duration = timeout or node.timeout_seconds or self.default_timeout

        started_at = time.time()
        perf_start = time.perf_counter()
        node_context = NodeDebugContext(
            node_id=node.node_id,
            operator_name=node.operator_name,
            op_type=node.op_type,
            node_attempt=attempt,
        )

        with debug_scope(node=node_context):
            try:
                outputs = await asyncio.wait_for(
                    self._execute_node(node=node, resolved_inputs=resolved_inputs),
                    timeout=timeout_duration
                )

                ended_at = time.time()
                duration = time.perf_counter() - perf_start
                return NodeResult(
                    node_id=node.node_id,
                    task_id=node.task_id,
                    status="success",
                    outputs=outputs,
                    error=None,
                    metrics={"duration_seconds": round(duration, 4)},
                    attempt=attempt,
                    started_at=started_at,
                    ended_at=ended_at,
                )
            except asyncio.TimeoutError:
                ended_at = time.time()
                duration = time.perf_counter() - perf_start
                return NodeResult(
                    node_id=node.node_id,
                    task_id=node.task_id,
                    status="failed",
                    outputs={},
                    error=f"Node execution timed out after {timeout_duration}s",
                    metrics={"duration_seconds": round(duration, 4)},
                    attempt=attempt,
                    started_at=started_at,
                    ended_at=ended_at,
                )

    async def _execute_node(
        self,
        node: OpNode,
        resolved_inputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a node using the appropriate handler.

        Args:
            node: The node to execute
            resolved_inputs: Resolved input bindings

        Returns:
            Outputs dictionary

        Raises:
            ValueError: If no handler is registered for the operator type
        """
        handler = self._get_handler(node.op_type)
        if handler is not None:
            # Use registered custom handler
            return await self._run_custom_handler(handler, node, resolved_inputs)

        # Fall back to built-in custom callable handler
        return await self._run_custom_callable(node, resolved_inputs)

    async def _run_custom_handler(
        self,
        handler: Callable[..., Any],
        node: OpNode,
        resolved_inputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run a registered custom handler."""
        payload = dict(node.payload or {})
        kwargs = dict(payload.get("kwargs") or {})
        kwargs.update(resolved_inputs)

        if inspect.iscoroutinefunction(handler):
            value = await handler(node, **kwargs)
        else:
            value = handler(node, **kwargs)
            if inspect.isawaitable(value):
                value = await value

        if isinstance(value, dict):
            return value
        return {"value": value}

    async def _run_custom_callable(
        self,
        node: OpNode,
        resolved_inputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run a custom callable from the node payload.

        This is the built-in handler for 'custom' operator types.
        """
        payload = dict(node.payload or {})
        fn = payload.get("callable")
        if fn is None:
            raise ValueError(
                f"Unsupported operator type '{node.op_type}' and missing payload.callable. "
                f"Register a handler using register_handler('{node.op_type}', handler)"
            )

        kwargs = dict(payload.get("kwargs") or {})
        kwargs.update(resolved_inputs)

        if inspect.iscoroutinefunction(fn):
            value = await fn(**kwargs)
        else:
            value = fn(**kwargs)
            if inspect.isawaitable(value):
                value = await value

        if isinstance(value, dict):
            return value
        return {"value": value}
