"""Factory helpers for DataAnalyzer instances driven by DSLightingConfig."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from dslighting.config import DSLightingConfig
from dslighting.services.data_analyzer import DataAnalyzer


def create_data_analyzer(config: DSLightingConfig) -> Optional[DataAnalyzer]:
    """Create a DataAnalyzer from the canonical DSLightingConfig."""
    settings = config.data_analysis
    if not settings.enabled:
        return None

    cache_dir = Path(settings.cache_dir).expanduser() if settings.cache_dir else None
    return DataAnalyzer(
        cache_enabled=settings.cache_enabled,
        cache_dir=cache_dir,
        cache_max_entries=settings.cache_max_entries,
        cache_debug_metrics=settings.cache_debug_metrics,
        analyzer_version=settings.analyzer_version,
    )
