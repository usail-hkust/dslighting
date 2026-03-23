from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from dslighting.benchmark.evaluation import (
    EvaluationContractResolver,
    TaskEvaluationContractRef,
    TaskEvaluationService,
)
from dslighting.benchmark.evaluation.contract_builder import build_task_evaluation_contract
from dslighting.benchmark.grading.helpers import read_reference_child_csv, read_submission_child_csv
from dslighting.benchmark.reporting import CompetitionReportBuilder


class _FakeGrader:
    def __init__(self, grade_fn):
        self.grade_fn = grade_fn

    @staticmethod
    def is_lower_better(_leaderboard):
        return False


class _FakeCompetition:
    def __init__(self, tmp_path: Path, grade_fn):
        self.id = "demo-task"
        self.description = "demo"
        self.grader = _FakeGrader(grade_fn)
        self.answers = tmp_path / "prepared" / "private" / "answers.csv"
        self.gold_submission = self.answers
        self.sample_submission = tmp_path / "prepared" / "public" / "sample_submission.csv"
        self.submission_filename = "sample_submission.csv"
        self.competition_type = "tabular"
        self.raw_dir = tmp_path / "raw"
        self.public_dir = tmp_path / "prepared" / "public"
        self.private_dir = tmp_path / "prepared" / "private"
        self.checksums = tmp_path / "checksums.yaml"
        self.leaderboard = tmp_path / "leaderboard.csv"
        self.api_version = None
        self.validate_fn = None
        self.evaluator_config = {}


def _prepare_files(tmp_path: Path) -> Path:
    (tmp_path / "prepared" / "public").mkdir(parents=True)
    (tmp_path / "prepared" / "private").mkdir(parents=True)
    (tmp_path / "raw").mkdir(parents=True)
    (tmp_path / "prepared" / "public" / "sample_submission.csv").write_text(
        "prediction\n0\n", encoding="utf-8"
    )
    (tmp_path / "prepared" / "private" / "answers.csv").write_text(
        "prediction\n1\n", encoding="utf-8"
    )
    (tmp_path / "leaderboard.csv").write_text("score\n0.5\n0.4\n0.3\n", encoding="utf-8")
    (tmp_path / "checksums.yaml").write_text("{}", encoding="utf-8")
    return tmp_path / "submission.csv"


@pytest.mark.asyncio
async def test_submission_grading_service_supports_legacy_dataframe_contract(tmp_path: Path) -> None:
    submission_path = _prepare_files(tmp_path)
    submission_path.write_text("prediction\n1\n", encoding="utf-8")

    def grade(submission, answers):
        return float((submission["prediction"] == answers["prediction"]).mean())

    competition = _FakeCompetition(tmp_path, grade)
    contract, _ = build_task_evaluation_contract(
        competition=competition,
        source_id="customx",
        engine_id="mle",
        registry_root=tmp_path,
        data_root=tmp_path.parent,
        mode="test",
        output_submission_path=submission_path,
        evaluation_mode="artifact_submission",
    )

    outcome = await TaskEvaluationService().evaluate(
        submission_path=submission_path,
        contract=contract,
        mode="test",
    )

    assert outcome.valid_submission is True
    assert outcome.score == 1.0
    assert outcome.error_kind == "none"


@pytest.mark.asyncio
async def test_submission_grading_service_supports_artifact_v1_contract(tmp_path: Path) -> None:
    submission_path = _prepare_files(tmp_path)
    submission_path.write_text("prediction\n1\n", encoding="utf-8")

    def grade(request):
        import pandas as pd

        pred = pd.read_csv(request.submission.root)
        gold = pd.read_csv(request.references.answers_path)
        return float((pred["prediction"] == gold["prediction"]).mean())

    competition = _FakeCompetition(tmp_path, grade)
    competition.api_version = "artifact_v1"
    contract, _ = build_task_evaluation_contract(
        competition=competition,
        source_id="customx",
        engine_id="mle",
        registry_root=tmp_path,
        data_root=tmp_path.parent,
        mode="test",
        output_submission_path=submission_path,
        evaluation_mode="artifact_submission",
    )

    outcome = await TaskEvaluationService().evaluate(
        submission_path=submission_path,
        contract=contract,
        mode="test",
    )

    assert outcome.valid_submission is True
    assert outcome.score == 1.0


