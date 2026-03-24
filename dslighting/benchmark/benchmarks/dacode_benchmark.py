"""Compatibility wrapper for DACode over the shared competition-style engine."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from dslighting.benchmark.benchmarks.mle_style_benchmark import MLEStyleBenchmark
from dslighting.benchmark.vendor.dacode.registry import Registry as DACodeRegistry
from dslighting.benchmark.vendor.dacode.registry import registry as DEFAULT_DACODE_REGISTRY


# All DA-Code task-type prefixes, as they appear after "dabench-" in the ID.
# e.g. "dabench-dm-csv-042" → segment "dm-csv"
_DACODE_SEGMENTS = frozenset({
    "data-sa",
    "data-wrangling",
    "di-csv",
    "di-text",
    "dm-csv",
    "ml-binary",
    "ml-cluster",
    "ml-competition",
    "ml-multi",
    "ml-regression",
    "plot-bar",
    "plot-line",
    "plot-pie",
    "plot-scatter",
})


class DACodeBenchmark(MLEStyleBenchmark):
    """
    Benchmark class for DA-Code tasks converted to DABench format.

    Uses the dedicated ``vendor/dacode/`` registry and ``/data/dacode/`` data
    directory, keeping converted tasks fully isolated from original DABench tasks.
    """

    def __init__(
        self,
        name: str = "dacodebench",
        log_path: str = "runs/benchmarks/dacodebench",
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
        )
        # Override: use DACodeRegistry instead of DABenchRegistry
        self.dacode_registry: DACodeRegistry = DEFAULT_DACODE_REGISTRY.set_data_dir(self.data_dir)

    # ── Registry routing ──────────────────────────────────────────────────────

    def _get_registry_for_competition(self, competition_id: str):
        if self._is_dacode_competition(competition_id):
            return self.dacode_registry
        return self.registry  # fallback to mlebench registry

    # ── ID filtering ──────────────────────────────────────────────────────────

    @staticmethod
    def _is_dacode_competition(competition_id: str) -> bool:
        if not competition_id.startswith("dabench-"):
            return False
        segment = competition_id[len("dabench-"):]
        return any(segment.startswith(s + "-") for s in _DACODE_SEGMENTS)

    def _load_config(self) -> Dict[str, Any]:
        config = self.config_loader.load_config()
        entries = config.get("competitions", [])

        filtered: List[Any] = []
        for entry in entries:
            competition_id = entry if isinstance(entry, str) else entry.get("id")
            if isinstance(competition_id, str) and self._is_dacode_competition(competition_id):
                filtered.append(entry)

        config["competitions"] = filtered
        return config

    @classmethod
    def _validate_competitions(cls, competitions: Optional[List[Any]]) -> Optional[List[Any]]:
        if competitions is None:
            return None

        invalid = [
            entry for entry in competitions
            if not cls._is_dacode_competition(
                entry if isinstance(entry, str) else entry.get("id", "")
            )
        ]
        if invalid:
            raise ValueError(
                "DACodeBenchmark only accepts converted DA-Code task IDs "
                f"(e.g. 'dabench-dm-csv-042'). Invalid entries: {invalid}"
            )
        return competitions
