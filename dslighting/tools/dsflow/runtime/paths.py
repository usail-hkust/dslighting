"""dslighting.tools.dsflow.runtime.paths

Shared path helpers for DSFlow runtime utilities.
"""

from __future__ import annotations

from pathlib import Path


def resolve_repo_root(anchor: Path) -> Path:
    """
    Resolve repository root (directory containing the `dslighting/` package).

    This helper is robust to code being relocated within the repository.
    """
    resolved = anchor.resolve()
    for parent in resolved.parents:
        if parent.name == "dslighting":
            return parent.parent
    # Fallback: best-effort (kept for safety in unusual layouts)
    return resolved.parents[3]
