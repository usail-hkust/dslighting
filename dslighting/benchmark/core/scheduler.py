"""Deprecated compatibility module removed in Phase 2 major cleanup.

Use canonical imports instead:
- ``dslighting.benchmark.core.scheduler_core`` for scheduler classes/options
- ``dslighting.benchmark.core.monitoring_integration`` for monitoring helpers
"""

raise ImportError(
    "'dslighting.benchmark.core.scheduler' was removed in this major release. "
    "Use 'dslighting.benchmark.core.scheduler_core' and "
    "'dslighting.benchmark.core.monitoring_integration' instead."
)
