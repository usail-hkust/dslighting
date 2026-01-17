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

    This class provides a structured view of the data that matches what
    the DSLighting Agent sees - file structure, schema, and metadata.

    Attributes:
        source: Original data source (path, DataFrame, etc.)
        data_dir: Data directory path (for file-based sources)
        task_detection: Detected task information
        task_id: Task/Competition ID (extracted from path)
        registry_dir: Benchmark registry directory (for MLE-Bench grading)
        metadata: Additional metadata
    """
    source: Any
    data_dir: Optional[Path] = None
    task_detection: Optional[TaskDetection] = None
    task_id: Optional[str] = None
    registry_dir: Optional[Path] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def __repr__(self) -> str:
        """Return a concise representation of loaded data."""
        if self.task_id:
            return f"LoadedData(task_id='{self.task_id}', task_type='{self.get_task_type()}')"
        elif self.data_dir:
            return f"LoadedData(data_dir='{self.data_dir.name}', task_type='{self.get_task_type()}')"
        else:
            return f"LoadedData(task_type='{self.get_task_type()}')"

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
            lines.append(f"  Path: {self.data_dir}")

            # Show MLE structure
            prepared_dir = self.data_dir / "prepared"
            if prepared_dir.exists():
                lines.append(f"  Structure: MLE-Bench format")
                public_dir = prepared_dir / "public"
                private_dir = prepared_dir / "private"

                if public_dir.exists():
                    lines.append(f"  Public dir:  {public_dir}")
                    lines.append(self._analyze_directory(public_dir, "Public Data"))
                else:
                    lines.append(f"  Public dir:  Not found")

                if private_dir.exists():
                    lines.append(f"  Private dir: {private_dir}")
            else:
                # Show raw structure
                lines.append(f"  Structure: Standard format")
                lines.append(self._analyze_directory(self.data_dir, "Data Files"))
            lines.append("")

        # Description
        description = self.get_description()
        if description:
            lines.append("## Task Description")
            # Truncate long descriptions
            if len(description) > 500:
                description = description[:500] + "...\n[Description truncated, use get_description() to see full]"
            lines.append(f"  {description}")
            lines.append("")

        # I/O Instructions
        io_instructions = self.get_io_instructions()
        if io_instructions:
            lines.append("## I/O Requirements")
            instructions = io_instructions.strip().split("\n")
            for line in instructions[:10]:  # Show first 10 lines
                lines.append(f"  {line}")
            if len(instructions) > 10:
                lines.append(f"  [... {len(instructions) - 10} more lines, use get_io_instructions() to see full]")
            lines.append("")

        lines.append("=" * 80)
        lines.append("Use .get_description() for full task description")
        lines.append("Use .get_io_instructions() for full I/O instructions")
        lines.append("Use agent.run(data) to run the agent on this data")
        lines.append("=" * 80)

        return "\n".join(lines)

    def _analyze_directory(self, directory: Path, title: str) -> str:
        """Analyze directory and return schema information."""
        lines = []
        lines.append(f"\n  ### {title}")

        try:
            # List files
            files = sorted([f for f in directory.iterdir() if f.is_file()])

            if not files:
                lines.append("    No files found")
                return "\n".join(lines)

            for file_path in files:
                if not file_path.suffix.lower() in ['.csv', '.tsv', '.parquet', '.json']:
                    continue

                lines.append(f"\n  📄 {file_path.name}")

                # Analyze CSV/TSV files
                if file_path.suffix.lower() in ['.csv', '.tsv']:
                    try:
                        df = pd.read_csv(file_path, nrows=0)  # Read only header

                        # Show columns
                        lines.append(f"     Columns ({len(df.columns)}): {', '.join(list(df.columns[:5]))}")
                        if len(df.columns) > 5:
                            lines.append(f"                ... and {len(df.columns) - 5} more")

                        # Show types for first few columns
                        lines.append(f"     Types:")
                        for col in list(df.columns)[:5]:
                            dtype = str(df[col].dtype)
                            lines.append(f"       - {col}: {dtype}")
                        if len(df.columns) > 5:
                            lines.append(f"       ... and {len(df.columns) - 5} more")

                    except Exception as e:
                        lines.append(f"     [Error reading file: {e}]")

        except Exception as e:
            lines.append(f"  [Error analyzing directory: {e}]")

        return "\n".join(lines)

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
    Load data from various sources with optional automatic type detection.

    By default, all data is treated as MLE format (prepared/public & prepared/private).
    Set auto_detect=True to enable automatic task type detection.

    Supported sources:
    - File paths (CSV, JSON, parquet)
    - Directory paths (competition layout)
    - Pandas DataFrames
    - Dict/question strings (QA tasks)
    """

    def __init__(self, auto_detect: bool = False):
        """
        Initialize DataLoader.

        Args:
            auto_detect: If True, automatically detect task type.
                        If False (default), treat all data as MLE format.
        """
        self.detector = TaskDetector()
        self.auto_detect = auto_detect
        self.logger = logger

    def load(
        self,
        source: Union[str, Path, pd.DataFrame, dict],
        auto_detect: bool = None,
        registry_dir: Union[str, Path] = None,
        **kwargs
    ) -> LoadedData:
        """
        Load data from a source.

        Args:
            source: Data source (path, DataFrame, dict, etc.)
            auto_detect: Override the instance's auto_detect setting.
                        If None (default), use instance setting.
            registry_dir: Benchmark registry directory (for MLE-Bench grading).
                        If None (default), will auto-detect from data directory structure.
                        For DSLighting project: benchmarks/mlebench/competitions/
            **kwargs: Additional parameters

        Returns:
            LoadedData with detection information
        """
        self.logger.info(f"Loading data from source: {type(source).__name__}")

        # Determine whether to auto-detect
        should_auto_detect = auto_detect if auto_detect is not None else self.auto_detect

        # Detect task type (or use MLE default)
        if should_auto_detect:
            task_detection = self.detector.detect(source)
        else:
            task_detection = self._get_default_mle_detection(source)

        # Determine data directory
        data_dir = self._extract_data_dir(source, task_detection)

        # Extract task_id from path
        task_id = self._extract_task_id(source, data_dir)

        # Auto-detect registry_dir if not provided
        if registry_dir is None:
            registry_dir = self._auto_detect_registry_dir(data_dir, task_id)
        else:
            registry_dir = Path(registry_dir)

        # Create LoadedData
        loaded_data = LoadedData(
            source=source,
            data_dir=data_dir,
            task_detection=task_detection,
            task_id=task_id,
            registry_dir=registry_dir,
            metadata=kwargs
        )

        if registry_dir:
            self.logger.info(f"Registry directory: {registry_dir}")

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

    def _get_default_mle_detection(self, source: Any) -> TaskDetection:
        """
        Get default MLE competition detection for any data source.

        This method treats all data as MLE format (prepared/public & prepared/private).
        It extracts the data directory if available.

        Args:
            source: Data source (path, DataFrame, dict, etc.)

        Returns:
            TaskDetection configured for MLE competition
        """
        self.logger.info("Using default MLE competition format (prepared/public & prepared/private)")

        # Try to extract data directory
        data_dir = None
        description = "MLE competition task"

        if isinstance(source, (str, Path)):
            path = Path(source).resolve()  # Convert to absolute path
            self.logger.info(f"Resolved path: {path}")

            if path.exists():
                if path.is_dir():
                    data_dir = path
                    self.logger.info(f"Data directory found: {data_dir}")
                    # Try to load description
                    desc_file = path / "description.md"
                    if desc_file.exists():
                        try:
                            description = desc_file.read_text(encoding='utf-8')
                            self.logger.info(f"Loaded description from {desc_file}")
                        except Exception:
                            pass
                elif path.is_file():
                    data_dir = path.parent
                    self.logger.info(f"Data directory (from file parent): {data_dir}")
                    # Try to load description from parent directory
                    desc_file = path.parent / "description.md"
                    if desc_file.exists():
                        try:
                            description = desc_file.read_text(encoding='utf-8')
                            self.logger.info(f"Loaded description from {desc_file}")
                        except Exception:
                            pass
            else:
                self.logger.warning(f"Path does not exist: {path}")

                # Try to find the data in common locations
                competition_id = path.name

                # Common search locations for data
                search_locations = [
                    # Current project: ./data/competitions/
                    Path.cwd() / "data" / "competitions" / competition_id,
                    # Parent dslighting: ../dslighting/data/competitions/
                    Path.cwd().parent / "dslighting" / "data" / "competitions" / competition_id,
                    # Parent data: ../data/competitions/
                    Path.cwd().parent / "data" / "competitions" / competition_id,
                    # From package location: ../../data/competitions/
                    Path(__file__).parent.parent.parent / "data" / "competitions" / competition_id,
                    # Absolute path fallback
                    Path("/Users/liufan/Applications/Github/dslighting/data/competitions") / competition_id,
                ]

                for location in search_locations:
                    self.logger.info(f"  Trying: {location}")
                    if location.exists() and location.is_dir():
                        data_dir = location
                        self.logger.info(f"  ✓ Found data at: {data_dir}")
                        break

                if data_dir is None:
                    # Last resort: use the original resolved path
                    self.logger.warning(f"  Could not find data, using original path: {path}")
                    data_dir = path

            # Try to load description (if data_dir was found)
            if data_dir and data_dir.exists():
                desc_file = data_dir / "description.md"
                if desc_file.exists():
                    try:
                        description = desc_file.read_text(encoding='utf-8')
                        self.logger.info(f"Loaded description from {desc_file}")
                    except Exception:
                        pass

        # Create MLE-style detection
        from dslighting.utils.defaults import WORKFLOW_RECOMMENDATIONS

        return TaskDetection(
            task_type="kaggle",  # MLE uses kaggle task type internally
            task_mode="standard_ml",
            data_dir=data_dir,
            description=description,
            io_instructions="Train a model and generate predictions for the test set.",
            recommended_workflow=WORKFLOW_RECOMMENDATIONS.get("kaggle_competition", {}).get("default", "aide"),
            confidence=1.0,  # High confidence since this is explicit user intent
            metadata={"structure": "mle_competition", "auto_detected": False}
        )

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

    def _extract_task_id(
        self,
        source: Any,
        data_dir: Optional[Path]
    ) -> Optional[str]:
        """
        Extract task/competition ID from source path.

        Args:
            source: Original data source
            data_dir: Detected data directory

        Returns:
            Task ID (e.g., "bike-sharing-demand") or None
        """
        # If source is a path, extract the last directory name as task_id
        if isinstance(source, (str, Path)):
            path = Path(source)

            # If it's a file, use parent directory name
            if path.is_file():
                return path.parent.name

            # If it's a directory, use its name
            if path.is_dir():
                return path.name

        # If data_dir is available, use its name
        if data_dir:
            return data_dir.name

        # No task_id found
        return None

    def _auto_detect_registry_dir(
        self,
        data_dir: Optional[Path],
        task_id: Optional[str]
    ) -> Optional[Path]:
        """
        Auto-detect MLE-Bench registry directory from data directory structure.

        The registry contains competition configs (config.yaml) with grading information.
        This method looks for the benchmarks directory relative to the data directory.

        Args:
            data_dir: Data directory path
            task_id: Task/competition ID

        Returns:
            Path to registry directory or None
        """
        if not data_dir:
            return None

        self.logger.info(f"Auto-detecting registry directory for data_dir: {data_dir}")

        # Expected structure:
        # dslighting/
        #   ├── data/competitions/{task_id}/     <- data_dir points here
        #   └── benchmarks/mlebench/competitions/ <- registry we need to find

        # Strategy 1: Look for benchmarks/ sibling to data/
        if data_dir.is_absolute():
            # data_dir = /path/to/dslighting/data/competitions/bike-sharing-demand
            # We want: /path/to/dslighting/benchmarks/mlebench/competitions

            # Go up to find data/, then look for benchmarks/ sibling
            current = data_dir
            for _ in range(5):  # Don't go up more than 5 levels
                if current.parent.name == "data":
                    # Found data/ directory, look for benchmarks/ sibling
                    benchmarks_root = current.parent.parent / "benchmarks" / "mlebench" / "competitions"
                    if benchmarks_root.exists():
                        self.logger.info(f"  ✓ Found benchmarks at: {benchmarks_root}")
                        return benchmarks_root
                    break
                current = current.parent

        # Strategy 2: Check known locations relative to current file
        try:
            # dslighting/dslighting/core/data_loader.py
            # Go up to dslighting/ root, then benchmarks/
            file_location = Path(__file__).resolve()
            dslighting_root = file_location.parent.parent.parent  # Up 3 levels
            benchmarks_root = dslighting_root / "benchmarks" / "mlebench" / "competitions"

            if benchmarks_root.exists():
                self.logger.info(f"  ✓ Found benchmarks from package structure: {benchmarks_root}")
                return benchmarks_root
        except Exception as e:
            self.logger.debug(f"  Could not determine package structure: {e}")

        # Strategy 3: If data_dir is in standard DSLighting location, infer benchmarks
        # /Users/liufan/Applications/Github/dslighting/data/competitions/{task_id}
        # -> /Users/liufan/Applications/Github/dslighting/benchmarks/mlebench/competitions/
        if "Github" in str(data_dir) or "dslighting" in str(data_dir):
            # Try to reconstruct benchmarks path
            parts = data_dir.parts
            try:
                if "data" in parts:
                    idx = parts.index("data")
                    # Rebuild path up to "data", then replace with "benchmarks/mlebench/competitions"
                    base_parts = parts[:idx]
                    benchmarks_path = Path(*base_parts) / "benchmarks" / "mlebench" / "competitions"

                    if benchmarks_path.exists():
                        self.logger.info(f"  ✓ Found benchmarks from path reconstruction: {benchmarks_path}")
                        return benchmarks_path
            except Exception as e:
                self.logger.debug(f"  Path reconstruction failed: {e}")

        # Strategy 4: Check if this is a test_project scenario
        # /Users/liufan/Applications/Github/dslighting_test_project/
        # -> /Users/liufan/Applications/Github/dslighting/benchmarks/
        try:
            import os
            cwd = Path.cwd()
            if "test_project" in str(cwd) or "test" in str(cwd):
                # Go up to Github/, then into dslighting/
                github_root = cwd.parent
                benchmarks_path = github_root / "dslighting" / "benchmarks" / "mlebench" / "competitions"

                if benchmarks_path.exists():
                    self.logger.info(f"  ✓ Found benchmarks from test project: {benchmarks_path}")
                    return benchmarks_path
        except Exception as e:
            self.logger.debug(f"  Test project detection failed: {e}")

        # Could not auto-detect
        self.logger.warning("  ⚠️  Could not auto-detect registry directory")
        self.logger.warning("     Pass registry_dir explicitly to load_data() or Agent.run()")
        self.logger.warning("     Example: load_data(path, registry_dir='path/to/benchmarks/mlebench/competitions')")

        return None
