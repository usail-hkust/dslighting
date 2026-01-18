# dsat/common/typing.py
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any

class ExecutionResult(BaseModel):
    """
    Standardized result of executing a code snippet in any sandbox mode.
    """
    success: bool = Field(description="True if the execution completed without errors, False otherwise.")
    stdout: str = Field(default="", description="The captured standard output stream.")
    stderr: str = Field(default="", description="The captured standard error stream.")
    exc_type: Optional[str] = Field(default=None, description="The type of exception if one was raised (e.g., 'TimeoutError', 'ValueError').")
    # For notebook mode, this can hold base64 encoded images or other rich outputs.
    artifacts: List[str] = Field(default_factory=list, description="A list of generated artifacts, like image filenames.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary execution metadata (timestamps, paths, etc.).")

    model_config = ConfigDict(
        extra='forbid'  # Pydantic configuration
    )
