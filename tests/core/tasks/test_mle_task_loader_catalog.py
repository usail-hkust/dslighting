from __future__ import annotations

from pathlib import Path

import pytest
import yaml

pytest.importorskip("diskcache")

from dslighting.benchmark.core.source_catalog import BenchmarkSourceCatalog


def _create_source(tmp_path: Path, source_id: str, task_id: str) -> tuple[Path, Path]:
    vendor_root = tmp_path / "benchmark" / "vendor" / source_id
    registry_root = vendor_root / "competitions"
    task_dir = registry_root / task_id
    data_root = tmp_path / "data"

    task_dir.mkdir(parents=True)
    (task_dir / "description.md").write_text("Synthetic task description", encoding="utf-8")
    (task_dir / "prepare.py").write_text(
        "def prepare(raw, public, private):\n    return public\n\n"
        "def prepare_val(raw, public, private):\n    return public\n",
        encoding="utf-8",
    )
    (task_dir / "grade.py").write_text(
        "def grade(submission, answers):\n    return 1.0\n",
        encoding="utf-8",
    )
    (task_dir / "leaderboard.csv").write_text("score\n1.0\n", encoding="utf-8")
    (task_dir / "checksums.yaml").write_text("{}", encoding="utf-8")
    (task_dir / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "id": task_id,
                "name": "Synthetic task",
                "competition_type": "tabular",
                "description": f"vendor/{source_id}/competitions/{task_id}/description.md",
                "preparer": f"file:vendor/{source_id}/competitions/{task_id}/prepare.py:prepare",
                "grader": {
                    "name": "StandardGrader",
                    "grade_fn": f"file:vendor/{source_id}/competitions/{task_id}/grade.py:grade",
                },
                "dataset": {
                    "answers": f"{task_id}/prepared/private/answers.csv",
                    "sample_submission": f"{task_id}/prepared/public/sample_submission.csv",
                },
            }
        ),
        encoding="utf-8",
    )
    (vendor_root / "benchmark.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "source_id": source_id,
                "contract_id": "mle_task_contract/v1",
                "engine_id": "mle",
                "registry_root": "competitions",
                "default_data_env_var": f"DSLIGHTING_{source_id.upper()}_DATA",
            }
        ),
        encoding="utf-8",
    )

    public_dir = data_root / task_id / "prepared" / "public"
    private_dir = data_root / task_id / "prepared" / "private"
    raw_dir = data_root / task_id / "raw"
    public_dir.mkdir(parents=True)
    private_dir.mkdir(parents=True)
    raw_dir.mkdir(parents=True)
    (public_dir / "sample_submission.csv").write_text("prediction\n0\n", encoding="utf-8")
    (public_dir / "placeholder.txt").write_text("x", encoding="utf-8")
    (private_dir / "answers.csv").write_text("prediction\n1\n", encoding="utf-8")
    (private_dir / "placeholder.txt").write_text("x", encoding="utf-8")
    return registry_root, data_root


def test_manifest_defined_source_builds_registry_for_single_task(tmp_path: Path) -> None:
    registry_root, data_root = _create_source(tmp_path, "customx", "plain-task")

    catalog = BenchmarkSourceCatalog()
    resolved = catalog.resolve_task(
        task_id="plain-task",
        registry_dir=registry_root,
        search_hints=[tmp_path],
    )
    registry = catalog.build_registry(
        resolved.descriptor,
        data_root=data_root,
        mode="test",
    )

    competition = registry.get_competition("plain-task")

    assert resolved.descriptor.source_id == "customx"
    assert competition.id == "plain-task"
    assert competition.public_dir == data_root / "plain-task" / "prepared" / "public"
