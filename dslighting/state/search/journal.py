"""
Journal state for search-based workflows.

Manages a tree of solution attempts (Nodes) for AIDE/AutoMind-style agents.
"""
import uuid
import threading
import json
from contextlib import contextmanager
from datetime import datetime
from functools import total_ordering
from typing import TYPE_CHECKING, Optional, Any, List, Dict, Set

if TYPE_CHECKING:
    from dslighting.core.types import ReviewResult

from pydantic import BaseModel, Field, ConfigDict

from dslighting.utils.typing import ExecutionResult
from dslighting.state.context import truncate_output


# Note: Removed State inheritance since BaseModel already provides the necessary
# interface (model_dump, model_validate, etc.) and JournalState does not implement
# the full State abstract interface (get, set, delete, clear, snapshot, restore).


def maximize_from_lower_is_better(lower_is_better: Optional[bool]) -> bool:
    """Convert lower-is-better semantics into MetricValue.maximize.

    Unknown direction defaults to maximize=True so search behavior remains stable
    without pretending the metric is minimize-oriented.
    """
    return False if lower_is_better is True else True

@total_ordering
class MetricValue(BaseModel):
    """
    Represents a comparable metric that can be configured for maximization or minimization.
    A value of None is considered worse than any numeric value.
    """
    value: Optional[float]
    maximize: bool = True

    def __gt__(self, other: "MetricValue") -> bool:
        if self.value is None:
            return False
        if other.value is None:
            return True
        return (self.value > other.value) if self.maximize else (self.value < other.value)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, MetricValue) and self.value == other.value

    def __str__(self) -> str:
        direction = "↑" if self.maximize else "↓"
        val_str = f"{self.value:.4f}" if self.value is not None else "N/A"
        return f"Metric{direction}({val_str})"

class Node(BaseModel):
    """
    Represents a single attempt or node in the solution search tree.
    Each node contains the code, plan, execution results, and review analysis.
    """
    code: str
    plan: str

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    parent_id: Optional[str] = None
    children_ids: Set[str] = Field(default_factory=set)

    # Execution Results
    term_out: str = ""
    exec_time: float = 0.0
    exc_type: Optional[str] = None
    exec_metadata: Dict[str, Any] = Field(default_factory=dict)

    # LLM Recordings
    task_context: Dict[str, Any] = Field(default_factory=dict)
    generate_prompt: Optional[str] = None
    llm_generate: Optional[Dict[str, Any]] = None
    review_context: Optional[Dict[str, Any]] = None
    llm_review: Optional[Dict[str, Any]] = None

    # Review Results
    analysis: str = ""
    metric: MetricValue = Field(default_factory=lambda: MetricValue(value=None))
    is_buggy: bool = True
    step: int = -1

    # Artifact paths
    code_artifact_path: Optional[str] = None
    final_submission_path: Optional[str] = None

    def absorb_exec_result(self, exec_result: ExecutionResult):
        """Updates the node with the results from a sandbox execution."""
        stdout = exec_result.stdout or ""
        stderr = exec_result.stderr or ""
        combined_output = f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}".strip()
        self.term_out = truncate_output(combined_output)
        self.exc_type = exec_result.exc_type
        self.is_buggy = not exec_result.success
        self.exec_metadata = exec_result.metadata or {}

    def absorb_review(self, review: "ReviewResult", task_context: Optional[Dict[str, Any]] = None) -> None:
        """Merges a ReviewResult into this node.

        Metric direction (lower_is_better) is sourced from task_context when
        available, falling back to the review's own field. This ensures direction
        is driven by the task spec rather than per-review LLM inference.

        Args:
            review: Structured result from the review operator.
            task_context: Optional dict, may carry 'lower_is_better' (bool) and
                          'metric_name' (str) set by the task runner.
        """
        self.analysis = review.summary
        self.is_buggy = review.is_buggy
        ctx = task_context or {}
        lower_is_better = ctx.get("lower_is_better")
        if not isinstance(lower_is_better, bool):
            lower_is_better = review.lower_is_better if isinstance(review.lower_is_better, bool) else None
        self.metric = MetricValue(
            value=review.metric_value,
            maximize=maximize_from_lower_is_better(lower_is_better),
        )

    model_config = ConfigDict(
        # Note: json_encoders deprecated in Pydantic V2
        # Sets are now automatically serialized to lists
    )

