"""Core types for dynamic DAG runtime."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Literal


OpType = Literal["llm", "sandbox", "io", "parse", "custom", "workflow"]
NodeStatus = Literal["pending", "ready", "running", "success", "failed", "cancelled"]


@dataclass(frozen=True)
class NodeInputBinding:
    """Map one downstream input key to an upstream node output key."""

    input_key: str
    source_node_id: str
    source_key: str


@dataclass
class OpNode:
    """A runtime operator node in the DAG."""

    node_id: str
    task_id: str
    op_type: OpType
    operator_name: str
    depends_on: List[str] = field(default_factory=list)
    input_bindings: List[NodeInputBinding] = field(default_factory=list)
    payload: Dict[str, Any] = field(default_factory=dict)
    resource_profile: Dict[str, Any] = field(default_factory=dict)
    state_version: int = 0
    priority: int = 0
    max_retries: int = 0
    estimated_runtime_seconds: Optional[float] = None
    timeout_seconds: Optional[float] = None  # Per-node timeout override
    created_at: float = field(default_factory=time.time)


@dataclass
class NodeResult:
    """Node execution result."""

    node_id: str
    task_id: str
    status: NodeStatus
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    attempt: int = 0
    started_at: Optional[float] = None
    ended_at: Optional[float] = None


@dataclass
class WorkflowGraphSpec:
    """Declarative workflow graph specification."""

    task_id: str
    initial_nodes: List[OpNode] = field(default_factory=list)
    initial_state: Any = field(default_factory=dict)


@dataclass
class GraphDelta:
    """Dynamic graph updates after one node result."""

    new_nodes: List[OpNode] = field(default_factory=list)
    done: bool = False
    final_result: Any = None


@dataclass
class DagRuntimeOptions:
    """Runtime options for DAG scheduler."""

    enabled: bool = False
    max_inflight_nodes: int = 256
    node_timeout_seconds: float = 300.0
    ready_queue_policy: str = "priority"  # fifo | priority | lpt_backfill
    llm_global_max_concurrency: Optional[int] = None
    llm_model_quotas: Dict[str, int] = field(default_factory=dict)
    enable_speculative_branches: bool = False
    dag_mode: str = "coarse"  # coarse | fine
    enable_debug_branch: bool = False
    max_retries: int = 3

    # Declarative DAG controls
    dag_actor_strategy: str = "coarse"  # coarse | declarative
    runtime_engine: str = "standard"  # standard | pipeline
    parallel_drafts: int = 1
    branch_budget: Optional[int] = None
    node_timeout_policy: str = "fixed"  # fixed | adaptive
    node_timeout_by_op: Dict[str, float] = field(default_factory=dict)

    def normalize(self) -> "DagRuntimeOptions":
        try:
            self.max_inflight_nodes = max(1, int(self.max_inflight_nodes))
        except (TypeError, ValueError):
            self.max_inflight_nodes = 256

        try:
            self.node_timeout_seconds = float(self.node_timeout_seconds)
            if self.node_timeout_seconds <= 0:
                raise ValueError
        except (TypeError, ValueError):
            self.node_timeout_seconds = 300.0

        policy = str(self.ready_queue_policy or "priority").strip().lower()
        if policy not in {"fifo", "priority", "lpt_backfill"}:
            policy = "priority"
        self.ready_queue_policy = policy

        if self.llm_global_max_concurrency is not None:
            try:
                self.llm_global_max_concurrency = max(1, int(self.llm_global_max_concurrency))
            except (TypeError, ValueError):
                self.llm_global_max_concurrency = None

        normalized_quotas: Dict[str, int] = {}
        for model, value in (self.llm_model_quotas or {}).items():
            try:
                cap = int(value)
            except (TypeError, ValueError):
                continue
            if cap > 0:
                normalized_quotas[str(model)] = cap
        self.llm_model_quotas = normalized_quotas

        actor_strategy = str(self.dag_actor_strategy or "coarse").strip().lower()
        if actor_strategy not in {"coarse", "declarative"}:
            actor_strategy = "coarse"
        self.dag_actor_strategy = actor_strategy

        runtime_engine = str(self.runtime_engine or "standard").strip().lower()
        if runtime_engine not in {"standard", "pipeline"}:
            runtime_engine = "standard"
        self.runtime_engine = runtime_engine

        try:
            self.parallel_drafts = max(1, int(self.parallel_drafts))
        except (TypeError, ValueError):
            self.parallel_drafts = 1

        if self.branch_budget is not None:
            try:
                budget = int(self.branch_budget)
                self.branch_budget = budget if budget > 0 else None
            except (TypeError, ValueError):
                self.branch_budget = None

        timeout_policy = str(self.node_timeout_policy or "fixed").strip().lower()
        if timeout_policy not in {"fixed", "adaptive"}:
            timeout_policy = "fixed"
        self.node_timeout_policy = timeout_policy

        normalized_timeout_by_op: Dict[str, float] = {}
        for op_type, value in (self.node_timeout_by_op or {}).items():
            try:
                timeout = float(value)
            except (TypeError, ValueError):
                continue
            if timeout > 0:
                normalized_timeout_by_op[str(op_type)] = timeout
        self.node_timeout_by_op = normalized_timeout_by_op

        return self


@dataclass
class DagRunSummary:
    """Summary of a DAG run for one task."""

    task_id: str
    total_nodes: int = 0
    successful_nodes: int = 0
    failed_nodes: int = 0
    cancelled_nodes: int = 0
    retries: int = 0
    duration_seconds: float = 0.0
    actor_completed: bool = False
    final_result: Any = None
    final_state: Any = None
    last_error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.actor_completed and self.failed_nodes == 0 and self.cancelled_nodes == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "total_nodes": self.total_nodes,
            "successful_nodes": self.successful_nodes,
            "failed_nodes": self.failed_nodes,
            "cancelled_nodes": self.cancelled_nodes,
            "retries": self.retries,
            "duration_seconds": round(float(self.duration_seconds), 4),
            "actor_completed": self.actor_completed,
            "final_result": self.final_result,
            "final_state": self.final_state,
            "success": self.success,
            "last_error": self.last_error,
        }
