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


def _create_multi_artifact_task(tmp_path: Path, source_id: str, task_id: str) -> Path:
    registry_root = tmp_path / source_id
    task_root = registry_root / task_id
    public_dir = task_root / "prepared" / "public"
    private_dir = task_root / "prepared" / "private"
    raw_dir = task_root / "raw"

    task_root.mkdir(parents=True)
    public_dir.mkdir(parents=True)
    private_dir.mkdir(parents=True)
    raw_dir.mkdir(parents=True)

    (task_root / "description.md").write_text("Synthetic multi-artifact task", encoding="utf-8")
    (task_root / "prepare.py").write_text(
        "def prepare(raw, public, private):\n    return public\n",
        encoding="utf-8",
    )
    (task_root / "grade.py").write_text(
        "from dslighting.benchmark.grading.helpers import read_reference_child_csv, read_submission_child_csv, require_submission_dir\n"
        "def grade(request):\n"
        "    require_submission_dir(request)\n"
        "    total = 0.0\n"
        "    for name in ('before.csv', 'after.csv'):\n"
        "        pred = read_submission_child_csv(request, name)\n"
        "        gold = read_reference_child_csv(request, name)\n"
        "        total += float((pred['value'] == gold['value']).mean())\n"
        "    return total / 2.0\n",
        encoding="utf-8",
    )
    (task_root / "leaderboard.csv").write_text("score\n1.0\n", encoding="utf-8")
    (task_root / "checksums.yaml").write_text("{}", encoding="utf-8")
    (public_dir / "sample_before.csv").write_text("value\n0\n", encoding="utf-8")
    (public_dir / "sample_after.csv").write_text("value\n0\n", encoding="utf-8")
    (private_dir / "before.csv").write_text("value\n1\n", encoding="utf-8")
    (private_dir / "after.csv").write_text("value\n2\n", encoding="utf-8")

    (task_root / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "id": task_id,
                "name": "Synthetic multi-artifact task",
                "competition_type": "tabular",
                "description": "description.md",
                "preparer": "file:prepare.py:prepare",
                "grader": {
                    "name": "ArtifactGrader",
                    "grade_fn": "file:grade.py:grade",
                },
                "dataset": {
                    "answers": f"{task_id}/prepared/private/before.csv",
                    "sample_submission": f"{task_id}/prepared/public/sample_before.csv",
                },
                "evaluator": {
                    "api_version": "artifact_v1",
                    "submission": {
                        "root_kind": "directory",
                        "root_basename": "submission_bundle",
                        "entries": [
                            {
                                "relative_path": "before.csv",
                                "format": "csv",
                                "sample": f"{task_id}/prepared/public/sample_before.csv",
                                "description": "before epoch matrix",
                            },
                            {
                                "relative_path": "after.csv",
                                "format": "csv",
                                "sample": f"{task_id}/prepared/public/sample_after.csv",
                                "description": "after epoch matrix",
                            },
                        ],
                    },
                    "references": {
                        "root_kind": "directory",
                        "root_path": f"{task_id}/prepared/private",
                        "entries": [
                            {"relative_path": "before.csv"},
                            {"relative_path": "after.csv"},
                        ],
                    },
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
    spec = adapter.build_file_submission_spec(layout, adapter.data_perception)
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
    spec = adapter.build_file_submission_spec(layout, adapter.data_perception)
    adapter.cleanup()

    assert adapter.data_perception is None
    assert "--- COMPREHENSIVE DATA REPORT ---" not in spec.description_text


def test_file_submission_adapter_propagates_metric_semantics(tmp_path: Path) -> None:
    task_root = _create_colocated_task(tmp_path, "customx", "plain-task")
    resolver = TaskResolver()
    layout = resolver.resolve(task_id="plain-task", data=task_root)

    adapter = FileSubmissionTaskAdapter(DSLightingConfig())
    spec = adapter.build_file_submission_spec(layout, adapter.data_perception)
    adapter.cleanup()

    assert spec.metric_name == "score"
    assert spec.lower_is_better is False

    payload = spec.to_payload()
    assert payload["metric_name"] == "score"
    assert payload["lower_is_better"] is False


def test_task_resolver_builds_directory_submission_contract(tmp_path: Path) -> None:
    task_root = _create_multi_artifact_task(tmp_path, "customx", "bundle-task")
    resolver = TaskResolver()
    layout = resolver.resolve(task_id="bundle-task", data=task_root)

    assert layout.output_path.suffix == ""
    assert layout.evaluation_contract.grading is not None
    submission = layout.evaluation_contract.grading.submission
    assert submission.root_kind == "directory"
    assert tuple(entry.relative_path for entry in submission.entries) == ("before.csv", "after.csv")

    adapter = FileSubmissionTaskAdapter(DSLightingConfig())
    spec = adapter.build_file_submission_spec(layout, adapter.data_perception)
    adapter.cleanup()

    assert "Required output directory name" in spec.io_instructions
    assert "`before.csv`" in spec.io_instructions
    assert "`after.csv`" in spec.io_instructions
    assert "## Submission Artifact Requirements" in spec.description_text
