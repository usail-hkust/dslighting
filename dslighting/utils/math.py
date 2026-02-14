"""Math utilities for the DSLighting benchmark system."""

from __future__ import annotations

import math
from typing import List


def p95(values: List[float]) -> float:
    """Calculate 95th percentile of values.

    Args:
        values: List of numeric values.

    Returns:
        The 95th percentile value, or 0.0 if the list is empty.
    """
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    ordered = sorted(float(v) for v in values)
    idx = int(math.ceil(0.95 * len(ordered))) - 1
    idx = min(max(0, idx), len(ordered) - 1)
    return ordered[idx]


__all__ = ["p95"]
