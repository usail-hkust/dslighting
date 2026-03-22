from __future__ import annotations

from pathlib import Path

from dslighting.benchmark.core.mle_style_registry import MLEStyleRegistry
from dslighting.benchmark.core.mle_task_contract import MLEStyleCompetition as Competition
from dslighting.benchmark.core.source_catalog import get_benchmark_source_catalog


DEFAULT_DATA_DIR = (Path.home() / ".cache" / "mle-bench" / "data").resolve()


class Registry:
    """Compatibility wrapper for the DACode registry."""

    def __init__(self, data_dir: Path = DEFAULT_DATA_DIR):
        descriptor = get_benchmark_source_catalog().get_source("dacode")
        self._delegate = MLEStyleRegistry(descriptor=descriptor, data_dir=Path(data_dir))

    def set_mode(self, mode: str = "test"):
        self._delegate.set_mode(mode)

    def get_competition(self, competition_id: str) -> Competition:
        return self._delegate.get_competition(competition_id)

    def get_competitions_dir(self) -> Path:
        return self._delegate.get_competitions_dir()

    def get_splits_dir(self) -> Path:
        return self._delegate.get_splits_dir()

    def get_data_dir(self) -> Path:
        return self._delegate.get_data_dir()

    def set_data_dir(self, new_data_dir: Path) -> "Registry":
        new_registry = Registry(new_data_dir)
        new_registry.set_mode(self._delegate.mode)
        return new_registry

    def list_competition_ids(self) -> list[str]:
        return self._delegate.list_competition_ids()


registry = Registry()
