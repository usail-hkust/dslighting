from pathlib import Path

import pytest

pytest.importorskip("pandas")

from dslighting.core.data.loader_utils import auto_detect_registry_dir, get_default_mle_detection


def test_auto_detect_registry_dir_from_data_layout(tmp_path: Path):
    task_id = "bike-sharing-demand"
    data_dir = tmp_path / "data" / "competitions" / task_id
    registry_root = tmp_path / "benchmark" / "vendor" / "mlebench" / "competitions"
    registry_task_dir = registry_root / task_id

    data_dir.mkdir(parents=True)
    registry_task_dir.mkdir(parents=True)

    detected = auto_detect_registry_dir(data_dir, task_id)
    assert detected == registry_root


def test_missing_source_path_keeps_local_resolution(tmp_path: Path):
    missing = tmp_path / "missing-competition"
    detection = get_default_mle_detection(missing)

    assert detection.data_dir is not None
    assert str(detection.data_dir).startswith(str(tmp_path))
