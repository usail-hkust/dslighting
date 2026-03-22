import concurrent.futures
import time
from pathlib import Path

import pytest

from dslighting.services.data_analyzer import DataAnalyzer


def _write_minimal_dataset(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "train.csv").write_text("id,value\n1,10\n2,20\n", encoding="utf-8")
    (data_dir / "sample_submission.csv").write_text(
        "id,answer\n1,@placeholder[0.00]\n", encoding="utf-8"
    )


@pytest.fixture(autouse=True)
def _clear_data_analyzer_cache():
    DataAnalyzer._clear_in_memory_cache_for_tests()
    yield
    DataAnalyzer._clear_in_memory_cache_for_tests()


def test_analyze_data_memory_cache_hit(tmp_path: Path, monkeypatch):
    data_dir = tmp_path / "data"
    cache_dir = tmp_path / "cache"
    _write_minimal_dataset(data_dir)

    analyzer = DataAnalyzer(cache_dir=cache_dir)
    calls = {"count": 0}
    original_compute = analyzer._compute_data_report

    def wrapped_compute(path: Path, task_type=None, submission_context=None):  # noqa: ANN001
        calls["count"] += 1
        return original_compute(path, task_type, submission_context=submission_context)

    monkeypatch.setattr(analyzer, "_compute_data_report", wrapped_compute)

    first = analyzer.analyze_data(data_dir, task_type="kaggle")
    second = analyzer.analyze_data(data_dir, task_type="kaggle")

    assert first == second
    assert calls["count"] == 1
    assert analyzer.cache_hits_memory >= 1


