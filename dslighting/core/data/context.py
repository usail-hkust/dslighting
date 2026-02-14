"""
Task context data structures.

This module contains the TaskContext class which represents
the Agent's view of a task dataset with all necessary metadata.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from dslighting.core.detection.detector import TaskDetection
from dslighting.utils.submission_contract import (
    build_tag_contract_reminder,
    extract_submission_tag_contract,
    find_sample_submission_file,
    normalize_submission_tag_contract,
)

logger = logging.getLogger(__name__)


@dataclass
class TaskContext:
    """
    Agent's view of a task dataset (NOT a traditional data-only dataset).

    ⚠️ IMPORTANT: This is NOT a typical dataset containing only data!
    This is the Agent's perspective of the ENTIRE task context.

    Contains everything the Agent needs to know:
    - Data location and structure
    - Task ID and metadata
    - Registry directory (for grading)
    - Submission format requirements

    Think of this as "Task Specification" rather than just data.

    Attributes:
        source: Original data source (path, DataFrame, etc.)
        data_dir: Data directory path (for file-based sources)
        task_detection: Detected task information
        task_id: Task/Competition ID (extracted from path)
        registry_dir: Benchmark registry directory (for MLE-Bench grading)
        metadata: Additional metadata

    Example:
        >>> context = dslighting.load_data("bike-sharing-demand")
        >>> print(context.show())  # Shows: schema, structure, submission format
        >>> agent = dslighting.Agent()
        >>> result = agent.run(context)  # Agent sees the full task context
    """
    source: Any
    data_dir: Optional[Path] = None
    task_detection: Optional[TaskDetection] = None
    task_id: Optional[str] = None
    registry_dir: Optional[Path] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        """Return a concise representation of the task context."""
        if self.task_id:
            return f"TaskContext(task_id='{self.task_id}', task_type='{self.get_task_type()}')"
        elif self.data_dir:
            return f"TaskContext(data_dir='{self.data_dir.name}', task_type='{self.get_task_type()}')"
        else:
            return f"TaskContext(task_type='{self.get_task_type()}')"

    def show(self) -> str:
        """
        Display detailed data structure and schema information.

        This shows what the Agent sees - file structure, data schema,
        and task information. Use this to understand your data before
        running the Agent.

        Returns:
            Formatted string with data structure and schema

        Example:
            >>> data = dslighting.load_data("data/competitions/bike-sharing-demand")
            >>> print(data.show())
        """
        lines = []
        lines.append("=" * 80)
        lines.append("DSLighting Data Overview")
        lines.append("=" * 80)
        lines.append("")

        # Task Information
        lines.append("## Task Information")
        lines.append(f"  Task ID:          {self.task_id or 'N/A'}")
        lines.append(f"  Task Type:        {self.get_task_type()}")
        lines.append(f"  Task Mode:        {self.task_detection.task_mode if self.task_detection else 'N/A'}")
        lines.append(f"  Recommended:      {self.get_recommended_workflow()} workflow")
        lines.append("")

        # Data Directory
        if self.data_dir:
            lines.append("## Data Directory")
            lines.append(f"  Path:             {self.data_dir}")
            lines.append(f"  Exists:          {self.data_dir.exists()}")
            lines.append("")

        # Data Schema
        lines.append("## Data Schema")
        if self.data_dir:
            train_path = self.data_dir / "train.csv"
            test_path = self.data_dir / "test.csv"
            lines.append(f"  Train file:       {train_path} {'✓' if train_path.exists() else '✗'}")
            lines.append(f"  Test file:        {test_path} {'✓' if test_path.exists() else '✗'}")

            if train_path.exists():
                try:
                    train_df = pd.read_csv(train_path, nrows=0)
                    lines.append(f"  Train columns:   {list(train_df.columns)}")
                except Exception:
                    lines.append("  Train columns:   (unable to read)")

            lines.append("")

        # Submission Format
        lines.append("## Submission Format")
        lines.append(f"  Expected:         {self._get_submission_format()}")
        submission_contract = self.get_submission_contract()
        if submission_contract.get("tag_wrapper_required", False):
            lines.append("  Tagged wrapper:   required")
            required_tags = submission_contract.get("required_tags") or []
            lines.append(
                f"  Required tags:    {required_tags if required_tags else '(detected from template)'}"
            )
        lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def get_task_type(self) -> str:
        """
        Get the task type (e.g., 'kaggle', 'open_end', 'qa').

        Returns:
            Task type string
        """
        if self.task_detection:
            return self.task_detection.task_type or "unknown"
        return "unknown"

    def get_task_mode(self) -> str:
        """
        Get the task mode (e.g., 'mle', 'open_end').

        Returns:
            Task mode string
        """
        if self.task_detection:
            return self.task_detection.task_mode or "unknown"
        return "unknown"

    def get_recommended_workflow(self) -> str:
        """
        Get the recommended workflow for this task.

        Returns:
            Workflow name (e.g., 'aide', 'autokaggle')
        """
        if self.task_detection:
            return self.task_detection.recommended_workflow or "aide"
        return "aide"

    def get_description(self) -> str:
        """
        Get the task description.

        Returns:
            Task description string
        """
        if self.task_detection:
            return self.task_detection.description or ""
        return ""

    def get_submission_contract(self) -> Dict[str, Any]:
        """Get normalized submission contract from metadata or template inference."""
        cached_contract = normalize_submission_tag_contract(
            self.metadata.get("submission_contract")
        )
        if cached_contract:
            self.metadata["submission_contract"] = cached_contract
            return cached_contract

        if not self.data_dir or not self.data_dir.exists():
            contract = extract_submission_tag_contract(None)
            self.metadata["submission_contract"] = contract
            return contract

        submission_context = self.metadata.get("submission_context")
        context = submission_context if isinstance(submission_context, dict) else {}

        sample_submission_file = find_sample_submission_file(
            self.data_dir,
            sample_submission_path=str(context.get("sample_submission_path", "") or ""),
            submission_filename=str(context.get("submission_filename", "") or ""),
        )
        contract = extract_submission_tag_contract(sample_submission_file)
        self.metadata["submission_contract"] = contract
        return contract

    def get_submission_reminder(self) -> str:
        """Get standardized submission reminder block for tagged templates."""
        return build_tag_contract_reminder(self.get_submission_contract())

    def _get_submission_format(self) -> str:
        """Get expected submission format."""
        if self.task_detection:
            return self.task_detection.submission_format or "csv"
        return "csv"
