"""
Data loading and processing module.

This module provides a unified interface for data loading:

DataLoader (PRIMARY) - Unified data loading and management
   - Simple: DataLoader(source).load()
   - Lazy loading of data
   - Rich metadata access via .info
   - Direct access to train/test DataFrames
   - Agent report generation

Examples:
    >>> from dslighting.core.data import DataLoader, load_dataset
    >>> loader = DataLoader("bike-sharing-demand")
    >>> loader.load()
    >>> train_df = loader.train

    >>> # Or use the convenience function
    >>> loader = load_dataset("bike-sharing-demand")
"""

# Common utilities
from .common import BaseDataLoader, validate_data_source, resolve_path

# Core data classes - unified DataLoader
from .dataset import DataLoader, DatasetInfo, load_dataset
from .context import TaskContext
from .loader_utils import *

__all__ = [
    # Common utilities
    "BaseDataLoader",
    "validate_data_source",
    "resolve_path",
    # Core data classes - DataLoader is the primary class
    "DataLoader",
    "DatasetInfo",
    "load_dataset",
    "TaskContext",
]
