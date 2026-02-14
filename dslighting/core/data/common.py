"""
Common data loading utilities shared by DataLoader and Dataset.

This module contains shared functionality to avoid code duplication between
loader.py and dataset.py.
"""

import logging
from pathlib import Path
from typing import Any, Optional, Union

from dslighting.core.detection.detector import TaskDetector, TaskDetection

logger = logging.getLogger(__name__)


class BaseDataLoader:
    """
    Base class for data loading functionality.

    Provides common methods for path resolution, task detection, and
    registry directory detection used by both DataLoader and Dataset.
    """

    def __init__(self, auto_detect: bool = False):
        """
        Initialize base data loader.

        Args:
            auto_detect: Whether to automatically detect task type
        """
        self.auto_detect = auto_detect
        self.detector = TaskDetector()
        self.logger = logger

    def detect_task_type(
        self,
        source: Any,
        default_to_mle: bool = True
    ) -> TaskDetection:
        """
        Detect task type from source.

        Args:
            source: Data source (path, DataFrame, etc.)
            default_to_mle: If True, return MLE detection when auto-detect is off

        Returns:
            TaskDetection with task type information
        """
        if self.auto_detect:
            return self.detector.detect(source)
        elif default_to_mle:
            return self._get_default_mle_detection(source)
        else:
            return TaskDetection(
                task_type="unknown",
                task_mode="unknown",
                description="Unknown task type",
            )

    def _get_default_mle_detection(self, source: Any) -> TaskDetection:
        """Get default MLE competition detection."""
        return TaskDetection(
            task_type="datasci",
            task_mode="standard_ml",
            description="MLE competition task",
            io_instructions="",
            recommended_workflow="autokaggle",
        )

    def resolve_data_dir(
        self,
        source: Any,
        task_detection: TaskDetection
    ) -> Optional[Path]:
        """
        Resolve data directory from source.

        Args:
            source: Data source
            task_detection: Task detection result

        Returns:
            Path to data directory or None
        """
        if isinstance(source, (str, Path)):
            path = Path(source).resolve()

            if path.exists():
                if path.is_dir():
                    return path
                elif path.is_file():
                    return path.parent

        # If task_detection has a data_dir, use it
        if hasattr(task_detection, 'data_dir') and task_detection.data_dir:
            return Path(task_detection.data_dir)

        return None

    def extract_task_id(
        self,
        source: Any,
        data_dir: Optional[Path]
    ) -> Optional[str]:
        """
        Extract task ID from source.

        Args:
            source: Data source
            data_dir: Data directory path

        Returns:
            Task ID string or None
        """
        if isinstance(source, (str, Path)):
            path = Path(source)

            if path.is_dir():
                return path.name
            elif path.is_file():
                # Try to get task ID from parent directory name
                if data_dir:
                    return data_dir.name
                return path.stem

        return None

    def auto_detect_registry_dir(
        self,
        data_dir: Optional[Path],
        task_id: Optional[str]
    ) -> Optional[Path]:
        """
        Auto-detect registry directory from data directory.

        Args:
            data_dir: Data directory path
            task_id: Task ID

        Returns:
            Path to registry directory or None
        """
        if not data_dir:
            return None

        # Common registry directory patterns
        candidates = [
            # MLE-Bench vendor directory
            data_dir.parent.parent.parent.parent / "benchmark" / "vendor" / "mlebench",
            # Alternative patterns
            data_dir.parent.parent / "registry",
            Path.cwd() / "benchmark" / "vendor" / "mlebench",
        ]

        for candidate in candidates:
            if candidate.exists() and (candidate / "competitions").exists():
                self.logger.info(f"Auto-detected registry_dir: {candidate}")
                return candidate

        return None


def validate_data_source(source: Any) -> None:
    """
    Validate that a data source is of a supported type.

    Args:
        source: Data source to validate

    Raises:
        TypeError: If source type is not supported
    """
    if source is None:
        raise TypeError("Data source cannot be None")

    supported_types = (str, Path, dict)
    if not isinstance(source, supported_types):
        raise TypeError(
            f"Data source must be a path (str/Path), dict, or pandas DataFrame. "
            f"Got {type(source).__name__}"
        )


def resolve_path(path: Union[str, Path]) -> Path:
    """
    Resolve a path to an absolute Path object.

    Args:
        path: Path to resolve

    Returns:
        Resolved absolute Path
    """
    return Path(path).resolve()
