"""Factory helpers for data perception runtimes driven by DSLightingConfig."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from dslighting.config import DSLightingConfig
from dslighting.core.data.perception import DataPerceptionRuntime
from dslighting.utils.constants import DEFAULT_DATA_PERCEPTION_ANALYZER_VERSION


def create_data_perception_runtime(config: DSLightingConfig) -> Optional[DataPerceptionRuntime]:
    """Create the config-bound data perception runtime used by main execution paths."""
    settings = config.data_analysis
    if not settings.enabled:
        return None

    cache_dir = Path(settings.cache_dir).expanduser() if settings.cache_dir else None
    return DataPerceptionRuntime(
        cache_enabled=settings.cache_enabled,
        cache_dir=cache_dir,
        cache_max_entries=settings.cache_max_entries,
        analyzer_version=settings.analyzer_version or DEFAULT_DATA_PERCEPTION_ANALYZER_VERSION,
        profile=settings.profile,
        max_artifacts=settings.max_artifacts,
        max_report_chars=settings.max_report_chars,
        document_preview_lines=settings.document_preview_lines,
        enable_document_inspection=settings.enable_document_inspection,
        enable_database_inspection=settings.enable_database_inspection,
        tabular_tolerant_fallback=settings.tabular_tolerant_fallback,
    )
