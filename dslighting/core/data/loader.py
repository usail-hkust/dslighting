"""
Data loading and preprocessing module.

This module re-exports the unified DataLoader class.

Use DataLoader directly:

    >>> from dslighting.core.data import DataLoader
    >>> loader = DataLoader("path/to/data")
    >>> loader.load()

Also available via the convenience function:
    >>> import dslighting
    >>> loader = dslighting.load_dataset("path/to/data")
"""

# Re-export the unified DataLoader class from dataset.py
from .dataset import DataLoader, DatasetInfo, load_dataset

__all__ = [
    "DataLoader",
    "DatasetInfo",
    "load_dataset",
]
