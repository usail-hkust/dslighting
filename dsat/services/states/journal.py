# dsat/services/states/journal.py

"""
Implements JournalState, which manages a tree of solution attempts (Nodes).
This is the core state representation for Paradigm 2 (AIDE/AutoMind-style) search agents.
"""
import uuid
from functools import total_ordering
from typing import Optional, Any, List, Dict, Set

from pydantic import BaseModel, Field, ConfigDict

from dsat.common.typing import ExecutionResult
from dsat.utils.context import truncate_output
from dsat.services.states.base import State


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

    model_config = ConfigDict(
        # Note: json_encoders deprecated in Pydantic V2
        # Sets are now automatically serialized to lists
    )

class JournalState(State, BaseModel):
    """
    Manages the entire search tree (the "Journal") of solution nodes.
    Provides methods for appending nodes, traversing the tree, and selecting
    nodes based on different criteria (e.g., best, buggy).
    """
    nodes: Dict[str, Node] = Field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.nodes)

    def append(self, node: Node, parent: Optional[Node] = None):
        """Adds a new node to the journal, linking it to a parent if provided."""
        if parent:
            if parent.id not in self.nodes:
                 raise ValueError(f"Parent node with id {parent.id} not in journal.")
            node.parent_id = parent.id
            self.nodes[parent.id].children_ids.add(node.id)
        node.step = len(self)
        self.nodes[node.id] = node

    def get_node(self, node_id: str) -> Optional[Node]:
        """Retrieves a node by its ID."""
        return self.nodes.get(node_id)

    def get_best_node(self) -> Optional[Node]:
        """Finds the best-performing, non-buggy node in the entire journal."""
        good_nodes = [n for n in self.nodes.values() if not n.is_buggy]
        if not good_nodes:
            return None
        return max(good_nodes, key=lambda n: n.metric)

    def generate_summary(self, max_nodes: int = 3) -> str:
        """
        Creates a textual summary of successful past attempts for prompt context.
        MODIFIED: Now selects the `max_nodes` BEST performing successful attempts.
        """
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
