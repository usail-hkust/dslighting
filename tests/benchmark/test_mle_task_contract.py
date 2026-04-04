from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("py7zr")

from dslighting.benchmark.core.mle_task_contract import MLETaskContractLoader
from dslighting.benchmark.core.source_catalog import BenchmarkSourceDescriptor


def test_mle_task_contract_prefers_prepare_val_sibling_file(tmp_path: Path) -> None:
    vendor_root = tmp_path / "benchmark" / "vendor" / "customx"
    task_dir = vendor_root / "competitions" / "task-a"
    task_dir.mkdir(parents=True)
    (task_dir / "prepare.py").write_text("def prepare(raw, public, private):\n    return public\n", encoding="utf-8")
    (task_dir / "prepare_val.py").write_text(
        "def prepare(raw, public, private):\n    return private\n",
        encoding="utf-8",
    )

    loader = MLETaskContractLoader(
        BenchmarkSourceDescriptor(
            source_id="customx",
            contract_id="mle_task_contract/v1",
            engine_id="mle",
            vendor_root=vendor_root,
            registry_root=vendor_root / "competitions",
        )
    )

    resolved = loader.resolve_callable_ref(
        task_dir,
        "file:vendor/customx/competitions/task-a/prepare.py:prepare",
        mode="validation",
    )

    assert resolved.endswith("prepare_val.py:prepare")


def test_mle_task_contract_extracts_api_version_from_grader_config(tmp_path: Path) -> None:
    vendor_root = tmp_path / "benchmark" / "vendor" / "customx"
    task_dir = vendor_root / "competitions" / "task-a"
    data_root = tmp_path / "data"
    public_dir = data_root / "task-a" / "prepared" / "public"
    private_dir = data_root / "task-a" / "prepared" / "private"
    raw_dir = data_root / "task-a" / "raw"
    task_dir.mkdir(parents=True)
    public_dir.mkdir(parents=True)
    private_dir.mkdir(parents=True)
    raw_dir.mkdir(parents=True)

    (task_dir / "description.md").write_text("Synthetic task", encoding="utf-8")
    (task_dir / "prepare.py").write_text(
        "def prepare(raw, public, private):\n    return public\n",
        encoding="utf-8",
    )
    (task_dir / "grade.py").write_text(
        "def grade(request):\n    return 1.0\n",
        encoding="utf-8",
    )
    (task_dir / "checksums.yaml").write_text("{}", encoding="utf-8")
    (task_dir / "leaderboard.csv").write_text("score\n1.0\n", encoding="utf-8")
    (public_dir / "sport.db").write_text("sample", encoding="utf-8")
    (private_dir / "sport.db").write_text("answers", encoding="utf-8")

    loader = MLETaskContractLoader(
        BenchmarkSourceDescriptor(
            source_id="customx",
            contract_id="mle_task_contract/v1",
            engine_id="mle",
            vendor_root=vendor_root,
            registry_root=vendor_root / "competitions",
        )
    )
    config = {
        "id": "task-a",
        "name": "Synthetic task",
        "competition_type": "code",
        "description": "description.md",
        "preparer": "file:prepare.py:prepare",
        "grader": {
            "name": "compare_db",
            "grade_fn": "file:grade.py:grade",
            "api_version": "artifact_v1",
        },
        "dataset": {
            "answers": "task-a/prepared/private/sport.db",
            "sample_submission": "task-a/prepared/public/sport.db",
            "submission_filename": "sport.db",
        },
    }

    payload = loader.build_competition_payload(task_dir, data_root, config, mode="test")
    competition = loader.build_competition_payload(task_dir, data_root, config, mode="test")

    assert payload["api_version"] == "artifact_v1"
    assert "api_version" not in payload["grader"]
    assert payload["grader"]["name"] == "compare_db"
    assert payload["submission_filename"] == "sport.db"
    # Regression guard: the payload must remain constructible as a runtime competition.
    from dslighting.benchmark.core.mle_task_contract import MLEStyleCompetition

    assert MLEStyleCompetition.from_dict(competition).api_version == "artifact_v1"