@pytest.mark.asyncio
async def test_submission_grading_service_supports_directory_artifact_contract(tmp_path: Path) -> None:
    _prepare_files(tmp_path)
    submission_dir = tmp_path / "submission_bundle"
    submission_dir.mkdir()
    (submission_dir / "before.csv").write_text("prediction\n1\n", encoding="utf-8")
    (submission_dir / "after.csv").write_text("prediction\n1\n", encoding="utf-8")
    (tmp_path / "prepared" / "private" / "before.csv").write_text("prediction\n1\n", encoding="utf-8")
    (tmp_path / "prepared" / "private" / "after.csv").write_text("prediction\n1\n", encoding="utf-8")
    (tmp_path / "prepared" / "public" / "sample_before.csv").write_text("prediction\n0\n", encoding="utf-8")
    (tmp_path / "prepared" / "public" / "sample_after.csv").write_text("prediction\n0\n", encoding="utf-8")

    def grade(request):
        before_pred = read_submission_child_csv(request, "before.csv")
        after_pred = read_submission_child_csv(request, "after.csv")
        before_gold = read_reference_child_csv(request, "before.csv")
        after_gold = read_reference_child_csv(request, "after.csv")
        before_score = float((before_pred["prediction"] == before_gold["prediction"]).mean())
        after_score = float((after_pred["prediction"] == after_gold["prediction"]).mean())
        return (before_score + after_score) / 2.0

    competition = _FakeCompetition(tmp_path, grade)
    competition.api_version = "artifact_v1"
    competition.evaluator_config = {
        "submission": {
            "root_kind": "directory",
            "root_basename": "submission_bundle",
            "entries": [
                {
                    "relative_path": "before.csv",
                    "format": "csv",
                    "sample_path": tmp_path / "prepared" / "public" / "sample_before.csv",
                },
                {
                    "relative_path": "after.csv",
                    "format": "csv",
                    "sample_path": tmp_path / "prepared" / "public" / "sample_after.csv",
                },
            ],
        },
        "references": {
            "root_kind": "directory",
            "root_path": tmp_path / "prepared" / "private",
            "entries": [
                {"relative_path": "before.csv"},
                {"relative_path": "after.csv"},
            ],
        },
    }
    contract, _ = build_task_evaluation_contract(
        competition=competition,
        source_id="customx",
        engine_id="mle",
        registry_root=tmp_path,
        data_root=tmp_path.parent,
        mode="test",
        output_submission_path=submission_dir,
        evaluation_mode="artifact_submission",
    )

    outcome = await TaskEvaluationService().evaluate(
        submission_path=submission_dir,
        contract=contract,
        mode="test",
    )

    assert contract.grading is not None
    assert contract.grading.submission.root_kind == "directory"
    assert outcome.valid_submission is True
    assert outcome.score == 1.0


def test_competition_report_builder_uses_shared_semantics(tmp_path: Path) -> None:
    leaderboard = tmp_path / "leaderboard.csv"
    leaderboard.write_text("score\n0.9\n0.8\n0.7\n0.6\n", encoding="utf-8")
    builder = CompetitionReportBuilder()

    from dslighting.benchmark.evaluation.models import EvaluationOutcome, EvaluationSemantics

    report = builder.build(
        outcome=EvaluationOutcome(
            score=0.95,
            submission_exists=True,
            valid_submission=True,
            error_kind="none",
            error_message=None,
            diagnostics={},
        ),
        semantics=EvaluationSemantics(
            objective="higher_is_better",
            leaderboard_path=leaderboard,
        ),
        competition_id="demo-task",
        submission_path=tmp_path / "submission.csv",
    )

    assert report.gold_medal is True
    assert report.valid_submission is True
    assert report.is_lower_better is False


def test_evaluation_contract_resolver_hydrates_from_contract_ref(tmp_path: Path) -> None:
    source_root = tmp_path / "customx"
    task_id = "demo-task"
    task_root = source_root / task_id
    public_dir = task_root / "prepared" / "public"
    private_dir = task_root / "prepared" / "private"
    raw_dir = task_root / "raw"
    public_dir.mkdir(parents=True)
    private_dir.mkdir(parents=True)
    raw_dir.mkdir(parents=True)
    (task_root / "description.md").write_text("demo", encoding="utf-8")
    (task_root / "prepare.py").write_text(
        "def prepare(raw, public, private):\n    return public\n",
        encoding="utf-8",
    )
    (task_root / "grade.py").write_text(
        "def grade(submission, answers):\n    return float((submission['prediction'] == answers['prediction']).mean())\n",
        encoding="utf-8",
    )
    (task_root / "leaderboard.csv").write_text("score\n1.0\n0.9\n", encoding="utf-8")
    (task_root / "checksums.yaml").write_text("{}", encoding="utf-8")
    (public_dir / "sample_submission.csv").write_text("prediction\n0\n", encoding="utf-8")
    (private_dir / "answers.csv").write_text("prediction\n1\n", encoding="utf-8")
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
    (source_root / "benchmark.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "source_id": "customx",
                "contract_id": "mle_task_contract/v1",
                "engine_id": "mle",
                "registry_root": ".",
            }
        ),
        encoding="utf-8",
    )

    ref = TaskEvaluationContractRef(
        task_id=task_id,
        source_id="customx",
        engine_id="mle",
        evaluation_mode="artifact_submission",
        api_version="legacy_dataframe_v0",
        registry_root=source_root,
        data_root=source_root,
        mode="test",
    )
    contract = EvaluationContractResolver().hydrate(ref)

    assert contract.task_id == task_id
    assert contract.grading is not None
    assert contract.grading.references.answers_path == private_dir / "answers.csv"
