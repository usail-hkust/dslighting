"""
Task detection and automatic task type inference.

This module provides intelligent detection of data science task types
from various data sources (directories, files, DataFrames, etc.).
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from dslighting.utils.defaults import WORKFLOW_RECOMMENDATIONS

logger = logging.getLogger(__name__)


@dataclass
class TaskDetection:
    """
    Result of task detection.

    Attributes:
        task_type: Detected task type (kaggle, qa, datasci, open_ended)
        task_mode: Task mode (standard_ml, open_ended)
        data_dir: Data directory path (if applicable)
        description: Task description (if found)
        io_instructions: I/O instructions
        recommended_workflow: Recommended workflow for this task
        confidence: Detection confidence (0-1)
        metadata: Additional detection metadata
    """
    task_type: str
    task_mode: str
    data_dir: Optional[Path] = None
    description: str = ""
    io_instructions: str = ""
    recommended_workflow: str = "aide"
    confidence: float = 0.8
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TaskDetector:
    """
    Automatically detect task types from data sources.

    This class analyzes directory structures, file types, and content
    to determine the most appropriate task type and workflow.
    """

    def __init__(self):
        self.logger = logger

    def detect(self, source: Any) -> TaskDetection:
        """
        Detect task type from a data source.

        Args:
            source: Data source (path, DataFrame, dict, etc.)

        Returns:
            TaskDetection with inferred task information
        """
        # DataFrame: Custom ML task (highest priority for DataFrames)
        if isinstance(source, pd.DataFrame):
            return self._detect_dataframe_task(source)

        # Path: Directory or file (check before treating as string)
        if isinstance(source, (str, Path)):
            path = Path(source)
            if path.is_dir():
                return self._detect_from_directory(path)
            elif path.is_file():
                return self._detect_from_file(path)
            # If path doesn't exist, check if it's a short question (QA task)
            elif len(source) < 500 and not any(c in source for c in ['/', '\\', '.csv', '.json', '.txt']):
                return self._detect_qa_task(source)

        # Dict: QA task
        if isinstance(source, dict):
            return self._detect_qa_task(str(source))

        # Fallback
        return TaskDetection(
            task_type="datasci",
            task_mode="standard_ml",
            description="Custom data science task",
            recommended_workflow="aide",
            confidence=0.5
        )

    def _detect_qa_task(self, question: str) -> TaskDetection:
        """Detect a QA (question-answering) task."""
        self.logger.info("Detected QA task")

        return TaskDetection(
            task_type="qa",
            task_mode="standard_ml",
            description=f"Answer the following question: {question}",
            io_instructions="Provide a clear, concise answer.",
            recommended_workflow=WORKFLOW_RECOMMENDATIONS["qa"]["default"],
            confidence=0.95,
            metadata={"question": question}
        )

    def _detect_dataframe_task(self, df: pd.DataFrame) -> TaskDetection:
        """Detect task type from a pandas DataFrame."""
        self.logger.info(f"Detected DataFrame task with {len(df)} rows, {len(df.columns)} columns")

        # Check if it has a target column (common pattern: last column is target)
        has_target = len(df.columns) > 1

        if has_target:
            description = (
                f"Build a machine learning model to predict the target variable. "
                f"Dataset has {len(df)} rows and {len(df.columns)} columns."
            )
            io_instructions = (
                "Train a model on the data and provide predictions. "
                "Use appropriate evaluation metrics."
            )
            recommended_workflow = "aide"
        else:
            description = (
                f"Perform exploratory data analysis and clustering. "
                f"Dataset has {len(df)} rows and {len(df.columns)} columns."
            )
            io_instructions = "Analyze the data and provide insights."
            recommended_workflow = "data_interpreter"

        return TaskDetection(
            task_type="datasci",
            task_mode="standard_ml" if has_target else "open_ended",
            description=description,
            io_instructions=io_instructions,
            recommended_workflow=recommended_workflow,
            confidence=0.85,
            metadata={
                "shape": df.shape,
                "columns": list(df.columns),
                "dtypes": df.dtypes.to_dict()
            }
        )

    def _detect_from_directory(self, dir_path: Path) -> TaskDetection:
        """Detect task type from a directory structure."""
        self.logger.info(f"Detecting task from directory: {dir_path}")

        # Priority 1: Check for MLE competition structure (prepared/public & prepared/private)
        if self._is_mle_competition(dir_path):
            return self._detect_mle_competition(dir_path)

        # Priority 2: Check for Kaggle competition structure (train.csv, test.csv)
        if self._is_kaggle_format(dir_path):
            return self._detect_kaggle_competition(dir_path)

        # Priority 3: Check for open-ended task
        if self._is_open_ended_task(dir_path):
            return self._detect_open_ended_task(dir_path)

        # Priority 4: Check for DataSci task
        if self._is_datasci_task(dir_path):
            return self._detect_datasci_task(dir_path)

        # Default: treat as generic data directory
        return self._detect_generic_directory(dir_path)

    def _detect_from_file(self, file_path: Path) -> TaskDetection:
        """Detect task type from a single file."""
        self.logger.info(f"Detecting task from file: {file_path}")

        suffix = file_path.suffix.lower()

        if suffix == ".csv":
            return self._detect_csv_file(file_path)
        elif suffix in [".json", ".jsonl"]:
            return self._detect_json_file(file_path)
        elif suffix in [".txt", ".md"]:
            return self._detect_text_file(file_path)
        else:
            # Unknown file type
            return TaskDetection(
                task_type="datasci",
                task_mode="standard_ml",
                description=f"Process file: {file_path.name}",
                recommended_workflow="aide",
                confidence=0.6
            )

    def _is_mle_competition(self, dir_path: Path) -> bool:
        """Check if directory is an MLE competition structure (prepared/public & prepared/private)."""
        # Check for prepared/public and prepared/private
        prepared = dir_path / "prepared"
        if prepared.exists():
            public = prepared / "public"
            private = prepared / "private"
            if public.exists() and private.exists():
                return True
        return False

    def _is_kaggle_format(self, dir_path: Path) -> bool:
        """Check if directory has Kaggle-style files (train.csv, test.csv, sample_submission.csv)."""
        # Check for train.csv + test.csv
        has_train = (dir_path / "train.csv").exists()
        has_test = (dir_path / "test.csv").exists()
        has_sample_submission = (dir_path / "sample_submission.csv").exists()

        return has_train and (has_test or has_sample_submission)

    def _is_open_ended_task(self, dir_path: Path) -> bool:
        """Check if directory is an open-ended task."""
        has_description = (dir_path / "description.md").exists()
        has_rubric = (dir_path / "rubric.md").exists()
        return has_description and has_rubric

    def _is_datasci_task(self, dir_path: Path) -> bool:
        """Check if directory is a DataSci task."""
        has_prompt = (dir_path / "prompt.txt").exists()
        has_description = (dir_path / "description.md").exists()
        return has_prompt or has_description

    def _detect_mle_competition(self, dir_path: Path) -> TaskDetection:
        """Detect MLE competition task (standard DSAT format with prepared/public & prepared/private)."""
        self.logger.info("Detected MLE competition structure (prepared/public & prepared/private)")

        # Load description if exists
        description = ""
        description_file = dir_path / "description.md"
        if description_file.exists():
            description = description_file.read_text(encoding='utf-8')

        # MLE competitions use kaggle task_type internally
        return TaskDetection(
            task_type="kaggle",
            task_mode="standard_ml",
            data_dir=dir_path,
            description=description or "MLE competition task",
            io_instructions="Train a model and generate predictions for the test set.",
            recommended_workflow="aide",
            confidence=0.95,
            metadata={"structure": "mle_competition"}
        )

    def _detect_kaggle_competition(self, dir_path: Path) -> TaskDetection:
        """Detect Kaggle competition task."""
        self.logger.info("Detected Kaggle competition structure")

        # Load description if exists
        description = ""
        description_file = dir_path / "description.md"
        if description_file.exists():
            description = description_file.read_text(encoding='utf-8')

        # Detect if tabular or time series
        is_tabular = self._is_tabular_competition(dir_path)
        is_time_series = self._is_time_series_competition(dir_path)

        if is_time_series:
            recommended = WORKFLOW_RECOMMENDATIONS["kaggle_competition"]["time_series"][0]
        elif is_tabular:
            recommended = WORKFLOW_RECOMMENDATIONS["kaggle_competition"]["tabular"][0]
        else:
            recommended = WORKFLOW_RECOMMENDATIONS["kaggle_competition"]["default"]

        return TaskDetection(
            task_type="kaggle",
            task_mode="standard_ml",
            data_dir=dir_path,
            description=description or "Kaggle competition task",
            io_instructions="Train a model and generate predictions for the test set.",
            recommended_workflow=recommended,
            confidence=0.9,
            metadata={"structure": "kaggle_competition"}
        )

    def _detect_open_ended_task(self, dir_path: Path) -> TaskDetection:
        """Detect open-ended exploration task."""
        self.logger.info("Detected open-ended task")

        description_file = dir_path / "description.md"
        description = ""
        if description_file.exists():
            description = description_file.read_text(encoding='utf-8')

        return TaskDetection(
            task_type="open_ended",
            task_mode="open_ended",
            data_dir=dir_path,
            description=description or "Open-ended data exploration task",
            io_instructions="Explore the data and provide comprehensive insights.",
            recommended_workflow=WORKFLOW_RECOMMENDATIONS["open_ended"]["default"],
            confidence=0.9,
            metadata={"structure": "open_ended"}
        )

    def _detect_datasci_task(self, dir_path: Path) -> TaskDetection:
        """Detect DataSci task."""
        self.logger.info("Detected DataSci task")

        prompt_file = dir_path / "prompt.txt"
        description_file = dir_path / "description.md"

        description = ""
        if prompt_file.exists():
            description = prompt_file.read_text(encoding='utf-8')
        elif description_file.exists():
            description = description_file.read_text(encoding='utf-8')

        return TaskDetection(
            task_type="datasci",
            task_mode="standard_ml",
            data_dir=dir_path,
            description=description or "Data science task",
            io_instructions="Complete the data science task as described.",
            recommended_workflow=WORKFLOW_RECOMMENDATIONS["datasci"]["default"],
            confidence=0.85,
            metadata={"structure": "datasci"}
        )

    def _detect_generic_directory(self, dir_path: Path) -> TaskDetection:
        """Detect task from generic directory."""
        self.logger.info("Treating as generic data directory")

        # List files in directory
        files = list(dir_path.glob("*"))
        file_names = [f.name for f in files if f.is_file()]

        description = (
            f"Process data in directory: {dir_path.name}. "
            f"Contains {len(files)} files: {', '.join(file_names[:5])}"
        )

        return TaskDetection(
            task_type="datasci",
            task_mode="standard_ml",
            data_dir=dir_path,
            description=description,
            io_instructions="Analyze the data and provide results.",
            recommended_workflow="aide",
            confidence=0.7,
            metadata={"files": file_names}
        )

    def _detect_csv_file(self, file_path: Path) -> TaskDetection:
        """Detect task type from a CSV file."""
        try:
            df = pd.read_csv(file_path, nrows=10)
            return self._detect_dataframe_task(df)
        except Exception as e:
            self.logger.warning(f"Failed to read CSV file {file_path}: {e}")
            return TaskDetection(
                task_type="datasci",
                task_mode="standard_ml",
                description=f"Process CSV file: {file_path.name}",
                recommended_workflow="aide",
                confidence=0.6
            )

    def _detect_json_file(self, file_path: Path) -> TaskDetection:
        """Detect task type from a JSON file."""
        import json

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, list) and len(data) > 0:
                # Likely a dataset
                return TaskDetection(
                    task_type="datasci",
                    task_mode="standard_ml",
                    description=f"Process JSON dataset with {len(data)} records",
                    recommended_workflow="aide",
                    confidence=0.7
                )
            else:
                # Likely a QA task or config
                return self._detect_qa_task(str(data))
        except Exception as e:
            self.logger.warning(f"Failed to read JSON file {file_path}: {e}")
            return TaskDetection(
                task_type="datasci",
                task_mode="standard_ml",
                description=f"Process JSON file: {file_path.name}",
                recommended_workflow="aide",
                confidence=0.6
            )

    def _detect_text_file(self, file_path: Path) -> TaskDetection:
        """Detect task type from a text/markdown file."""
        content = file_path.read_text(encoding='utf-8')

        if len(content) < 1000:
            # Short text: likely QA or description
            return self._detect_qa_task(content)
        else:
            # Long text: likely description for a task
            return TaskDetection(
                task_type="open_ended",
                task_mode="open_ended",
                description=content,
                recommended_workflow="deepanalyze",
                confidence=0.75
            )

    def _is_tabular_competition(self, dir_path: Path) -> bool:
        """Check if competition is tabular (has CSV files)."""
        csv_files = list(dir_path.glob("**/*.csv"))
        return len(csv_files) > 0

    def _is_time_series_competition(self, dir_path: Path) -> bool:
        """Check if competition is time series."""
        # Heuristic: check for time-related keywords in file/directory names
        name_lower = str(dir_path).lower()
        time_keywords = ["time", "temporal", "forecast", "series", "date"]
        return any(keyword in name_lower for keyword in time_keywords)
