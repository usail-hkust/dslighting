# web_ui/backend/app/models/llm_formats.py

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class IntentResponse(BaseModel):
    action: str = Field(description="The selected action tag, e.g., <DATA_PREPARATION_CODE>, <DATA_ANALYSIS_CODE>, or <UPDATE_REPORT>.")
    reason: str = Field(description="Explanation for why this action was chosen.")

class DebugSummary(BaseModel):
    concise_summary: str = Field(description="A 2-3 sentence summary of the debugging progress.")
    mistakes_identified: List[str] = Field(description="List of specific mistakes found in previous attempts.")
    next_step_recommendation: str = Field(description="Guidance for the next fix attempt.")

class ExplorationAction(BaseModel):
    thought: str = Field(description="Reasoning for the current exploration step.")
    code: str = Field(description="The Python script to execute, wrapped in the prompt but returned as a clean string here.")
    is_done: bool = Field(description="True if you have enough information about the data schema.")

class FileLoadingInfo(BaseModel):
    file_path: str = Field(description="Relative path to the file from sandbox root (e.g., 'raw/train.csv', 'prepared/train.csv').")
    file_type: str = Field(description="Type of file: 'csv', 'json', 'parquet', 'image', 'audio', or 'other'.")
    suggested_parameters: Dict[str, Any] = Field(description="Loading parameters specific to this file (e.g., encoding, separator, parse_dates for CSV; library-specific args for images/audio).")
    data_structure: str = Field(description="File-specific structure: column names with data types, shape info, or key fields.")
    critical_insights: str = Field(description="File-specific findings: missing values, encoding issues, outliers, or special handling requirements.")

class DataLoadingGuide(BaseModel):
    files: List[FileLoadingInfo] = Field(description="List of file-specific loading instructions. Each file gets its own detailed entry.")
    overall_insights: str = Field(description="Cross-file insights: relationships between files, train/test splits, shared schemas, or data lineage.")
    loading_example: str = Field(description="A concrete code example showing how to load all files using the suggested parameters.")

class CodeResponse(BaseModel):
    thought: str = Field(description="Step-by-step reasoning for the proposed solution.")
    code: str = Field(description="The complete, single-file Python script.")

class TaskBlueprint(BaseModel):
    modality: str = Field(description="The data modality: 'tabular', 'image', 'audio', or 'text'.")
    task_type: str = Field(description="e.g., 'regression', 'multi-class classification', 'object detection'.")
    target_column_or_label: str = Field(description="The name of the target column or how labels are identified.")
    splitting_strategy: str = Field(description="Detailed plan for splitting (e.g., 'Chronological split at 2021').")
    feature_engineering_plan: List[str] = Field(description="List of specific features or preprocessing steps to be implemented.")
    output_layout: Dict[str, str] = Field(description="Expected file mapping for manifest.json (e.g., {'train': 'prepared_data/train.csv'}).")
    justification: str = Field(description="Why this specific blueprint is the best for this task.")

class BlueprintApproval(BaseModel):
    is_approved: bool = Field(description="True if the user is satisfied and wants to proceed to implementation. False if they want changes.")
    feedback_summary: str = Field(description="A concise summary of the user's feedback or confirmation.")

class ChatSummary(BaseModel):
    current_task_state: List[str] = Field(description="List of bullet points describing the completed steps and current status.")
    user_specific_requirements: List[str] = Field(description="List of bullet points describing specific constraints or preferences set by the user.")

class ComplianceCheck(BaseModel):
    compliant: bool = Field(description="True if the dataset structure meets all requirements.")
    reason: str = Field(description="If compliant, 'OK'. If not, detailed explanation of what is missing or wrong.")

class ReportResponse(BaseModel):
    thought: str = Field(description="Reasoning for the report structure and content.")
    report_content: str = Field(description="The full markdown content of the report.")

class ChatResponse(BaseModel):
    thought: str = Field(description="Step-by-step reasoning for the response.")
    response: str = Field(description="The text response to the user.")
    code: Optional[str] = Field(default=None, description="Optional Python code if the response includes code.")

# =============================================================================
# MODEL TRAINING ASSISTANT RESPONSES
# =============================================================================

class QAResponse(BaseModel):
    """Response for Q&A assistant mode in model training."""
    answer: str = Field(description="The detailed answer to the user's question.")

class ProblemRefinementResponse(BaseModel):
    """Response for refining problem definition."""
    thought: str = Field(description="Analysis of what needs improvement in the description.")
    refined_description: str = Field(description="The improved task description.")

class RubricRefinementResponse(BaseModel):
    """Response for refining evaluation rubric."""
    thought: str = Field(description="Analysis of what needs improvement in the rubric.")
    refined_rubric: str = Field(description="The improved rubric in Markdown format.")

class CodeImprovementResponse(BaseModel):
    """Response for improving model training code."""
    thought: str = Field(description="Analysis of what needs improvement in the code.")
    improved_code: str = Field(description="The complete improved Python code.")
    changes: List[str] = Field(description="List of specific improvements made.")
