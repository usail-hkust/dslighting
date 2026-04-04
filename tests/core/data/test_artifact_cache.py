from __future__ import annotations

from pathlib import Path

import pytest

from dslighting.core.data.perception import DataPerceptionRequest, DataPerceptionService
from dslighting.core.data.perception.cache import DataPerceptionCache


@pytest.fixture(autouse=True)
def _clear_perception_cache() -> None:
    DataPerceptionCache._clear_in_memory_cache_for_tests()


def _make_cache(cache_dir: Path) -> DataPerceptionCache:
    return DataPerceptionCache(
        enabled=True,
        cache_dir=cache_dir,
        cache_max_entries=32,
        analyzer_version="test-v1",
    )


def test_artifact_summary_cache_hits_across_service_instances(tmp_path: Path, monkeypatch) -> None:
    data_dir = tmp_path / "public"
    cache_dir = tmp_path / "cache"
    data_dir.mkdir()
    (data_dir / "train.csv").write_text("id,value\n1,10\n2,20\n", encoding="utf-8")

    request = DataPerceptionRequest(data_dir=data_dir)
    service1 = DataPerceptionService(request, cache=_make_cache(cache_dir))
    first_context = service1.inspect()
    assert first_context.summaries

    service2 = DataPerceptionService(request, cache=_make_cache(cache_dir))

    def fail_summarize(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("Expected cached artifact summary, but summarize path was used.")

    monkeypatch.setattr(service2, "_summarize_artifact", fail_summarize)
    second_context = service2.inspect()

    assert [summary.descriptor.relative_path for summary in second_context.summaries] == ["train.csv"]


def test_artifact_cache_recomputes_only_changed_file(tmp_path: Path, monkeypatch) -> None:
    data_dir = tmp_path / "public"
    cache_dir = tmp_path / "cache"
    data_dir.mkdir()
    (data_dir / "a.csv").write_text("id,value\n1,10\n2,20\n", encoding="utf-8")
    (data_dir / "b.csv").write_text("id,value\n1,100\n2,200\n", encoding="utf-8")

    request = DataPerceptionRequest(data_dir=data_dir)
    DataPerceptionService(request, cache=_make_cache(cache_dir)).inspect()

    (data_dir / "b.csv").write_text("id,value\n1,101\n2,202\n3,303\n", encoding="utf-8")
    service = DataPerceptionService(request, cache=_make_cache(cache_dir))
    recomputed: list[str] = []
    original = service._summarize_artifact

    def wrapped(descriptor):  # noqa: ANN001
        recomputed.append(descriptor.relative_path)
        return original(descriptor)

    monkeypatch.setattr(service, "_summarize_artifact", wrapped)
    context = service.inspect()

    assert sorted(summary.descriptor.relative_path for summary in context.summaries) == ["a.csv", "b.csv"]
    assert recomputed == ["b.csv"]


def test_inventory_cache_hits_across_service_instances(tmp_path: Path, monkeypatch) -> None:
    data_dir = tmp_path / "public"
    cache_dir = tmp_path / "cache"
    data_dir.mkdir()
    (data_dir / "schema.yml").write_text("# Database Schema\n## Table: T\n- id: INTEGER\n", encoding="utf-8")

    request = DataPerceptionRequest(data_dir=data_dir)
    DataPerceptionService(request, cache=_make_cache(cache_dir)).inspect()

    from dslighting.core.data.perception import service as service_module

    def fail_discovery(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("Expected cached inventory, but discovery path was used.")

    monkeypatch.setattr(service_module, "discover_artifacts", fail_discovery)
    monkeypatch.setattr(service_module, "generate_file_tree", fail_discovery)

    context = DataPerceptionService(request, cache=_make_cache(cache_dir)).inspect()

    assert [artifact.relative_path for artifact in context.inventory.artifacts] == ["schema.yml"]
