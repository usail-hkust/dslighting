"""Tests for DataPerceptionCache hit/miss/invalidation/concurrency mechanics.

Migrated from test_data_analyzer_cache.py.
These tests verify that the new DataPerceptionCache (wrapping
DataPerceptionService.inspect() inventory/summary results) correctly
hits memory, hits disk, misses on changed files, and serialises
concurrent requests for the same key.
"""

from __future__ import annotations

import concurrent.futures
import time
from pathlib import Path

import pytest

from dslighting.core.data.perception.cache import DataPerceptionCache
from dslighting.core.data.perception.runtime import DataPerceptionRuntime


def _write_minimal_dataset(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "train.csv").write_text("id,value\n1,10\n2,20\n", encoding="utf-8")
    (data_dir / "sample_submission.csv").write_text(
        "id,answer\n1,@placeholder[0.00]\n", encoding="utf-8"
    )


@pytest.fixture(autouse=True)
def _clear_cache():
    DataPerceptionCache._clear_in_memory_cache_for_tests()
    yield
    DataPerceptionCache._clear_in_memory_cache_for_tests()


def test_analyze_data_memory_cache_hit(tmp_path: Path) -> None:
    """Second analyze_data on same data_dir hits in-memory cache."""
    data_dir = tmp_path / "data"
    cache_dir = tmp_path / "cache"
    _write_minimal_dataset(data_dir)

    runtime = DataPerceptionRuntime(cache_dir=cache_dir)

    first = runtime.analyze_data(data_dir, task_type="kaggle")
    second = runtime.analyze_data(data_dir, task_type="kaggle")

    assert first == second
    stats = DataPerceptionCache.get_cache_stats()
    assert stats["hits_memory"] >= 1


def test_analyze_data_disk_cache_hit_across_instances(tmp_path: Path) -> None:
    """Second Runtime instance with same cache_dir hits disk cache."""
    data_dir = tmp_path / "data"
    cache_dir = tmp_path / "cache"
    _write_minimal_dataset(data_dir)

    runtime1 = DataPerceptionRuntime(cache_dir=cache_dir)
    expected = runtime1.analyze_data(data_dir, task_type="kaggle")

    DataPerceptionCache._clear_in_memory_cache_for_tests()

    runtime2 = DataPerceptionRuntime(cache_dir=cache_dir)
    actual = runtime2.analyze_data(data_dir, task_type="kaggle")

    assert actual == expected
    stats = DataPerceptionCache.get_cache_stats()
    # Disk hits reflect reads of inventory + summary entries stored on disk.
    # The exact count depends on how many artifacts were in the dataset.
    assert stats["hits_disk"] >= 1


def test_analyze_data_task_id_cache_miss_across_directories_when_analysis_root_differs(
    tmp_path: Path,
) -> None:
    """Different data_dir with same task_id produces different reports."""
    data_dir_1 = tmp_path / "data_1"
    data_dir_2 = tmp_path / "data_2"
    cache_dir = tmp_path / "cache"
    _write_minimal_dataset(data_dir_1)
    _write_minimal_dataset(data_dir_2)
    (data_dir_2 / "train.csv").write_text("id,value\n9,90\n10,100\n", encoding="utf-8")

    runtime1 = DataPerceptionRuntime(cache_dir=cache_dir, analyzer_version="test-v1")
    expected = runtime1.analyze_data(
        data_dir_1,
        task_type="kaggle",
        task_id="dabench-fixed-task",
    )

    DataPerceptionCache._clear_in_memory_cache_for_tests()

    runtime2 = DataPerceptionRuntime(cache_dir=cache_dir, analyzer_version="test-v1")
    actual = runtime2.analyze_data(
        data_dir_2,
        task_type="kaggle",
        task_id="dabench-fixed-task",
    )

    assert actual != expected
    stats = DataPerceptionCache.get_cache_stats()
    assert stats["misses"] >= 1


