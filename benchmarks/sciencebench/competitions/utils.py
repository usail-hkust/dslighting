"""
Utility functions for ScienceBench competitions.

These functions are re-exported here for convenience so competition files
can use "from .utils import ..."
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Any, Dict

# Re-export commonly used functions that might be needed by competition files


def read_csv(*args, **kwargs) -> pd.DataFrame:
    """Read CSV file with standard settings"""
    try:
        new_kwargs = {"float_precision": "round_trip", **kwargs}
        return pd.read_csv(*args, **new_kwargs)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def load_yaml(file_path: Path) -> Dict:
    """Load YAML file"""
    import yaml
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


__all__ = ['read_csv', 'load_yaml']
