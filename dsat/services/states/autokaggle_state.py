# dsat/services/states/autokaggle_state.py

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from dsat.models.formats import TaskContract


class AttemptMemory(BaseModel):
    """Stores the memory of a single attempt within a phase."""
    attempt_number: int
    plan: str
    code: str
    execution_output: str
    execution_error: Optional[str]
    validation_result: Dict[str, Any]
    review_score: float
    review_suggestion: str


class PhaseMemory(BaseModel):
    """Stores the history of all attempts for a single successful phase."""
    phase_goal: str
    attempts: List[AttemptMemory] = Field(default_factory=list)
    final_report: str = ""
    is_successful: bool = False
    # Keep track of artifacts produced *in this phase*. Paths are relative to the sandbox workdir.
    output_artifacts: Dict[str, str] = Field(default_factory=dict, description="Mapping of artifact filenames to their descriptions.")


class AutoKaggleState(BaseModel):
    """Manages the entire state of a dynamic AutoKaggle workflow run."""
    contract: TaskContract
    dynamic_phases: List[str] = Field(default_factory=list)
    phase_history: List[PhaseMemory] = Field(default_factory=list)
    io_instructions: str = Field(default="", description="Standardized I/O instructions for the agents.")
    full_task_description: str = Field(
        description="The original, complete task description including the data analysis report from DataAnalyzer."
    )
    # The central registry for all artifacts created during the run.
    # This provides state continuity between phases.
    # Maps artifact filename to a description.
    global_artifacts: Dict[str, str] = Field(default_factory=dict)