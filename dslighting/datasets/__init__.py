"""
Example datasets module for DSLighting.

This module provides easy access to example datasets that can be used
to test and explore the DSLighting package.

Available function:
    - load_example: Load a dataset by name
"""

import atexit
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional
import pandas as pd


# Track temporary directories for cleanup
_temp_dirs: list[str] = []


def _cleanup_temp_dirs() -> None:
    """
    Clean up all temporary directories created during dataset loading.
    This function is automatically called at program exit.
    """
    for temp_dir in _temp_dirs:
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception:
            pass  # Ignore errors during cleanup


# Register cleanup function to run at exit
atexit.register(_cleanup_temp_dirs)


def get_data_path() -> Path:
    """
    Get the path to the datasets directory.

    Returns:
        Path to the datasets directory
    """
    return Path(__file__).parent.absolute()


def list_datasets() -> list[str]:
    """
    List available example datasets.

    Returns:
        List of dataset names
    """
    data_path = get_data_path()
    datasets = []
    for item in data_path.iterdir():
        if item.is_dir() and not item.name.startswith('_'):
            datasets.append(item.name)
    return sorted(datasets)


def load_example(name: str, data_dir: Optional[str] = None) -> dict:
    """
    Load a dataset by name and create the directory structure.

    Args:
        name: Name of the dataset (e.g., 'bike-sharing-demand')
        data_dir: Base data directory. If None, uses a temporary directory
            that will be automatically cleaned up at program exit.

    Returns:
        Dictionary with keys:
            - 'task_id': Dataset name
            - 'data_dir': Path to the competition directory
            - 'prepared_dir': Path to prepared/public directory
            - 'data': Raw data dict with 'train', 'test', etc.

    Example:
        >>> import dslighting
        >>> info = dslighting.datasets.load_example('bike-sharing-demand')
        >>> print(f"Data directory: {info['data_dir']}")
    """
    name = name.lower().replace('_', '-')
    data_path = get_data_path() / name

    if not data_path.exists():
        available = list_datasets()
        raise ValueError(
            f"Dataset '{name}' not found. Available datasets: {available}"
        )

    # Load raw data
    public_dir = data_path / "prepared" / "public"
    private_dir = data_path / "prepared" / "private"

    raw_data = {
        'train': pd.read_csv(public_dir / "train.csv"),
        'test': pd.read_csv(public_dir / "test.csv"),
        'sample_submission': pd.read_csv(public_dir / "sampleSubmission.csv"),
    }

    test_answer_path = private_dir / "test_answer.csv"
    if test_answer_path.exists():
        raw_data['test_answer'] = pd.read_csv(test_answer_path)

    # Determine output directory
    if data_dir is None:
        temp_base = tempfile.mkdtemp(prefix='dslighting_')
        _temp_dirs.append(temp_base)
        competition_dir = Path(temp_base) / name
    else:
        competition_dir = Path(data_dir) / name

    prepared_dir = competition_dir / "prepared" / "public"
    prepared_dir.mkdir(parents=True, exist_ok=True)
    private_dir_out = competition_dir / "prepared" / "private"
    private_dir_out.mkdir(parents=True, exist_ok=True)

    # Copy data files
    raw_data['train'].to_csv(prepared_dir / "train.csv", index=False)
    raw_data['test'].to_csv(prepared_dir / "test.csv", index=False)
    raw_data['sample_submission'].to_csv(prepared_dir / "sampleSubmission.csv", index=False)
    if 'test_answer' in raw_data:
        raw_data['test_answer'].to_csv(private_dir_out / "test_answer.csv", index=False)

    return {
        'task_id': name,
        'data_dir': competition_dir,
        'prepared_dir': prepared_dir,
        'data': raw_data
    }


__all__ = [
    "get_data_path",
    "list_datasets",
    "load_example",
]
