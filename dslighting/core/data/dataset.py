"""
Data loading and processing module.

This module provides a unified, simplified API for data loading and management,
following best practices from popular frameworks:
- HuggingFace Datasets: load_dataset() -> DataLoader
- Pandas: read_csv() -> DataFrame
- PyTorch: Dataset + DataLoader (simplified)

Key Design Principles:
1. Single class: DataLoader (contains all data and metadata)
2. Simple loading: load_dataset() function
3. Rich metadata: info, data_dir, task_type, etc.
4. Lazy loading: data loaded on demand when possible

Examples:
    >>> from dslighting.core.data import DataLoader, load_dataset
    >>> loader = DataLoader("bike-sharing-demand")
    >>> loader.load()
    >>> print(loader.info)

    >>> # Or use the convenience function
    >>> loader = load_dataset("bike-sharing-demand")
"""

import logging
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd

from dslighting.core.detection.detector import TaskDetector, TaskDetection
from dslighting.utils.submission_contract import (
    build_tag_contract_reminder,
    extract_submission_tag_contract,
    find_sample_submission_file,
    normalize_submission_tag_contract,
)
from .loader_utils import (
    get_default_mle_detection,
    extract_data_dir,
    extract_task_id,
    auto_detect_registry_dir,
    load_task_type_from_registry,
)

logger = logging.getLogger(__name__)


@dataclass
class DatasetInfo:
    """
    Dataset metadata and information.

    Similar to:
    - HuggingFace DatasetInfo
    - Pandas DataFrame.info()
    """
    task_id: Optional[str] = None
    task_type: str = "datasci"
    task_mode: str = "standard_ml"
    description: str = ""
    io_instructions: str = ""
    recommended_workflow: str = "aide"
    data_dir: Optional[Path] = None
    registry_dir: Optional[Path] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"DatasetInfo(task_id='{self.task_id}', task_type='{self.task_type}')"


