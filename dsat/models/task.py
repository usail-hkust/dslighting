from pydantic import BaseModel, Field
from typing import Literal, Dict, Any

# Define a controlled vocabulary for task types.
# The framework will choose appropriate TaskHandler based on this type.
TaskType = Literal["kaggle", "qa", "code", "datasci"]


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
    payload: Dict[str, Any] = Field(
        description="A dictionary containing task-specific data."
    )

    class Config:
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
        """
        frozen = True  # Task definitions should be immutable after creation.