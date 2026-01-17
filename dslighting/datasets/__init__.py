"""
Example datasets module for DSLighting.

This module provides easy access to example datasets that can be used
to test and explore the DSLighting package.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional
import pandas as pd


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


def load_bike_sharing_demand_raw() -> dict:
    """
    Load the Bike Sharing Demand dataset as raw DataFrames.

    This returns the raw data files as DataFrames in a dictionary.
    Use this if you want to access the data directly.

    Note: Data files are in prepared/public and prepared/private structure.

    Returns:
        Dictionary with keys:
            - 'train': Training DataFrame
            - 'test': Test DataFrame
            - 'sample_submission': Sample submission DataFrame
            - 'test_answer': Test answers (for evaluation)

    Example:
        >>> import dslighting
        >>> data = dslighting.datasets.load_bike_sharing_demand_raw()
        >>> train_df = data['train']
        >>> test_df = data['test']
        >>> print(train_df.head())
    """
    data_path = get_data_path() / "bike-sharing-demand"

    if not data_path.exists():
        raise FileNotFoundError(
            f"Bike Sharing Demand dataset not found at {data_path}. "
            "Please reinstall the package."
        )

    data = {}
    # Load from prepared/public directory
    public_dir = data_path / "prepared" / "public"
    private_dir = data_path / "prepared" / "private"

    data['train'] = pd.read_csv(public_dir / "train.csv")
    data['test'] = pd.read_csv(public_dir / "test.csv")
    data['sample_submission'] = pd.read_csv(public_dir / "sampleSubmission.csv")

    # Load test_answer from prepared/private
    test_answer_path = private_dir / "test_answer.csv"
    if test_answer_path.exists():
        data['test_answer'] = pd.read_csv(test_answer_path)

    return data


def load_bike_sharing_demand(data_dir: Optional[str] = None) -> dict:
    """
    Load the Bike Sharing Demand dataset as a ready-to-use competition.

    The dataset already follows the MLE-Bench standard structure with
    prepared/public and prepared/private directories.

    Args:
        data_dir: Base data directory. If None, uses the built-in dataset location.

    Returns:
        Dictionary with keys:
            - 'task_id': 'bike-sharing-demand'
            - 'data_dir': Path to the competition directory
            - 'prepared_dir': Path to prepared/public directory
            - 'data': Raw data dict (for direct access)

    Example:
        >>> import dslighting
        >>> info = dslighting.datasets.load_bike_sharing_demand()
        >>> print(f"Data directory: {info['data_dir']}")
        >>>
        >>> # Now you can run the agent
        >>> agent = dslighting.Agent()
        >>> result = agent.run(
        ...     task_id="bike-sharing-demand",
        ...     data_dir=str(info['data_dir'].parent)
        ... )
    """
    # Load raw data (from prepared/public and prepared/private structure)
    raw_data = load_bike_sharing_demand_raw()

    # Determine data directory
    if data_dir is None:
        # Use built-in dataset location
        competition_dir = get_data_path() / "bike-sharing-demand"
    else:
        # Create directory structure in specified location
        data_dir = Path(data_dir)
        competition_dir = data_dir / "bike-sharing-demand"

        # Create prepared/public and prepared/private structure
        prepared_dir = competition_dir / "prepared" / "public"
        prepared_dir.mkdir(parents=True, exist_ok=True)

        # Copy data files
        raw_data['train'].to_csv(prepared_dir / "train.csv", index=False)
        raw_data['test'].to_csv(prepared_dir / "test.csv", index=False)
        raw_data['sample_submission'].to_csv(prepared_dir / "sampleSubmission.csv", index=False)

        # Create private directory with answers
        private_dir = competition_dir / "prepared" / "private"
        private_dir.mkdir(parents=True, exist_ok=True)
        raw_data['test_answer'].to_csv(private_dir / "test_answer.csv", index=False)

    prepared_dir = competition_dir / "prepared" / "public"

    return {
        'task_id': 'bike-sharing-demand',
        'data_dir': competition_dir,
        'prepared_dir': prepared_dir,
        'data': raw_data
    }


def load_dataset(name: str, data_dir: Optional[str] = None) -> dict:
    """
    Load a dataset by name and create the directory structure.

    Args:
        name: Name of the dataset (e.g., 'bike-sharing-demand')
        data_dir: Base data directory. If None, uses a temporary directory.

    Returns:
        Dictionary containing dataset information

    Example:
        >>> import dslighting
        >>> info = dslighting.datasets.load_dataset('bike-sharing-demand')
        >>> print(f"Data directory: {info['data_dir']}")
    """
    name = name.lower().replace('_', '-')

    if name == 'bike-sharing-demand':
        return load_bike_sharing_demand(data_dir=data_dir)
    else:
        available = list_datasets()
        raise ValueError(
            f"Dataset '{name}' not found. Available datasets: {available}"
        )


__all__ = [
    "get_data_path",
    "list_datasets",
    "load_bike_sharing_demand",
    "load_bike_sharing_demand_raw",
    "load_dataset",
]
