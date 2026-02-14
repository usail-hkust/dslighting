"""Deprecated compatibility module removed in Phase 2 major cleanup.

Import exceptions from ``dslighting.error`` instead.
"""

raise ImportError(
    "'dslighting.exceptions' was removed in this major release. "
    "Use 'from dslighting.error import ...' instead."
)