class DataLoader:
    """
    Unified DataLoader class for loading and managing data.

    This combines the functionality of the older DataLoader and Dataset classes into a single,
    intuitive interface following best practices from HuggingFace and Pandas.

    Examples:
        >>> # Simple usage (recommended)
        >>> import dslighting
        >>> loader = dslighting.load_dataset("bike-sharing-demand")
        >>> print(loader.info)

        >>> # Advanced usage
        >>> from dslighting.core.data import DataLoader
        >>> loader = DataLoader("/path/to/data", auto_detect=True)

        >>> # Access data
        >>> loader.load()  # Load data into memory
        >>> train_df = loader.train
        >>> test_df = loader.test

    Attributes:
        source: Original data source (path, DataFrame, etc.)
        info: DatasetInfo object containing metadata
        auto_detect: Whether to auto-detect task type
        _data: Cached loaded data (lazy loading)
    """

    def __init__(
        self,
        source: Union[str, Path, pd.DataFrame],
        auto_detect: bool = False,
        registry_dir: Optional[Union[str, Path]] = None,
        **kwargs
    ):
        """
        Initialize DataLoader.

        Args:
            source: Data source - can be:
                - Built-in dataset name (e.g., "bike-sharing-demand")
                - File path (e.g., "/path/to/data.csv")
                - Directory path (e.g., "/path/to/competition")
                - pandas DataFrame
            auto_detect: Automatically detect task type (default: False)
            registry_dir: Benchmark registry directory (optional)
            **kwargs: Additional metadata
        """
        self.source = source
        self.auto_detect = auto_detect
        self._data: Optional[Dict[str, pd.DataFrame]] = None
        self._detector = TaskDetector()
        self._task_detection: Optional[TaskDetection] = None

        # Store registry_dir for later use
        if registry_dir is not None:
            if isinstance(registry_dir, str):
                registry_dir = Path(registry_dir)
            self._registry_dir = registry_dir
        else:
            self._registry_dir = None

        # Load dataset info
        self.info = self._load_info(source, auto_detect, registry_dir, kwargs)

        logger.info(f"Loaded dataset: {self.info}")

    def _load_info(
        self,
        source: Union[str, Path, pd.DataFrame],
        auto_detect: bool,
        registry_dir: Optional[Union[str, Path]],
        metadata: Dict[str, Any]
    ) -> DatasetInfo:
        """Load dataset information and metadata."""
        source_path = Path(source) if isinstance(source, (str, Path)) else None

        # Detect task type or use MLE default
        if auto_detect:
            task_detection = self._detector.detect(source)
        else:
            task_detection = self._get_mle_detection(source)

        # Store task_detection for later use
        self._task_detection = task_detection

        # Extract paths
        data_dir = self._extract_data_dir(source, task_detection)
        task_id = self._extract_task_id(source, data_dir)

        # Auto-detect registry_dir
        if registry_dir is None:
            registry_dir = self._auto_detect_registry_dir(data_dir, task_id)
        elif isinstance(registry_dir, str):
            registry_dir = Path(registry_dir)

        # Store registry_dir
        self._registry_dir = registry_dir

        # Load task_type from registry config (if available)
        task_type_from_registry = load_task_type_from_registry(registry_dir, task_id, logger)
        if task_type_from_registry:
            # Override detected task_type with registry config
            task_detection = TaskDetection(
                task_type=task_type_from_registry,
                task_mode=task_detection.task_mode,
                data_dir=task_detection.data_dir,
                description=task_detection.description,
                io_instructions=task_detection.io_instructions,
                recommended_workflow=task_detection.recommended_workflow,
                confidence=1.0,  # High confidence for explicit config
            )
            self._task_detection = task_detection
            logger.info(f"Using task_type from registry config: {task_type_from_registry}")

        # Create DatasetInfo
        info = DatasetInfo(
            task_id=task_id,
            task_type=task_detection.task_type,
            task_mode=task_detection.task_mode,
            description=task_detection.description,
            io_instructions=task_detection.io_instructions,
            recommended_workflow=task_detection.recommended_workflow,
            data_dir=data_dir,
            registry_dir=registry_dir,
            metadata=metadata
        )

        return info

    def _get_mle_detection(self, source: Any) -> TaskDetection:
        """Get default MLE competition detection."""
        from dslighting.utils.defaults import WORKFLOW_RECOMMENDATIONS

        # Try to extract data directory
        data_dir = None
        description = "MLE competition task"

        if isinstance(source, (str, Path)):
            path = Path(source).resolve()
            logger.info(f"Resolved path: {path}")

            if path.exists():
                if path.is_dir():
                    data_dir = path
                    logger.info(f"Data directory found: {data_dir}")
                    # Try to load description
                    desc_file = path / "description.md"
                    if desc_file.exists():
                        try:
                            description = desc_file.read_text(encoding='utf-8')
                            logger.info(f"Loaded description from {desc_file}")
                        except (OSError, UnicodeDecodeError) as e:
                            logger.debug(f"Could not read description file {desc_file}: {e}")
                elif path.is_file():
                    data_dir = path.parent
                    logger.info(f"Data directory (from file parent): {data_dir}")
                    # Try to load description from parent directory
                    desc_file = path.parent / "description.md"
                    if desc_file.exists():
                        try:
                            description = desc_file.read_text(encoding='utf-8')
                            logger.info(f"Loaded description from {desc_file}")
                        except (OSError, UnicodeDecodeError) as e:
                            logger.debug(f"Could not read description file {desc_file}: {e}")
            else:
                # Path doesn't exist - try to find built-in dataset
                logger.warning(f"Path does not exist: {path}")
                competition_id = path.name

                # Try built-in datasets directory
                dataset_path = Path(__file__).parent.parent / "datasets" / competition_id
                if dataset_path.exists():
                    data_dir = dataset_path
                    logger.info(f"  ✓ Found built-in dataset at: {data_dir}")
                else:
                    # Try other common locations
                    search_locations = [
                        Path.cwd() / "data" / "competitions" / competition_id,
                        Path.cwd().parent / "dslighting" / "data" / "competitions" / competition_id,
                        Path(__file__).parent.parent.parent / "data" / "competitions" / competition_id,
                    ]

                    for location in search_locations:
                        logger.info(f"  Trying: {location}")
                        if location.exists() and location.is_dir():
                            data_dir = location
                            logger.info(f"  ✓ Found data at: {data_dir}")
                            break

                if data_dir is None:
                    logger.warning(f"  Could not find data, using original path: {path}")
                    data_dir = path

            # Try to load description (if data_dir was found)
            if data_dir and data_dir.exists():
                desc_file = data_dir / "description.md"
                if desc_file.exists():
                    try:
                        description = desc_file.read_text(encoding='utf-8')
                        logger.info(f"Loaded description from {desc_file}")
                    except (OSError, UnicodeDecodeError) as e:
                        logger.debug(f"Could not read description file {desc_file}: {e}")

        return TaskDetection(
            task_type="kaggle",
            task_mode="standard_ml",
            data_dir=data_dir,
            description=description,
            io_instructions="Train a model and generate predictions for the test set.",
            recommended_workflow=WORKFLOW_RECOMMENDATIONS.get("kaggle_competition", {}).get("default", "aide"),
            confidence=1.0,
            metadata={"structure": "mle_competition", "auto_detected": False}
        )

    def _extract_data_dir(self, source: Any, detection: TaskDetection) -> Optional[Path]:
        """Extract data directory from source and detection."""
        if detection.data_dir:
            return detection.data_dir

        if isinstance(source, (str, Path)):
            path = Path(source)
            if path.is_file():
                return path.parent
            elif path.is_dir():
                return path

        return None

    def _extract_task_id(self, source: Any, data_dir: Optional[Path]) -> Optional[str]:
        """Extract task/competition ID."""
        if isinstance(source, (str, Path)):
            path = Path(source)
            if path.is_file():
                return path.parent.name
            if path.is_dir():
                return path.name

        if data_dir:
            return data_dir.name

        return None

    def _auto_detect_registry_dir(
        self,
        data_dir: Optional[Path],
        task_id: Optional[str]
    ) -> Optional[Path]:
        """Auto-detect MLE-Bench registry directory."""
        if not data_dir:
            return None

        logger.info(f"Auto-detecting registry directory for data_dir: {data_dir}")

        # Try to find benchmark/ sibling to data/
        if data_dir.is_absolute():
            current = data_dir
            for _ in range(5):
                if current.parent.name == "data":
                    benchmarks_root = current.parent.parent / "benchmark" / "vendor" / "mlebench" / "competitions"
                    if benchmarks_root.exists():
                        logger.info(f"  ✓ Found benchmark registry at: {benchmarks_root}")
                        return benchmarks_root
                current = current.parent

        # Try package structure
        try:
            file_location = Path(__file__).resolve()
            dslighting_root = file_location.parent.parent.parent
            benchmarks_root = dslighting_root / "benchmark" / "vendor" / "mlebench" / "competitions"

            if benchmarks_root.exists():
                logger.info(f"  ✓ Found benchmark registry from package structure: {benchmarks_root}")
                return benchmarks_root
        except (OSError, RuntimeError) as e:
            logger.debug(f"Could not determine package structure: {e}")

        logger.warning("  ⚠️  Could not auto-detect registry directory")
        return None

    def load(self) -> "DataLoader":
        """
        Load data into memory (lazy loading).

        Returns:
            self (for method chaining)

        Example:
            >>> loader = dslighting.load_dataset("bike-sharing-demand")
            >>> loader.load()
            >>> print(loader.train.head())
        """
        if self._data is not None:
            logger.info("Data already loaded")
            return self

        logger.info("Loading data into memory...")
        self._data = {}

        if self.info.data_dir and self.info.data_dir.exists():
            # Try MLE format: prepared/public
            public_dir = self.info.data_dir / "prepared" / "public"

            if public_dir.exists():
                # Load train.csv, test.csv, etc.
                for csv_file in public_dir.glob("*.csv"):
                    name = csv_file.stem  # filename without .csv
                    try:
                        self._data[name] = pd.read_csv(csv_file)
                        logger.info(f"  Loaded {name} from {csv_file}")
                    except Exception as e:
                        logger.warning(f"  Failed to load {csv_file}: {e}")
            else:
                # Load all CSV files from data_dir
                for csv_file in self.info.data_dir.glob("*.csv"):
                    name = csv_file.stem
                    try:
                        self._data[name] = pd.read_csv(csv_file)
                        logger.info(f"  Loaded {name} from {csv_file}")
                    except Exception as e:
                        logger.warning(f"  Failed to load {csv_file}: {e}")

        logger.info("Data loading complete")
        return self

    @property
    def train(self) -> Optional[pd.DataFrame]:
        """Get training data (loads if not already loaded)."""
        self.load()
        return self._data.get("train")

    @property
    def test(self) -> Optional[pd.DataFrame]:
        """Get test data (loads if not already loaded)."""
        self.load()
        return self._data.get("test")

    @property
    def sample_submission(self) -> Optional[pd.DataFrame]:
        """Get sample submission (loads if not already loaded)."""
        self.load()
        # Try both possible key names
        if "sampleSubmission" in self._data:
            return self._data["sampleSubmission"]
        elif "sample_submission" in self._data:
            return self._data["sample_submission"]
        return None

    @property
    def data(self) -> Dict[str, pd.DataFrame]:
        """Get all loaded data as a dictionary."""
        self.load()
        return self._data

    # =========================================================================
    # DataLoader compatibility methods (aliases for load with different sources)
    # =========================================================================

    def load_csv(self, path: Union[str, Path], **kwargs) -> "DataLoader":
        """
        Load data from a CSV file.

        Args:
            path: Path to CSV file
            **kwargs: Additional parameters passed to pd.read_csv

        Returns:
            self (for method chaining)

        Example:
            >>> loader = DataLoader()
            >>> loader.load_csv("train.csv")
        """
        path = Path(path)
        logger.info(f"Loading CSV file: {path}")
        self.source = path
        # Re-initialize with the new source
        self._data = None
        self.info = self._load_info(path, self.auto_detect, self.info.registry_dir, kwargs)
        logger.info(f"Loaded CSV: {self.info}")
        return self

    def load_directory(self, path: Union[str, Path], **kwargs) -> "DataLoader":
        """
        Load data from a directory.

        Args:
            path: Path to directory
            **kwargs: Additional parameters

        Returns:
            self (for method chaining)

        Example:
            >>> loader = DataLoader()
            >>> loader.load_directory("/path/to/data")
        """
        path = Path(path)
        logger.info(f"Loading directory: {path}")

        if not path.is_dir():
            raise ValueError(f"Not a directory: {path}")

        self.source = path
        self._data = None
        self.info = self._load_info(path, self.auto_detect, self.info.registry_dir, kwargs)
        logger.info(f"Loaded directory: {self.info}")
        return self

    def load_dataframe(self, df: pd.DataFrame, **kwargs) -> "DataLoader":
        """
        Load data from a pandas DataFrame.

        Args:
            df: Pandas DataFrame
            **kwargs: Additional parameters

        Returns:
            self (for method chaining)

        Example:
            >>> loader = DataLoader()
            >>> loader.load_dataframe(df)
        """
        logger.info(f"Loading DataFrame with shape {df.shape}")
        self.source = df
        self._data = None
        self.info = self._load_info(df, self.auto_detect, self.info.registry_dir, kwargs)
        logger.info(f"Loaded DataFrame: {self.info}")
        return self

    def load_competition(
        self,
        competition_id: str,
        data_dir: Union[str, Path] = None,
        **kwargs
    ) -> "DataLoader":
        """
        Load data from a competition (MLE-Bench style).

        Args:
            competition_id: Competition identifier
            data_dir: Base data directory containing competitions
            **kwargs: Additional parameters

        Returns:
            self (for method chaining)

        Example:
            >>> loader = DataLoader()
            >>> loader.load_competition("bike-sharing-demand")
        """
        logger.info(f"Loading competition: {competition_id}")

        # Default to data/competitions directory
        if data_dir is None:
            data_dir = Path("data/competitions") / competition_id
        else:
            data_dir = Path(data_dir) / competition_id

        if not data_dir.exists():
            raise ValueError(f"Competition directory not found: {data_dir}")

        self.source = data_dir
        self._data = None
        self.info = self._load_info(data_dir, self.auto_detect, self.info.registry_dir, kwargs)
        logger.info(f"Loaded competition: {self.info}")
        return self

    def load_question(self, question: str, **kwargs) -> "DataLoader":
        """
        Load a QA question.

        Args:
            question: Question text
            **kwargs: Additional parameters

        Returns:
            self (for method chaining)

        Example:
            >>> loader = DataLoader()
            >>> loader.load_question("What is the average fare?")
        """
        logger.info("Loading QA question")
        self.source = question
        self._data = None
        self.info = self._load_info(question, self.auto_detect, self.info.registry_dir, kwargs)
        logger.info(f"Loaded question: {self.info}")
        return self

    # =========================================================================
    # Convenience properties for accessing metadata (DataLoader compatibility)
    # =========================================================================

    @property
    def data_dir(self) -> Optional[Path]:
        """Get data directory path."""
        return self.info.data_dir

    @property
    def task_detection(self) -> Optional[TaskDetection]:
        """Get task detection result."""
        # Return a TaskDetection-like object based on info
        if hasattr(self, '_task_detection'):
            return self._task_detection
        return TaskDetection(
            task_type=self.info.task_type,
            task_mode=self.info.task_mode,
            data_dir=self.info.data_dir,
            description=self.info.description,
            io_instructions=self.info.io_instructions,
            recommended_workflow=self.info.recommended_workflow,
        )

    @property
    def task_id(self) -> Optional[str]:
        """Get task ID."""
        return self.info.task_id

    @property
    def registry_dir(self) -> Optional[Path]:
        """Get registry directory path."""
        return self.info.registry_dir

    def get_submission_contract(self) -> Dict[str, Any]:
        """Get normalized submission contract from metadata or template inference."""
        metadata = self.info.metadata if isinstance(self.info.metadata, dict) else {}

        cached_contract = normalize_submission_tag_contract(
            metadata.get("submission_contract")
        )
        if cached_contract:
            metadata["submission_contract"] = cached_contract
            self.info.metadata = metadata
            return cached_contract

        data_dir = self.info.data_dir
        if not data_dir or not data_dir.exists():
            contract = extract_submission_tag_contract(None)
            metadata["submission_contract"] = contract
            self.info.metadata = metadata
            return contract

        submission_context = metadata.get("submission_context")
        context = submission_context if isinstance(submission_context, dict) else {}

        sample_submission_file = find_sample_submission_file(
            data_dir,
            sample_submission_path=str(context.get("sample_submission_path", "") or ""),
            submission_filename=str(context.get("submission_filename", "") or ""),
        )
        contract = extract_submission_tag_contract(sample_submission_file)
        metadata["submission_contract"] = contract
        self.info.metadata = metadata
        return contract

    def get_submission_reminder(self) -> str:
        """Get standardized submission reminder block for tagged templates."""
        return build_tag_contract_reminder(self.get_submission_contract())

    # =========================================================================
    # show() method (from TaskContext)
    # =========================================================================

    def show(self) -> str:
        """
        Display detailed data structure and schema information.

        This shows what the Agent sees - file structure, data schema,
        and task information. Use this to understand your data before
        running the Agent.

        Returns:
            Formatted string with data structure and schema

        Example:
            >>> dataset = dslighting.load_dataset("bike-sharing-demand")
            >>> print(dataset.show())
        """
        lines = []
        lines.append("=" * 80)
        lines.append("DSLighting Data Overview")
        lines.append("=" * 80)
        lines.append("")

        # Task Information
        lines.append("## Task Information")
        lines.append(f"  Task ID:          {self.info.task_id or 'N/A'}")
        lines.append(f"  Task Type:        {self.info.task_type}")
        lines.append(f"  Task Mode:        {self.info.task_mode or 'N/A'}")
        lines.append(f"  Recommended:      {self.info.recommended_workflow or 'aide'} workflow")
        lines.append("")

        # Data Directory
        if self.info.data_dir:
            lines.append("## Data Directory")
            lines.append(f"  Path:             {self.info.data_dir}")
            lines.append(f"  Exists:          {self.info.data_dir.exists()}")
            lines.append("")

        # Data Schema
        lines.append("## Data Schema")
        if self.info.data_dir:
            public_dir = self.info.data_dir / "prepared" / "public"
            data_dir = public_dir if public_dir.exists() else self.info.data_dir

            for csv_file in sorted(data_dir.glob("*.csv")):
                name = csv_file.stem
                try:
                    df = pd.read_csv(csv_file, nrows=0)
                    lines.append(f"  {name}: {len(df.columns)} columns")
                    lines.append(f"       Columns: {', '.join(list(df.columns[:5]))}")
                    if len(df.columns) > 5:
                        lines.append(f"                ... and {len(df.columns) - 5} more")
                except Exception:
                    lines.append(f"  {name}: (unable to read)")

        lines.append("")

        # Submission Format
        lines.append("## Submission Format")
        lines.append(f"  Expected:         {self.info.metadata.get('submission_format', 'auto-detect')}")
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

    def __repr__(self) -> str:
        """Return concise representation."""
        if self.info.task_id:
            return f"DataLoader('{self.info.task_id}', task_type='{self.info.task_type}')"
        return f"DataLoader(task_type='{self.info.task_type}')"

    def get_agent_report(self, output_filename: str = None) -> str:
        """
        Get the comprehensive data report that Agent sees.

        This method uses the same DataAnalyzer service that Agent uses,
        ensuring consistency with what the Agent receives.

        Args:
            output_filename: Optional output filename for I/O instructions

        Returns:
            Comprehensive data report (structure, schema, I/O instructions)

        Example:
            >>> dataset = dslighting.load_dataset("bike-sharing-demand")
            >>> print(dataset.get_agent_report())
        """
        if not self.info.data_dir:
            return "Error: No data directory available"

        try:
            # Import the DataAnalyzer service that Agent uses
            from dslighting.services.data_analyzer import DataAnalyzer

            analyzer = DataAnalyzer()

            # Use the same task type string used by runner/data analyzer.
            task_type = self.info.task_type if self.info.task_type else None

            # Generate the full report (data + I/O instructions)
            output_filename = output_filename or "submission.csv"
            report = analyzer.analyze(
                data_dir=self.info.data_dir,
                output_filename=output_filename,
                task_type=task_type,
                task_id=self.info.task_id,
            )

            return report

        except ImportError as e:
            logger.error(f"Failed to import DataAnalyzer service: {e}", exc_info=True)
            logger.info("Falling back to basic dataset display")
            return self.show()

    def _analyze_directory(
        self,
        directory: Path,
        title: str,
        include_samples: bool = True,
        max_samples: int = 3
    ) -> str:
        """Analyze directory and return detailed schema information."""
        lines = []
        lines.append(f"\n  ### {title}")

        try:
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
                        # Read header and schema
                        df = pd.read_csv(file_path, nrows=0)

                        # Show basic info
                        lines.append(f"     Rows: {self._count_rows(file_path)}")
                        lines.append(f"     Columns ({len(df.columns)}): {', '.join(list(df.columns[:5]))}")
                        if len(df.columns) > 5:
                            lines.append(f"                ... and {len(df.columns) - 5} more")

                        # Show data types
                        lines.append(f"     Schema:")
                        for col in list(df.columns)[:5]:
                            dtype = str(df[col].dtype)
                            lines.append(f"       - {col}: {dtype}")
                        if len(df.columns) > 5:
                            lines.append(f"       ... and {len(df.columns) - 5} more")

                        # Show sample data
                        if include_samples:
                            lines.append(f"     Sample data (first {max_samples} rows):")
                            df_sample = pd.read_csv(file_path, nrows=max_samples)
                            for idx, row in df_sample.iterrows():
                                lines.append(f"       Row {idx}:")
                                for col in list(df_sample.columns)[:5]:
                                    val = str(row[col])[:30]
                                    if len(str(row[col])) > 30:
                                        val += "..."
                                    lines.append(f"         - {col}: {val}")
                                if len(df_sample.columns) > 5:
                                    lines.append(f"         ... and {len(df_sample.columns) - 5} more columns")
                                if idx >= max_samples - 1:
                                    break

                    except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError) as e:
                        lines.append(f"     [Error reading file: {e}]")

        except OSError as e:
            lines.append(f"  [Error analyzing directory: {e}]")

        return "\n".join(lines)

    def _count_rows(self, file_path: Path) -> int:
        """Count rows in a CSV file efficiently."""
        try:
            with open(file_path, 'r') as f:
                return sum(1 for _ in f) - 1  # Subtract header row
        except OSError:
            return 0

    def to_dataframe(self) -> Optional[pd.DataFrame]:
        """
        Get main data as DataFrame (if single file).

        Returns:
            DataFrame or None if multiple files
        """
        self.load()

        if len(self._data) == 1:
            return list(self._data.values())[0]
        elif "train" in self._data:
            return self._data["train"]
        else:
            return None


# Convenience function (similar to HuggingFace's load_dataset)
def load_dataset(
    source: Union[str, Path, pd.DataFrame],
    auto_detect: bool = False,
    registry_dir: Optional[Union[str, Path]] = None,
    **kwargs
) -> DataLoader:
    """
    Load a dataset (convenience function).

    This is the recommended way to load datasets, following the pattern
    of HuggingFace's load_dataset().

    Args:
        source: Data source (name, path, or DataFrame)
        auto_detect: Auto-detect task type
        registry_dir: Registry directory
        **kwargs: Additional metadata

    Returns:
        DataLoader object

    Examples:
        >>> import dslighting
        >>> loader = dslighting.load_dataset("bike-sharing-demand")
        >>> print(loader.info)
        >>> loader.load()
        >>> train_df = loader.train
    """
    return DataLoader(source, auto_detect=auto_detect, registry_dir=registry_dir, **kwargs)


__all__ = [
    "DataLoader",
    "DatasetInfo",
    "load_dataset",
]
