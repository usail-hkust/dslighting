from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# --- Pydantic Models for Operator Outputs ---
# These models are now used with LLMService.call_with_json

class ReviewResult(BaseModel):
    """Structured result from the ReviewOperator."""
    is_buggy: bool = Field(..., description="True if the execution failed or has a clear bug, otherwise False.")
    summary: str = Field(..., description="If buggy, a proposal to fix the bug. If successful, a summary of empirical findings.")
    metric_value: Optional[float] = Field(..., description="A quantitative measure of success based on the task requirements. Null if the task does not define a quantitative metric or if it cannot be determined.")
    lower_is_better: bool = Field(default=True, description="True if a lower metric is better (e.g., RMSE), False if higher is better (e.g., Accuracy).")

class Task(BaseModel):
    """A single task within a larger plan."""
    task_id: str = Field(..., description="Unique identifier for a task, e.g., '1', '2.1'.")
    instruction: str = Field(..., description="Clear, concise instruction for what to do in this task.")
    dependent_task_ids: List[str] = Field(default_factory=list, description="List of task_ids this task depends on.")

class Plan(BaseModel):
    """A structured plan consisting of multiple tasks."""
    tasks: List[Task] = Field(..., description="A list of tasks to achieve the overall goal.")


class ComplexityScore(BaseModel):
    """Structured result from the ComplexityScorerOperator."""
    complexity: int = Field(..., description="An integer score from 1 to 5 representing the plan's complexity.", ge=1, le=5)
    justification: str = Field(..., description="A brief justification for the assigned score.")

class DecomposedPlan(BaseModel):
    """A structured plan decomposed into sequential tasks, used for stepwise execution."""
    tasks: List[Task] = Field(..., description="A list of sequential tasks to achieve the overall goal.")



class FileArtifact(BaseModel):
    filename: str = Field(description="The name of the file, e.g., 'input_data.dat', 'image_001.png', or 'results.json'.")
    description: str = Field(description="A brief description of the file's purpose and content.")


class TaskContract(BaseModel):
    task_goal: str = Field(description="A clear, one-sentence summary of the main objective.")
    task_type: str = Field(description="A high-level categorization derived from the task goal (e.g., 'Classification', 'Generation', 'Simulation', 'Data Processing').")
    input_files: List[FileArtifact] = Field(description="A list of all input files required to complete the task.")
    output_files: List[FileArtifact] = Field(description="A list of all final output files that must be generated.")
    evaluation_metric: str = Field(description="The primary metric for evaluating the success of the output, e.g., 'Accuracy Score', 'ROUGE Score', 'Visual Appeal'.")

class StepPlan(BaseModel):
    """A detailed plan for a single phase and the artifacts it's expected to create."""
    plan: str = Field(description="A detailed, step-by-step natural language plan for the developer.")
    input_artifacts: List[str] = Field(default_factory=list, description="A list of artifact filenames from the global state that this plan will use as input (e.g., ['train_preprocessed.csv', 'scaler.joblib']).")
    output_files: List[str] = Field(description="A list of filenames that the plan is expected to generate (e.g., ['model.pkl', 'submission.csv']).")