def test_analyze_data_disk_cache_hit_across_instances(tmp_path: Path, monkeypatch):
    data_dir = tmp_path / "data"
    cache_dir = tmp_path / "cache"
    _write_minimal_dataset(data_dir)

    analyzer1 = DataAnalyzer(cache_dir=cache_dir)
    expected = analyzer1.analyze_data(data_dir, task_type="kaggle")

    DataAnalyzer._clear_in_memory_cache_for_tests()

    analyzer2 = DataAnalyzer(cache_dir=cache_dir)

    def fail_compute(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("Expected disk cache hit, but compute path was used.")

    monkeypatch.setattr(analyzer2, "_compute_data_report", fail_compute)
    actual = analyzer2.analyze_data(data_dir, task_type="kaggle")

    assert actual == expected
    assert analyzer2.cache_hits_disk == 1


def test_analyze_data_task_id_cache_miss_across_directories_when_analysis_root_differs(tmp_path: Path, monkeypatch):
    data_dir_1 = tmp_path / "data_1"
    data_dir_2 = tmp_path / "data_2"
    cache_dir = tmp_path / "cache"
    _write_minimal_dataset(data_dir_1)
    _write_minimal_dataset(data_dir_2)
    (data_dir_2 / "train.csv").write_text("id,value\n9,90\n10,100\n", encoding="utf-8")

    analyzer1 = DataAnalyzer(cache_dir=cache_dir, analyzer_version="test-v1")
    expected = analyzer1.analyze_data(
        data_dir_1,
        task_type="kaggle",
        task_id="dabench-fixed-task",
    )

    DataAnalyzer._clear_in_memory_cache_for_tests()
    analyzer2 = DataAnalyzer(cache_dir=cache_dir, analyzer_version="test-v1")

    calls = {"count": 0}
    original_compute = analyzer2._compute_data_report

    def wrapped_compute(path: Path, task_type=None, submission_context=None):  # noqa: ANN001
        calls["count"] += 1
        return original_compute(path, task_type, submission_context=submission_context)

    monkeypatch.setattr(analyzer2, "_compute_data_report", wrapped_compute)
    actual = analyzer2.analyze_data(
        data_dir_2,
        task_type="kaggle",
        task_id="dabench-fixed-task",
    )

    assert actual != expected
    assert calls["count"] == 1
    assert analyzer2.cache_misses == 1


def test_analyze_data_task_id_cache_invalidates_on_analyzer_version(tmp_path: Path, monkeypatch):
    data_dir = tmp_path / "data"
    cache_dir = tmp_path / "cache"
    _write_minimal_dataset(data_dir)

    analyzer1 = DataAnalyzer(cache_dir=cache_dir, analyzer_version="test-v1")
    analyzer1.analyze_data(data_dir, task_type="kaggle", task_id="dabench-versioned-task")

    DataAnalyzer._clear_in_memory_cache_for_tests()
    analyzer2 = DataAnalyzer(cache_dir=cache_dir, analyzer_version="test-v2")
    calls = {"count": 0}

    def fake_compute(path: Path, task_type=None, submission_context=None):  # noqa: ANN001
        calls["count"] += 1
        return "fresh-v2-report"

    monkeypatch.setattr(analyzer2, "_compute_data_report", fake_compute)
    result = analyzer2.analyze_data(data_dir, task_type="kaggle", task_id="dabench-versioned-task")

    assert result == "fresh-v2-report"
    assert calls["count"] == 1


def test_analyze_data_cache_invalidates_when_file_changes(tmp_path: Path, monkeypatch):
    data_dir = tmp_path / "data"
    cache_dir = tmp_path / "cache"
    _write_minimal_dataset(data_dir)

    analyzer = DataAnalyzer(cache_dir=cache_dir)
    calls = {"count": 0}
    original_compute = analyzer._compute_data_report

    def wrapped_compute(path: Path, task_type=None, submission_context=None):  # noqa: ANN001
        calls["count"] += 1
        return original_compute(path, task_type, submission_context=submission_context)

    monkeypatch.setattr(analyzer, "_compute_data_report", wrapped_compute)

    analyzer.analyze_data(data_dir, task_type="kaggle")
    (data_dir / "train.csv").write_text("id,value\n1,10\n2,20\n3,30\n", encoding="utf-8")
    analyzer.analyze_data(data_dir, task_type="kaggle")

    assert calls["count"] == 2
    assert analyzer.cache_misses >= 2


def test_analyze_data_corrupt_disk_cache_falls_back_to_compute(tmp_path: Path, monkeypatch):
    data_dir = tmp_path / "data"
    cache_dir = tmp_path / "cache"
    _write_minimal_dataset(data_dir)

    analyzer1 = DataAnalyzer(cache_dir=cache_dir)
    analyzer1.analyze_data(data_dir, task_type="kaggle")

    cache_key = analyzer1._build_cache_key(data_dir, "kaggle")
    assert cache_key is not None
    cache_path = analyzer1._cache_file_path(cache_key)
    assert cache_path is not None
    cache_path.write_text("{ this-is-invalid-json ", encoding="utf-8")

    DataAnalyzer._clear_in_memory_cache_for_tests()

    analyzer2 = DataAnalyzer(cache_dir=cache_dir)
    calls = {"count": 0}

    def fake_compute(path: Path, task_type=None, submission_context=None):  # noqa: ANN001
        calls["count"] += 1
        return "fresh-report"

    monkeypatch.setattr(analyzer2, "_compute_data_report", fake_compute)
    result = analyzer2.analyze_data(data_dir, task_type="kaggle")

    assert result == "fresh-report"
    assert calls["count"] == 1


def test_analyze_data_concurrent_requests_compute_once(tmp_path: Path, monkeypatch):
    data_dir = tmp_path / "data"
    cache_dir = tmp_path / "cache"
    _write_minimal_dataset(data_dir)

    analyzer = DataAnalyzer(cache_dir=cache_dir)
    calls = {"count": 0}

    def slow_compute(path: Path, task_type=None, submission_context=None):  # noqa: ANN001
        calls["count"] += 1
        time.sleep(0.05)
        return "shared-report"

    monkeypatch.setattr(analyzer, "_compute_data_report", slow_compute)

    def run_once() -> str:
        return analyzer.analyze_data(data_dir, task_type="kaggle")

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: run_once(), range(8)))

    assert all(value == "shared-report" for value in results)
    assert calls["count"] == 1
