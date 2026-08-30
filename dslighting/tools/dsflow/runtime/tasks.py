"""dslighting.tools.dsflow.runtime.tasks

Task preparation and description loading utilities.
"""

import logging
from pathlib import Path
from typing import Any, Tuple

from dslighting.tools.dsflow.runtime.paths import resolve_repo_root

logger = logging.getLogger(__name__)


def get_problem_description_and_data_dir(
    *,
    benchmark: Any,
    competition_id: str,
    workflow_file: Path,
) -> Tuple[str, Path]:
    """
    Get problem description and data directory for a competition.

    Prefers using benchmark registry when available, falls back to filesystem search.

    Args:
        benchmark: The benchmark instance
        competition_id: ID of the competition
        workflow_file: Path to the workflow file (for finding repo root)

    Returns:
        Tuple of (description, data_dir)
    """
    # Preferred: use benchmark registry (MLEBench/ScienceBench)
    try:
        competition = benchmark.registry.get_competition(competition_id)
        return competition.description, competition.public_dir.absolute()
    except Exception:
        pass

    # Fallback: read description from repo, point data_dir to prepared/public
    repo_dir = resolve_repo_root(workflow_file)

    # Search common competition directories
    for competitions_root in (
        repo_dir / "benchmarks" / "mlebench" / "competitions",
        repo_dir / "benchmarks" / "dabench" / "competitions",
        repo_dir / "benchmarks" / "sciencebench" / "competitions",
        repo_dir / "competitions",
    ):
        comp_dir = competitions_root / competition_id
        desc_path = comp_dir / "description.md"

        if desc_path.exists():
            description = desc_path.read_text()

            # Try to find data directory
            data_root = getattr(benchmark.registry, "get_data_dir", lambda: repo_dir / "data")()
            public_val = data_root / competition_id / "prepared" / "public_val"
            public = data_root / competition_id / "prepared" / "public"

            data_dir = public_val if public_val.exists() else public

            if data_dir.exists():
                return description, data_dir.absolute()

    # Last resort: raise error
    raise ValueError(
        f"Could not find problem description or data for competition '{competition_id}'. "
        f"Searched in {repo_dir}/benchmarks/*/competitions/"
    )
