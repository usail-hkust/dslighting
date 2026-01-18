from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Dict, Any

# Define a controlled vocabulary for task types.
# The framework will choose appropriate TaskHandler based on this type.
TaskType = Literal["kaggle", "qa", "code", "datasci", "open_ended"]

# Define execution modes.
# 'standard_ml': Strict evaluation against ground truth (e.g., RMSE, Accuracy).
# 'open_ended': Exploratory tasks evaluated by LLM judge or artifact existence.
TaskMode = Literal["standard_ml", "open_ended"]


class TaskDefinition(BaseModel):
    """
    Standardized, serializable representation of any task in the DSAT framework.

    This is the "logical contract" for the framework to interact with external benchmarks.
    It encapsulates all information about a task so that DSATRunner and TaskHandler
    can understand and process it.
    """
    task_id: str = Field(
        description="Unique identifier for the task instance, e.g., 'house-prices-advanced-regression-techniques', 'gsm8k_train_001'."
    )
    task_type: TaskType = Field(
        description="General category of the task, used to select the correct TaskHandler for processing."
    )
    mode: TaskMode = Field(
        default="standard_ml",
        description="The execution mode for the task. Defaults to 'standard_ml' for backward compatibility."
    )
    payload: Dict[str, Any] = Field(
        description="A dictionary containing task-specific data."
    )

    model_config = ConfigDict(
        """
        Pydantic configuration with documentation examples.

        Payload examples:
        - task_type='kaggle':
          {
              "description": "Predict sales prices for houses in Ames, Iowa.",
              "public_data_dir": "/path/to/benchmark/data",
              "output_submission_path": "/path/to/run/artifacts/submission.csv"
          }
        - task_type='qa':
          {
              "question": "What is the result of 9*8-2?"
          }
        - task_type='code':
          {
              "prompt": "Write a Python function that computes the nth Fibonacci number.",
              "entry_point": "fibonacci",
              "test_cases": "[...]"
          }
        - task_type='open_ended':
          {
              "description": "Design a mathematical model to optimize traffic flow in a city.",
              "rubric": "Evaluation criteria: model accuracy (40%), creativity (30%), clarity (30%)",
              "output_submission_path": "/path/to/run/artifacts"
          }
        """
        frozen = True  # Task definitions should be immutable after creation.