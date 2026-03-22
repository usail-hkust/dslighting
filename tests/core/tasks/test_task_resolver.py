from __future__ import annotations

from pathlib import Path

import pytest
import yaml

pytest.importorskip("diskcache")

from dslighting.config import DSLightingConfig
from dslighting.core.tasks import FileSubmissionTaskAdapter, TaskResolver


def _create_colocated_task(tmp_path: Path, source_id: str, task_id: str) -> Path:
    registry_root = tmp_path / source_id
    task_root = registry_root / task_id
    public_dir = task_root / "prepared" / "public"
    private_dir = task_root / "prepared" / "private"
    raw_dir = task_root / "raw"

    task_root.mkdir(parents=True)
    public_dir.mkdir(parents=True)
    private_dir.mkdir(parents=True)
    raw_dir.mkdir(parents=True)

    (task_root / "description.md").write_text("Synthetic task description", encoding="utf-8")
    (task_root / "prepare.py").write_text(
        "def prepare(raw, public, private):\n    return public\n",
        encoding="utf-8",
    )
    (task_root / "grade.py").write_text(
        "def grade(submission, answers):\n    return 1.0\n",
        encoding="utf-8",
    )
    (task_root / "leaderboard.csv").write_text("score\n1.0\n", encoding="utf-8")
    (task_root / "checksums.yaml").write_text("{}", encoding="utf-8")
    (public_dir / "sample_submission.csv").write_text("prediction\n0\n", encoding="utf-8")
    (public_dir / "visible.csv").write_text("feature\n1\n", encoding="utf-8")
    (private_dir / "answers.csv").write_text("prediction\n1\n", encoding="utf-8")
    (private_dir / "secret.txt").write_text("hidden", encoding="utf-8")
    (raw_dir / "source.csv").write_text("feature\n2\n", encoding="utf-8")

    (task_root / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "id": task_id,
                "name": "Synthetic task",
                "competition_type": "tabular",
                "description": "description.md",
                "preparer": "file:prepare.py:prepare",
                "grader": {
                    "name": "StandardGrader",
                    "grade_fn": "file:grade.py:grade",
                },
                "dataset": {
                    "answers": f"{task_id}/prepared/private/answers.csv",
                    "sample_submission": f"{task_id}/prepared/public/sample_submission.csv",
                },
            }
        ),
        encoding="utf-8",
    )
    (registry_root / "benchmark.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "source_id": source_id,
                "contract_id": "mle_task_contract/v1",
                "engine_id": "mle",
                "registry_root": ".",
            }
        ),
        encoding="utf-8",
    )
    return task_root


def test_task_resolver_accepts_task_root_and_public_dir(tmp_path: Path) -> None:
    task_root = _create_colocated_task(tmp_path, "customx", "plain-task")
    resolver = TaskResolver()

    from_task_root = resolver.resolve(task_id="plain-task", data=task_root)
    from_public_dir = resolver.resolve(task_id="plain-task", data=task_root / "prepared" / "public")

    assert from_task_root.registry_root == task_root.parent
    assert from_task_root.task_root == task_root
    assert from_task_root.agent_visible_dir == task_root / "prepared" / "public"
    assert from_task_root.sample_submission_path == task_root / "prepared" / "public" / "sample_submission.csv"

    assert from_public_dir.registry_root == task_root.parent
    assert from_public_dir.task_root == task_root
    assert from_public_dir.agent_visible_dir == task_root / "prepared" / "public"


def test_file_submission_adapter_builds_single_public_report(tmp_path: Path) -> None:
    task_root = _create_colocated_task(tmp_path, "customx", "plain-task")
    resolver = TaskResolver()
    layout = resolver.resolve(task_id="plain-task", data=task_root)

    adapter = FileSubmissionTaskAdapter(DSLightingConfig())
    spec = adapter.build_file_submission_spec(layout, adapter.analyzer)
    adapter.cleanup()

    assert spec.agent_visible_dir == task_root / "prepared" / "public"
    assert spec.description_text.count("--- COMPREHENSIVE DATA REPORT ---") == 1
    assert "secret.txt" not in spec.description_text
    assert "sample_submission.csv" in spec.description_text


def test_file_submission_adapter_respects_disabled_data_analysis(tmp_path: Path) -> None:
    task_root = _create_colocated_task(tmp_path, "customx", "plain-task")
    resolver = TaskResolver()
    layout = resolver.resolve(task_id="plain-task", data=task_root)

    config = DSLightingConfig.model_validate({"data_analysis": {"enabled": False}})
    adapter = FileSubmissionTaskAdapter(config)
    spec = adapter.build_file_submission_spec(layout, adapter.analyzer)
    adapter.cleanup()

    assert adapter.analyzer is None
    assert "--- COMPREHENSIVE DATA REPORT ---" not in spec.description_text
