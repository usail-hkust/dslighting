from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class Message(BaseModel):
    role: str
    content: str
    updated_blueprint: Optional[Dict[str, Any]] = None
    selected_data_view: Optional[str] = "data"
    subtask: Optional[str] = None
    report_scope: Optional[str] = None
    custom_prompt: Optional[str] = None

class TaskMetadata(BaseModel):
    title: str
    description: str
    task_type: str
    metric: str
    target_column: Optional[str] = None
