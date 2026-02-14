"""
Data loader utility functions.

This module contains helper functions extracted from DataLoader class
to improve code organization and maintainability.

These functions handle data directory detection, task ID extraction,
registry auto-detection, and other data loading utilities.
"""

import logging
from pathlib import Path
from typing import Any, Optional

from dslighting.core.detection.detector import TaskDetection

logger = logging.getLogger(__name__)


def get_default_mle_detection(
    source: Any,
    logger_instance: Optional[logging.Logger] = None
) -> TaskDetection:
    """
    Get default MLE competition detection for any data source.

    This function treats all data as MLE format (prepared/public & prepared/private).
    It extracts the data directory if available.

    Args:
        source: Data source (path, DataFrame, dict, etc.)
        logger_instance: Logger instance for output (uses module logger if None)

    Returns:
        TaskDetection configured for MLE competition
    """
    log = logger_instance or logger
    log.info("Using default MLE competition format (prepared/public & prepared/private)")
    log.info(f"[get_default_mle_detection] Processing source: {type(source).__name__}")

    # Try to extract data directory
    data_dir = None
    description = "MLE competition task"

    if isinstance(source, (str, Path)):
        path = Path(source).resolve()  # Convert to absolute path
        log.info(f"Resolved path: {path}")

        if path.exists():
            if path.is_dir():
                data_dir = path
                log.info(f"Data directory found: {data_dir}")
                # Try to load description
                desc_file = path / "description.md"
                if desc_file.exists():
                    try:
                        description = desc_file.read_text(encoding='utf-8')
                        log.info(f"Loaded description from {desc_file}")
                    except (OSError, UnicodeDecodeError) as e:
                        log.debug(f"Could not read description file {desc_file}: {e}")
            elif path.is_file():
                data_dir = path.parent
                log.info(f"Data directory (from file parent): {data_dir}")
                # Try to load description from parent directory
                desc_file = path.parent / "description.md"
                if desc_file.exists():
                    try:
                        description = desc_file.read_text(encoding='utf-8')
                        log.info(f"Loaded description from {desc_file}")
                    except (OSError, UnicodeDecodeError) as e:
                        log.debug(f"Could not read description file {desc_file}: {e}")
        else:
            log.warning(f"Path does not exist: {path}")

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
            ]

            for location in search_locations:
                log.info(f"  Trying: {location}")
                if location.exists() and location.is_dir():
                    data_dir = location
                    log.info(f"  ✓ Found data at: {data_dir}")
                    break

            if data_dir is None:
                # Last resort: use the original resolved path
                log.warning(f"  Could not find data, using original path: {path}")
                data_dir = path

        # Try to load description (if data_dir was found)
        if data_dir and data_dir.exists():
            desc_file = data_dir / "description.md"
            if desc_file.exists():
                try:
                    description = desc_file.read_text(encoding='utf-8')
                    log.info(f"Loaded description from {desc_file}")
                except (OSError, UnicodeDecodeError) as e:
                    log.debug(f"Could not read description file {desc_file}: {e}")

    # Create MLE-style detection
    from dslighting.utils.defaults import WORKFLOW_RECOMMENDATIONS

    task_detection = TaskDetection(
        task_type="kaggle",  # MLE uses kaggle task type internally
        task_mode="standard_ml",
        data_dir=data_dir,
        description=description,
        io_instructions="Train a model and generate predictions for the test set.",
        recommended_workflow=WORKFLOW_RECOMMENDATIONS.get("kaggle_competition", {}).get("default", "aide"),
        confidence=1.0,  # High confidence since this is explicit user intent
        metadata={"structure": "mle_competition", "auto_detected": False}
    )
    log.info(f"[get_default_mle_detection] Created TaskDetection with task_type={task_detection.task_type}")

    return task_detection


def extract_data_dir(
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


def extract_task_id(
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


def auto_detect_registry_dir(
    data_dir: Optional[Path],
    task_id: Optional[str],
    logger_instance: Optional[logging.Logger] = None
) -> Optional[Path]:
    """
    Auto-detect MLE-Bench registry directory from data directory structure.

    The registry contains competition configs (config.yaml) with grading information.
    This function looks for the benchmark registry directory relative to the data directory.

    Args:
        data_dir: Data directory path
        task_id: Task/competition ID
        logger_instance: Logger instance for output (uses module logger if None)

    Returns:
        Path to registry directory or None
    """
    log = logger_instance or logger

    if not data_dir:
        return None

    log.info(f"Auto-detecting registry directory for data_dir: {data_dir}")

    # Expected structure:
    # dslighting/
    #   ├── data/competitions/{task_id}/     <- data_dir points here
    #   └── benchmark/vendor/mlebench/competitions/ <- registry we need to find

    # Strategy 1: Look for benchmark/ sibling to data/
    if data_dir.is_absolute():
        # data_dir = /path/to/dslighting/data/competitions/bike-sharing-demand
        # We want: /path/to/dslighting/benchmark/vendor/mlebench/competitions

        # Go up to find data/, then look for benchmark/ sibling
        current = data_dir
        for _ in range(5):  # Don't go up more than 5 levels
            if current.parent.name == "data":
                # Found data/ directory, look for benchmark/ sibling
                benchmarks_root = current.parent.parent / "benchmark" / "vendor" / "mlebench" / "competitions"
                if benchmarks_root.exists():
                    log.info(f"  ✓ Found benchmark registry at: {benchmarks_root}")
                    return benchmarks_root
                break
            current = current.parent

    # Strategy 2: Check package-relative benchmark location
    try:
        # dslighting/core/data/loader_utils.py -> dslighting/
        file_location = Path(__file__).resolve()
        dslighting_root = file_location.parent.parent.parent  # Up 3 levels
        benchmarks_root = dslighting_root / "benchmark" / "vendor" / "mlebench" / "competitions"

        if benchmarks_root.exists():
            log.info(f"  ✓ Found benchmark registry from package structure: {benchmarks_root}")
            return benchmarks_root
    except (OSError, RuntimeError) as e:
        log.debug(f"  Could not determine package structure: {e}")

    # Could not auto-detect
    log.warning("  ⚠️  Could not auto-detect registry directory")
    log.warning("     Pass registry_dir explicitly to load_data() or Agent.run()")
    log.warning("     Example: load_data(path, registry_dir='path/to/benchmark/vendor/mlebench/competitions')")

    return None


def load_task_type_from_registry(
    registry_dir: Optional[Path],
    task_id: Optional[str],
    logger_instance: Optional[logging.Logger] = None
) -> Optional[str]:
    """
    Load task_type from registry config.yaml (if available).

    This allows tasks to explicitly specify their type instead of relying on auto-detection.

    Args:
        registry_dir: Registry directory path
        task_id: Task/competition ID
        logger_instance: Logger instance for output (uses module logger if None)

    Returns:
        task_type string (e.g., "kaggle", "open_ended") or None if not found
    """
    log = logger_instance or logger

    if not registry_dir or not task_id:
        return None

    try:
        # Check if config.yaml exists in registry
        config_path = registry_dir / task_id / "config.yaml"
        if not config_path.exists():
            log.debug(f"  No registry config found at: {config_path}")
            return None

        # Load config.yaml
        import yaml
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        # Extract task_type (default to "kaggle" if not specified)
        task_type = config.get("task_type", "kaggle")

        log.info(f"  ✓ Loaded task_type from registry config: {task_type}")
        return task_type

    except (OSError, yaml.YAMLError) as e:
        log.debug(f"  Failed to load task_type from registry: {e}")
        return None