def test_analyze_data_cache_invalidates_on_analyzer_version(tmp_path: Path) -> None:
    """Changing analyzer_version causes a cache miss and recompute."""
    data_dir = tmp_path / "data"
    cache_dir = tmp_path / "cache"
    _write_minimal_dataset(data_dir)

    runtime1 = DataPerceptionRuntime(
        cache_dir=cache_dir, analyzer_version="test-v1"
    )
    runtime1.analyze_data(data_dir, task_type="kaggle", task_id="dabench-versioned-task")

    DataPerceptionCache._clear_in_memory_cache_for_tests()

    runtime2 = DataPerceptionRuntime(
        cache_dir=cache_dir, analyzer_version="test-v2"
    )
    result = runtime2.analyze_data(
        data_dir, task_type="kaggle", task_id="dabench-versioned-task"
    )

    # test-v2 has different fingerprint, so a new compute is required
    # (report may or may not differ, but cache must miss)
    stats = DataPerceptionCache.get_cache_stats()
    assert stats["misses"] >= 1


def test_analyze_data_cache_invalidates_when_file_changes(tmp_path: Path) -> None:
    """Modifying a data file after first analyze invalidates cache."""
    data_dir = tmp_path / "data"
    cache_dir = tmp_path / "cache"
    _write_minimal_dataset(data_dir)

    runtime = DataPerceptionRuntime(cache_dir=cache_dir)

    runtime.analyze_data(data_dir, task_type="kaggle")
    (data_dir / "train.csv").write_text(
        "id,value\n1,10\n2,20\n3,30\n", encoding="utf-8"
    )
    runtime.analyze_data(data_dir, task_type="kaggle")

    stats = DataPerceptionCache.get_cache_stats()
    assert stats["misses"] >= 2


def test_analyze_data_corrupt_disk_cache_falls_back_to_compute(tmp_path: Path) -> None:
    """Corrupting the disk cache file causes a recompute without raising."""
    data_dir = tmp_path / "data"
    cache_dir = tmp_path / "cache"
    _write_minimal_dataset(data_dir)

    runtime1 = DataPerceptionRuntime(cache_dir=cache_dir)
    runtime1.analyze_data(data_dir, task_type="kaggle")

    # Corrupt the on-disk cache.
    cache_key = None
    # Find the cache key by inspecting the cache dir structure.
    import hashlib
    import json

    def find_cache_path() -> Path | None:
        import os

        perception_dir = cache_dir / "perception"
        if not perception_dir.exists():
            return None
        for root, _dirs, files in os.walk(perception_dir):
            for f in files:
                if f.endswith(".json"):
                    return Path(root) / f
        return None

    cache_path = find_cache_path()
    if cache_path:
        cache_path.write_text("{ this-is-invalid-json ", encoding="utf-8")

    DataPerceptionCache._clear_in_memory_cache_for_tests()

    runtime2 = DataPerceptionRuntime(cache_dir=cache_dir)
    result = runtime2.analyze_data(data_dir, task_type="kaggle")

    # Should have computed without raising; content reflects the (unchanged) data
    assert "id" in result
    stats = DataPerceptionCache.get_cache_stats()
    assert stats["misses"] >= 1


def test_analyze_data_concurrent_requests_compute_once(tmp_path: Path) -> None:
    """Eight concurrent analyze_data calls for the same data_dir compute only once."""
    data_dir = tmp_path / "data"
    cache_dir = tmp_path / "cache"
    _write_minimal_dataset(data_dir)

    runtime = DataPerceptionRuntime(cache_dir=cache_dir)

    def run_once() -> str:
        return runtime.analyze_data(data_dir, task_type="kaggle")

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: run_once(), range(8)))

    assert all(value == results[0] for value in results)
    stats = DataPerceptionCache.get_cache_stats()
    # At minimum, there should be 7 hits across memory + disk
    total_hits = stats["hits_memory"] + stats["hits_disk"]
    assert total_hits >= 7
