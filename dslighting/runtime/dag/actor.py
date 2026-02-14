"""Actor protocol and default adapters for DAG runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Tuple

from dslighting.runtime.dag.reducer import CompactStateReducer, Reducer
from dslighting.runtime.dag.types import (
    GraphDelta,
    NodeResult,
    OpNode,
    WorkflowGraphSpec,
)


class WorkflowActor(Protocol):
    """Protocol for workflow-to-DAG adapter."""

    task_id: str

    def initial_nodes(self) -> List[OpNode]:
        """Return initial nodes to seed runtime execution."""

    def on_node_result(self, result: NodeResult) -> Tuple[List[OpNode], bool]:
        """Consume node result, optionally emit new nodes, and report completion."""

    def reducer(self) -> Reducer:
        """Return reducer used for actor state updates."""

    def initial_state(self) -> Any:
        """Return actor initial state value."""

    def get_result(self) -> Any:
        """Return final actor result."""


class BaseWorkflowActor(WorkflowActor):
    """Convenient base class for concrete actors."""

    def reducer(self) -> Reducer:
        return CompactStateReducer(include_outputs=False)

    def initial_state(self) -> Any:
        return {}

    def get_result(self) -> Any:
        return None


class DeclarativeWorkflowActor(BaseWorkflowActor):
    """Adapter for workflows exposing a declarative operator DAG contract."""

    def __init__(
        self,
        *,
        task_id: str,
        workflow: Any,
        description: str,
        io_instructions: str,
        data_dir: Path,
        output_path: Path,
        dag_options: Any = None,
    ):
        self.task_id = task_id
        self.workflow = workflow
        self.description = description
        self.io_instructions = io_instructions
        self.data_dir = data_dir
        self.output_path = output_path
        self.dag_options = dag_options

        self._done = False
        self._final_result: Any = None
        self._dag_state: Any = {}

        graph_spec = self._build_graph_spec()
        self._initial_nodes: List[OpNode] = list(graph_spec.initial_nodes or [])
        self._dag_state = graph_spec.initial_state

    def _build_graph_spec(self) -> WorkflowGraphSpec:
        build_graph = getattr(self.workflow, "build_operator_graph", None)
        if not callable(build_graph):
            raise ValueError(
                f"Workflow '{self.workflow.__class__.__name__}' does not implement build_operator_graph()"
            )

        kwargs = {
            "task_id": self.task_id,
            "description": self.description,
            "io_instructions": self.io_instructions,
            "data_dir": self.data_dir,
            "output_path": self.output_path,
            "dag_options": self.dag_options,
        }

        try:
            spec = build_graph(**kwargs)
        except TypeError:
            kwargs.pop("dag_options", None)
            spec = build_graph(**kwargs)

        if isinstance(spec, WorkflowGraphSpec):
            return spec

        if isinstance(spec, dict):
            return WorkflowGraphSpec(
                task_id=str(spec.get("task_id") or self.task_id),
                initial_nodes=list(spec.get("initial_nodes") or []),
                initial_state=spec.get("initial_state") if "initial_state" in spec else {},
            )

        raise TypeError(
            f"build_operator_graph() must return WorkflowGraphSpec or dict, got {type(spec).__name__}"
        )

    def initial_nodes(self) -> List[OpNode]:
        return list(self._initial_nodes)

    def initial_state(self) -> Any:
        return self._dag_state

    def on_node_result(self, result: NodeResult) -> Tuple[List[OpNode], bool]:
        if self._done:
            return [], True

        transition_fn = getattr(self.workflow, "on_operator_node_result", None)
        if not callable(transition_fn):
            self._done = True
            self._final_result = {
                "status": "failed",
                "error": (
                    f"Workflow '{self.workflow.__class__.__name__}' does not implement "
                    "on_operator_node_result()"
                ),
                "failed_node_id": result.node_id,
            }
            return [], True

        try:
            delta = transition_fn(result=result, dag_state=self._dag_state)
        except TypeError:
            # Backward compatible fallback for implementations without keyword-only params.
            delta = transition_fn(result, self._dag_state)

        if isinstance(delta, dict):
            delta = GraphDelta(
                new_nodes=list(delta.get("new_nodes") or delta.get("nodes") or []),
                done=bool(delta.get("done", False)),
                final_result=delta.get("final_result"),
            )
        elif not isinstance(delta, GraphDelta):
            raise TypeError(
                f"on_operator_node_result() must return GraphDelta or dict, got {type(delta).__name__}"
            )

        new_nodes = list(delta.new_nodes or [])
        if delta.done:
            self._done = True
            finalized_result: Any = None

            finalize_fn = getattr(self.workflow, "finalize_operator_graph", None)
            if callable(finalize_fn):
                try:
                    finalized_result = finalize_fn(
                        task_id=self.task_id,
                        dag_state=self._dag_state,
                    )
                except TypeError:
                    finalized_result = finalize_fn(self.task_id, self._dag_state)

            if delta.final_result is not None:
                self._final_result = delta.final_result
            else:
                self._final_result = finalized_result

        return new_nodes, self._done

    def get_result(self) -> Any:
        return self._final_result


class SolveWorkflowActor(BaseWorkflowActor):
    """Adapter that wraps `workflow.solve(...)` as one DAG node."""

    def __init__(
        self,
        *,
        task_id: str,
        workflow: Any,
        description: str,
        io_instructions: str,
        data_dir: Path,
        output_path: Path,
    ):
        self.task_id = task_id
        self.workflow = workflow
        self.description = description
        self.io_instructions = io_instructions
        self.data_dir = data_dir
        self.output_path = output_path
        self._completed = False
        self._final_result: Optional[NodeResult] = None

    @property
    def root_node_id(self) -> str:
        return f"{self.task_id}:workflow.solve:0"

    def initial_nodes(self) -> List[OpNode]:
        return [
            OpNode(
                node_id=self.root_node_id,
                task_id=self.task_id,
                op_type="workflow",
                operator_name="workflow.solve",
                depends_on=[],
                payload={
                    "callable": self.workflow.solve,
                    "kwargs": {
                        "description": self.description,
                        "io_instructions": self.io_instructions,
                        "data_dir": self.data_dir,
                        "output_path": self.output_path,
                    },
                },
                state_version=0,
                priority=0,
                max_retries=0,
            )
        ]

    def on_node_result(self, result: NodeResult) -> Tuple[List[OpNode], bool]:
        self._final_result = result
        self._completed = True
        return [], True

    def get_result(self) -> Any:
        if not self._final_result:
            return None
        return {
            "node_id": self._final_result.node_id,
            "status": self._final_result.status,
            "outputs": dict(self._final_result.outputs),
            "error": self._final_result.error,
        }
