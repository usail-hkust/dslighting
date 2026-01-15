"""
Data loading and preprocessing.

This module provides a unified interface for loading data from various sources
with automatic type detection and validation.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from dslighting.core.task_detector import TaskDetector, TaskDetection

logger = logging.getLogger(__name__)


@dataclass
class LoadedData:
    """
    Container for loaded data with metadata.

    Attributes:
        source: Original data source (path, DataFrame, etc.)
        data_dir: Data directory path (for file-based sources)
        task_detection: Detected task information
        metadata: Additional metadata
    """
    source: Any
    data_dir: Optional[Path] = None
    task_detection: Optional[TaskDetection] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def get_description(self) -> str:
        """Get task description."""
        if self.task_detection:
            return self.task_detection.description
        return ""

    def get_io_instructions(self) -> str:
        """Get I/O instructions."""
        if self.task_detection:
            return self.task_detection.io_instructions
        return ""

    def get_recommended_workflow(self) -> str:
        """Get recommended workflow."""
        if self.task_detection:
            return self.task_detection.recommended_workflow
        return "aide"

    def get_task_type(self) -> str:
        """Get task type."""
        if self.task_detection:
            return self.task_detection.task_type
        return "datasci"


class DataLoader:
    """
    Load data from various sources with automatic type detection.

    Supported sources:
    - File paths (CSV, JSON, parquet)
    - Directory paths (competition layout)
    - Pandas DataFrames
    - Dict/question strings (QA tasks)
    """

    def __init__(self):
        self.detector = TaskDetector()
        self.logger = logger

    def load(
        self,
        source: Union[str, Path, pd.DataFrame, dict],
        **kwargs
    ) -> LoadedData:
        """
        Load data from a source with automatic type detection.

        Args:
            source: Data source (path, DataFrame, dict, etc.)
            **kwargs: Additional parameters

        Returns:
            LoadedData with detection information
        """
        self.logger.info(f"Loading data from source: {type(source).__name__}")

        # Detect task type
        task_detection = self.detector.detect(source)

        # Determine data directory
        data_dir = self._extract_data_dir(source, task_detection)

        # Create LoadedData
        loaded_data = LoadedData(
            source=source,
            data_dir=data_dir,
            task_detection=task_detection,
            metadata=kwargs
        )

        self.logger.info(
            f"Loaded data: task_type={task_detection.task_type}, "
            f"workflow={task_detection.recommended_workflow}"
        )

        return loaded_data

    def load_csv(
        self,
        path: Union[str, Path],
        **kwargs
    ) -> LoadedData:
        """
        Load data from a CSV file.

        Args:
            path: Path to CSV file
            **kwargs: Additional parameters passed to pd.read_csv

        Returns:
            LoadedData with DataFrame and detection
        """
        path = Path(path)
        self.logger.info(f"Loading CSV file: {path}")

        try:
            df = pd.read_csv(path, **kwargs)
            return self.load(df)
        except Exception as e:
            self.logger.error(f"Failed to load CSV file {path}: {e}")
            raise

    def load_directory(
        self,
        path: Union[str, Path],
        **kwargs
    ) -> LoadedData:
        """
        Load data from a directory.

        Args:
            path: Path to directory
            **kwargs: Additional parameters

        Returns:
            LoadedData with directory and detection
        """
        path = Path(path)
        self.logger.info(f"Loading directory: {path}")

        if not path.is_dir():
            raise ValueError(f"Not a directory: {path}")

        return self.load(path, **kwargs)

    def load_dataframe(
        self,
        df: pd.DataFrame,
        **kwargs
    ) -> LoadedData:
        """
        Load data from a pandas DataFrame.

        Args:
            df: Pandas DataFrame
            **kwargs: Additional parameters

        Returns:
            LoadedData with DataFrame and detection
        """
        self.logger.info(f"Loading DataFrame with shape {df.shape}")
        return self.load(df, **kwargs)

    def load_competition(
        self,
        competition_id: str,
        data_dir: Union[str, Path] = None,
        **kwargs
    ) -> LoadedData:
        """
        Load data from a competition (MLE-Bench style).

        Args:
            competition_id: Competition identifier
            data_dir: Base data directory containing competitions
            **kwargs: Additional parameters

        Returns:
            LoadedData with competition data
        """
        self.logger.info(f"Loading competition: {competition_id}")

        # Default to data/competitions directory
        if data_dir is None:
            data_dir = Path("data/competitions") / competition_id
        else:
            data_dir = Path(data_dir) / competition_id

        if not data_dir.exists():
            raise ValueError(f"Competition directory not found: {data_dir}")

        return self.load(data_dir, **kwargs)

    def load_question(
        self,
        question: str,
        **kwargs
    ) -> LoadedData:
        """
        Load a QA question.

        Args:
            question: Question text
            **kwargs: Additional parameters

        Returns:
            LoadedData with question
        """
        self.logger.info("Loading QA question")
        return self.load(question, **kwargs)

    def _extract_data_dir(
        self,
        source: Any,
        detection: TaskDetection
    ) -> Optional[Path]:
        """
        Extract data directory from source and detection.

        Args:
            source: Original data source
            detection: Task detection result

        Returns:
            Path to data directory or None
        """
        # If detection already has data_dir, use it
        if detection.data_dir:
            return detection.data_dir

        # If source is a path, use its parent
        if isinstance(source, (str, Path)):
            path = Path(source)
            if path.is_file():
                return path.parent
            elif path.is_dir():
                return path

        # No data directory
        return None
