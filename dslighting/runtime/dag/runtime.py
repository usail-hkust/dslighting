"""Dynamic DAG runtime with dependency-aware scheduling."""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from typing import Any, Deque, Dict, List, Optional, Set, Tuple

from dslighting.runtime.dag.actor import WorkflowActor
from dslighting.runtime.dag.dispatch import NodeDispatcher
from dslighting.runtime.dag.reducer import Reducer
from dslighting.runtime.dag.types import DagRunSummary, DagRuntimeOptions, NodeResult, OpNode

logger = logging.getLogger(__name__)


class BaseDagRuntime(ABC):
    """Abstract base class for DAG runtime implementations.

    This class uses the template method pattern to define the core execution
    loop while allowing subclasses to customize specific behaviors through
    hook methods.
    """

    def __init__(
        self,
        *,
        options: Optional[DagRuntimeOptions] = None,
        dispatcher: Optional[NodeDispatcher] = None,
    ):
        self.options = (options or DagRuntimeOptions()).normalize()
        self.dispatcher = dispatcher or NodeDispatcher()

        self._nodes: Dict[str, OpNode] = {}
        self._indegree: Dict[str, int] = {}
        self._children: Dict[str, Set[str]] = defaultdict(set)
        self._results: Dict[str, NodeResult] = {}
        self._attempts: Dict[str, int] = defaultdict(int)
        self._ready: Deque[str] = deque()
        self._created_seq: Dict[str, int] = {}
        self._seq_counter = 0

        # Cancellation support
        self._cancel_requested = False
        self._cancel_reason: Optional[str] = None

        # Track running tasks for cleanup
        self._running_tasks: Dict[str, asyncio.Task[NodeResult]] = {}

    async def __aenter__(self) -> "BaseDagRuntime":
        """Async context manager entry for resource setup."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager for graceful cleanup."""
        await self.shutdown()

    async def shutdown(self, reason: str = "user_requested") -> None:
        """Gracefully shutdown the runtime.

        Cancels all running tasks and waits for cleanup.

        Args:
            reason: The reason for shutdown (default: "user_requested")
        """
        self._cancel_requested = True
        self._cancel_reason = reason

        # Cancel all running tasks
        if self._running_tasks:
            logger.info(f"Cancelling {len(self._running_tasks)} running tasks during shutdown")

            # Cancel all tasks
            for task in self._running_tasks.values():
                if not task.done():
                    task.cancel()

            # Wait for all tasks to complete cancellation
            if self._running_tasks:
                await asyncio.wait(
                    set(self._running_tasks.values()),
                    timeout=5.0,
                    return_when=asyncio.ALL_COMPLETED
                )

            # Clear the tasks dictionary
            self._running_tasks.clear()

    def request_cancellation(self, reason: Optional[str] = None) -> None:
        """Request graceful cancellation of the runtime.

        Args:
            reason: Optional reason for cancellation
        """
        self._cancel_requested = True
        self._cancel_reason = reason

    async def run_actor(self, actor: WorkflowActor) -> DagRunSummary:
        """Execute nodes emitted by actor until completion.

        This is the template method that defines the core execution loop.
        Subclasses can override hook methods to customize behavior.
        """
        started = time.perf_counter()

        self._reset_runtime_state()

        reducer: Reducer = actor.reducer()
        actor_state = actor.initial_state()
        actor_done = False

        initial_nodes = actor.initial_nodes()
        self._register_nodes(initial_nodes)

        running_tasks = self._running_tasks
        running_tasks.clear()
        task_to_node: Dict[asyncio.Task[NodeResult], str] = {}

        last_error: Optional[str] = None

        # Hook for subclass initialization before main loop
        await self._before_main_loop(actor, reducer, actor_state)

        while True:
            if self._cancel_requested:
                if not last_error:
                    cancel_reason = self._cancel_reason or "cancellation requested"
                    last_error = f"DAG runtime cancelled: {cancel_reason}"

                if not running_tasks:
                    self._mark_remaining_nodes_cancelled()
                    break

            # Start new tasks up to max_inflight limit
            while (
                not self._cancel_requested
                and self._ready
                and len(running_tasks) < self.options.max_inflight_nodes
            ):
                node_id = self._pop_ready_node_id()
                if not node_id:
                    break

                # Hook for preprocessing inputs (e.g., prefetch in pipeline runtime)
                missing_error, resolved_inputs = await self._preprocess_inputs(node_id)

                node = self._nodes[node_id]
                if node_id in self._results:
                    continue

                if missing_error:
                    result = NodeResult(
                        node_id=node.node_id,
                        task_id=node.task_id,
                        status="failed",
                        outputs={},
                        error=missing_error,
                        attempt=self._attempts[node_id],
                    )
                    actor_state = self._handle_completed_node_result(
                        reducer=reducer,
                        actor_state=actor_state,
                        result=result,
                    )
                    new_nodes, is_done = actor.on_node_result(result)
                    actor_done = actor_done or is_done
                    self._register_nodes(new_nodes)
                    if result.error:
                        last_error = result.error
                    continue

                node_timeout = node.timeout_seconds
                if node_timeout is None:
                    node_timeout = (self.options.node_timeout_by_op or {}).get(node.op_type)

                task = asyncio.create_task(
                    self.dispatcher.execute(
                        node,
                        resolved_inputs=resolved_inputs,
                        attempt=self._attempts[node_id],
                        timeout=node_timeout,
                    )
                )
                running_tasks[node_id] = task
                task_to_node[task] = node_id

                # Hook after scheduling a task
                await self._after_schedule_task(actor, running_tasks)

            if not running_tasks:
                if actor_done:
                    break
                if not self._ready:
                    if self._has_unresolved_nodes():
                        last_error = "DAG runtime deadlock: unresolved nodes remaining with unsatisfied dependencies"
                    break

            if not running_tasks:
                continue

            done, _ = await asyncio.wait(
                set(running_tasks.values()),
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in done:
                node_id = task_to_node.pop(task)
                running_tasks.pop(node_id, None)

                try:
                    result = task.result()
                except Exception as exc:  # pragma: no cover - defensive
                    result = NodeResult(
                        node_id=node_id,
                        task_id=self._nodes[node_id].task_id,
                        status="failed",
                        outputs={},
                        error=f"{exc.__class__.__name__}: {exc}",
                        attempt=self._attempts[node_id],
                    )

                node = self._nodes[node_id]
                if result.status == "failed" and self._attempts[node_id] < max(0, int(node.max_retries)):
                    self._attempts[node_id] += 1
                    self._ready.append(node_id)
                    continue

                actor_state = self._handle_completed_node_result(
                    reducer=reducer,
                    actor_state=actor_state,
                    result=result,
                )

                new_nodes, is_done = actor.on_node_result(result)
                actor_done = actor_done or is_done
                self._register_nodes(new_nodes)

                if result.error:
                    last_error = result.error

                # Hook after task completion (for scheduling prefetches, etc.)
                await self._after_task_complete(actor, new_nodes)

        duration = time.perf_counter() - started

        success_count = sum(1 for r in self._results.values() if r.status == "success")
        failed_count = sum(1 for r in self._results.values() if r.status == "failed")
        cancelled_count = sum(1 for r in self._results.values() if r.status == "cancelled")

        get_result = getattr(actor, "get_result", None)
        final_result = get_result() if callable(get_result) else None

        summary = DagRunSummary(
            task_id=getattr(actor, "task_id", "unknown_task"),
            total_nodes=len(self._nodes),
            successful_nodes=success_count,
            failed_nodes=failed_count,
            cancelled_nodes=cancelled_count,
            retries=sum(self._attempts.values()),
            duration_seconds=duration,
            actor_completed=actor_done,
            final_result=final_result,
            final_state=actor_state,
            last_error=last_error,
        )
        return summary

    def _mark_remaining_nodes_cancelled(self) -> None:
        """Mark all unresolved nodes as cancelled after cancellation is requested."""
        cancel_reason = self._cancel_reason or "cancellation requested"
        for node_id, node in self._nodes.items():
            if node_id in self._results:
                continue
            self._results[node_id] = NodeResult(
                node_id=node_id,
                task_id=node.task_id,
                status="cancelled",
                outputs={},
                error=cancel_reason,
                attempt=self._attempts.get(node_id, 0),
            )

    # --- Hook methods for subclass customization ---

    async def _before_main_loop(
        self,
        actor: WorkflowActor,
        reducer: Reducer,
        actor_state: Any,
    ) -> None:
        """Hook called before the main execution loop.

        Override in subclass to perform initialization (e.g., schedule prefetches).
        """
        pass

    async def _preprocess_inputs(self, node_id: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """Hook for preprocessing inputs before node execution.

        Override in subclass to provide cached inputs (e.g., from prefetch).

        Args:
            node_id: The node ID to preprocess inputs for

        Returns:
            Tuple of (error_message_or_None, resolved_inputs_dict)
        """
        node = self._nodes[node_id]
        return self._resolve_inputs(node)

    async def _after_schedule_task(
        self,
        actor: WorkflowActor,
        running_tasks: Dict[str, asyncio.Task[NodeResult]],
    ) -> None:
        """Hook called after scheduling a new task.

        Override in subclass for pipeline-specific operations.
        """
        pass

    async def _after_task_complete(
        self,
        actor: WorkflowActor,
        new_nodes: List[OpNode],
    ) -> None:
        """Hook called after a task completes.

        Override in subclass for pipeline-specific operations.
        """
        pass

    # --- Core state management methods (not template methods) ---

    def _reset_runtime_state(self) -> None:
        self._nodes.clear()
        self._indegree.clear()
        self._children.clear()
        self._results.clear()
        self._attempts.clear()
        self._ready.clear()
        self._created_seq.clear()
        self._seq_counter = 0

    def _register_nodes(self, nodes: List[OpNode]) -> None:
        for node in nodes:
            if node.node_id in self._nodes:
                logger.warning("Skip duplicate DAG node id: %s", node.node_id)
                continue

            self._nodes[node.node_id] = node
            self._created_seq[node.node_id] = self._seq_counter
            self._seq_counter += 1

            indegree = 0
            for parent_id in node.depends_on:
                self._children[parent_id].add(node.node_id)
                parent_result = self._results.get(parent_id)
                if parent_result is None or parent_result.status != "success":
                    indegree += 1

            self._indegree[node.node_id] = indegree
            if indegree == 0:
                self._ready.append(node.node_id)

    def _pop_ready_node_id(self) -> Optional[str]:
        if not self._ready:
            return None

        if self.options.ready_queue_policy == "fifo":
            return self._ready.popleft()

        candidates = list(self._ready)
        if self.options.ready_queue_policy == "lpt_backfill":
            chosen = max(
                candidates,
                key=lambda node_id: (
                    self._nodes[node_id].estimated_runtime_seconds or 0.0,
                    self._nodes[node_id].priority,
                    -self._created_seq[node_id],
                ),
            )
        else:  # priority
            chosen = max(
                candidates,
                key=lambda node_id: (
                    self._nodes[node_id].priority,
                    self._nodes[node_id].estimated_runtime_seconds or 0.0,
                    -self._created_seq[node_id],
                ),
            )

        self._ready.remove(chosen)
        return chosen

    def _resolve_inputs(self, node: OpNode) -> Tuple[Optional[str], Dict[str, Any]]:
        resolved: Dict[str, Any] = {}
        for binding in node.input_bindings:
            parent_result = self._results.get(binding.source_node_id)
            if parent_result is None:
                return (
                    f"Missing dependency result: {binding.source_node_id} for node {node.node_id}",
                    {},
                )
            if parent_result.status != "success":
                return (
                    f"Dependency {binding.source_node_id} status={parent_result.status} blocks node {node.node_id}",
                    {},
                )
            if binding.source_key not in parent_result.outputs:
                return (
                    f"Dependency output key '{binding.source_key}' missing in {binding.source_node_id}",
                    {},
                )
            resolved[binding.input_key] = parent_result.outputs[binding.source_key]
        return None, resolved

    def _handle_completed_node_result(
        self,
        *,
        reducer: Reducer,
        actor_state: Any,
        result: NodeResult,
    ) -> Any:
        self._results[result.node_id] = result

        try:
            next_state = reducer.apply(state=actor_state, node_result=result)
        except Exception as exc:
            logger.warning("Reducer apply failed for node %s: %s", result.node_id, exc)
            next_state = actor_state

        if result.status == "success":
            for child_id in self._children.get(result.node_id, set()):
                if child_id not in self._indegree:
                    continue
                self._indegree[child_id] = max(0, self._indegree[child_id] - 1)
                if self._indegree[child_id] == 0 and child_id not in self._results:
                    if child_id not in self._ready:
                        self._ready.append(child_id)
        return next_state

    def _has_unresolved_nodes(self) -> bool:
        for node_id in self._nodes.keys():
            if node_id not in self._results:
                return True
        return False


class DagRuntime(BaseDagRuntime):
    """Runtime that executes dynamically generated DAG nodes."""

    # Inherits all behavior from BaseDagRuntime
    pass
