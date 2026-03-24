"""Compatibility wrapper for the shared competition-style benchmark engine."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from dslighting.benchmark.benchmarks.mle_style_benchmark import MLEStyleBenchmark
from dslighting.benchmark.core.config_loader import BaseBenchmarkConfigLoader
from dslighting.benchmark.vendor.dabench.registry import Registry as DABenchRegistry


class DABenchmark(MLEStyleBenchmark):
    """
    Dedicated benchmark class for DABench tasks.

    This is a thin wrapper around ``MLEStyleBenchmark`` that:
    1. Restricts competition IDs to ``dabench-*``.
    2. Defaults to filtering only DABench entries from config when no explicit
       competitions are passed.
    """

    def __init__(
        self,
        name: str = "dabench",
        log_path: str = "runs/benchmarks/dabench",
        data_dir: Optional[str] = None,
        competitions: Optional[List[Any]] = None,
        data_source: str = "prepared",
        runner: Optional[Any] = None,
        eval_fn: Optional[Any] = None,
    ):
        validated = self._validate_competitions(competitions)
        super().__init__(
            name=name,
            file_path=None,
            log_path=log_path,
            data_dir=data_dir,
            competitions=validated,
            data_source=data_source,
            runner=runner,
            eval_fn=eval_fn,
            registry=DABenchRegistry(Path(data_dir)) if data_dir else DABenchRegistry(),
        )

    @staticmethod
    def _is_dabench_competition(competition_id: str) -> bool:
        return competition_id.startswith("dabench-")

    def _load_config(self) -> Dict[str, Any]:
        """Load config and keep only DABench competitions."""
        # Get base config from parent's config loader
        config = self.config_loader.load_config()
        entries = config.get("competitions", [])
        filtered: List[Any] = []

        for entry in entries:
            competition_id = entry
            if isinstance(entry, dict):
                competition_id = entry.get("id")

            if isinstance(competition_id, str) and self._is_dabench_competition(competition_id):
                filtered.append(entry)

        config["competitions"] = filtered
        return config


    @staticmethod
    def _validate_competitions(competitions: Optional[List[Any]]) -> Optional[List[Any]]:
        if competitions is None:
            return None

        invalid: List[Any] = []
        for entry in competitions:
            competition_id = entry
            if isinstance(entry, dict):
                competition_id = entry.get("id")

            if not isinstance(competition_id, str) or not competition_id.startswith("dabench-"):
                invalid.append(entry)

        if invalid:
            raise ValueError(
                "DABenchmark only accepts DABench task IDs (prefix 'dabench-'). "
                f"Invalid IDs: {invalid}"
            )
        return competitions