class JournalState(BaseModel):
    """
    Manages the entire search tree (the "Journal") of solution nodes.
    Provides methods for appending nodes, traversing the tree, and selecting
    nodes based on different criteria (e.g., best, buggy).

    Note: This class implements State-like interface (snapshot/restore) compatible
    with Pydantic serialization. The design intentionally avoids full State ABC
    inheritance to prevent serialization conflicts between BaseModel's model_dump
    and State's abstract snapshot/restore methods.

    修复：添加 State 接口兼容实现 + 线程安全保护，支持并发节点访问
    """
    nodes: Dict[str, Node] = Field(default_factory=dict)
    created_timestamp: datetime = Field(default_factory=datetime.now)

    def __init__(self, **data):
        super().__init__(**data)
        self._lock = threading.RLock()

    # === State-like Interface (compatible with State ABC) ===
    # These methods provide compatibility with the State interface without
    # inheriting from ABC, avoiding serialization conflicts.

    @property
    def created_at(self) -> datetime:
        """When this JournalState was created."""
        return self.created_timestamp

    def snapshot(self) -> bytes:
        """Create a checkpoint snapshot using Pydantic serialization.

        Returns:
            Serialized state data as bytes (JSON format).
        """
        with self._atomic_operation():
            data = self.model_dump()
            return json.dumps(data, indent=2, default=str).encode("utf-8")

    def restore(self, data: bytes) -> bool:
        """Restore from checkpoint snapshot.

        Args:
            data: Serialized state data from snapshot() call.

        Returns:
            True if restoration was successful, False otherwise.
        """
        try:
            decoded = json.loads(data.decode("utf-8"))
            restored = self.model_validate(decoded)
            self.nodes = restored.nodes
            self.created_timestamp = restored.created_timestamp
            return True
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            return False

    # === Key-value interface (for State compatibility) ===
    # JournalState treats node_id as key and Node as value.

    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """Get a node by ID (State interface compatibility).

        Args:
            key: The node ID.
            default: Default value if node not found.

        Returns:
            The Node or default if not found.
        """
        with self._atomic_operation():
            node = self.nodes.get(key)
            return node if node is not None else default

    def set(self, key: str, value: Any) -> None:
        """Set a node by ID (State interface compatibility).

        Args:
            key: The node ID.
            value: The Node to store.
        """
        with self._atomic_operation():
            if not isinstance(value, Node):
                raise TypeError(f"Value must be Node, got {type(value)}")
            self.nodes[key] = value

    def delete(self, key: str) -> bool:
        """Delete a node by ID (State interface compatibility).

        Args:
            key: The node ID to delete.

        Returns:
            True if node existed and was deleted, False otherwise.
        """
        with self._atomic_operation():
            if key in self.nodes:
                del self.nodes[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all nodes (State interface compatibility)."""
        with self._atomic_operation():
            self.nodes.clear()

    @contextmanager
    def _atomic_operation(self):
        """Context manager for atomic state operations."""
        with self._lock:
            yield

    def __len__(self) -> int:
        with self._atomic_operation():
            return len(self.nodes)

    def append(self, node: Node, parent: Optional[Node] = None):
        """Adds a new node to the journal, linking it to a parent if provided.

        修复：线程安全的 append 操作
        """
        with self._atomic_operation():
            if parent:
                if parent.id not in self.nodes:
                     raise ValueError(f"Parent node with id {parent.id} not in journal.")
                node.parent_id = parent.id
                self.nodes[parent.id].children_ids.add(node.id)
            node.step = len(self)
            self.nodes[node.id] = node

    def get_node(self, node_id: str) -> Optional[Node]:
        """Retrieves a node by its ID.

        修复：线程安全的节点读取
        """
        with self._atomic_operation():
            return self.nodes.get(node_id)

    def get_best_node(self) -> Optional[Node]:
        """Finds the best-performing, non-buggy node in the entire journal.

        修复：线程安全的最佳节点查找
        """
        with self._atomic_operation():
            good_nodes = [n for n in self.nodes.values() if not n.is_buggy]
            if not good_nodes:
                return None
            return max(good_nodes, key=lambda n: n.metric)

    def generate_summary(self, max_nodes: int = 3) -> str:
        """
        Creates a textual summary of successful past attempts for prompt context.
        MODIFIED: Now selects the `max_nodes` BEST performing successful attempts.

        修复：线程安全的摘要生成
        """
        with self._atomic_operation():
            good_nodes = sorted(
                [n for n in self.nodes.values() if not n.is_buggy and n.metric.value is not None],
                key=lambda x: x.metric,
                reverse=True  # MetricValue handles > comparison correctly, so reverse=True gets the best
            )
            if not good_nodes:
                return "No successful solutions have been found yet."

            # Apply windowing: take the top `max_nodes`
            selected_nodes = good_nodes[:max_nodes]

            summary_parts = []
            for n in selected_nodes:
                summary_part = (
                    f"Attempt #{n.step}:\n"
                    f"Plan: {n.plan}\n"
                    f"Result Analysis: {n.analysis}\n"
                    f"Validation Metric: {n.metric}\n"
                )
                summary_parts.append(summary_part)

            prefix = ""
            if len(good_nodes) > len(selected_nodes):
                prefix = f"[... {len(good_nodes) - len(selected_nodes)} other successful attempts exist ...]\n"

            return prefix + "Here is a summary of the best performing attempts:\n" + "\n------------------\n".join(summary_parts)
