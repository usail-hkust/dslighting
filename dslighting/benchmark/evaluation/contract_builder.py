from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any

import pandas as pd

from dslighting.benchmark.evaluation.models import (
    EvaluationSemantics,
    TaskEvaluationContract,
    TaskEvaluationContractRef,
    TaskJudgeContract,
)
from dslighting.benchmark.grading.models import (
    ReferenceArtifacts,
    SubmissionArtifactContract,
    SubmissionValidationSpec,
    TaskGradingContract,
)


def _detect_api_version(
    *,
    explicit_api_version: str | None,
    evaluation_mode: str,
    grade_fn: Any | None,
) -> str:
    if explicit_api_version:
        return explicit_api_version
    if evaluation_mode == "judge_based":
        return "judge_v1"
    if grade_fn is not None:
        try:
            params = inspect.signature(grade_fn).parameters
            if len(params) == 1:
                return "artifact_v1"
        except (TypeError, ValueError):
            pass
    return "legacy_dataframe_v0"


def _resolve_semantics(competition: Any) -> EvaluationSemantics:
    leaderboard_path = getattr(competition, "leaderboard", None)
    objective = "higher_is_better"
    if leaderboard_path is not None:
        leaderboard_path = Path(leaderboard_path)
        if leaderboard_path.exists():
            try:
                leaderboard = pd.read_csv(leaderboard_path)
                grader = getattr(competition, "grader", None)
                if grader is not None and hasattr(grader, "is_lower_better") and "score" in leaderboard.columns:
                    objective = (
                        "lower_is_better" if grader.is_lower_better(leaderboard) else "higher_is_better"
                    )
            except Exception:
                objective = "higher_is_better"
    return EvaluationSemantics(objective=objective, leaderboard_path=leaderboard_path)


def build_task_evaluation_contract(
    *,
    competition: Any,
    source_id: str,
    engine_id: str,
    registry_root: Path | None,
    data_root: Path | None,
    mode: str,
    output_submission_path: Path | None = None,
    evaluation_mode: str | None = None,
) -> tuple[TaskEvaluationContract, TaskEvaluationContractRef]:
    task_id = str(getattr(competition, "id"))
    detected_mode = evaluation_mode or (
        "judge_based" if str(getattr(competition, "competition_type", "")).strip() == "open_ended" else "artifact_submission"
    )

    raw_dir = Path(getattr(competition, "raw_dir"))
    public_dir = Path(getattr(competition, "public_dir"))
    private_dir = Path(getattr(competition, "private_dir"))
    answers_path = Path(getattr(competition, "answers"))
    gold_submission_path = getattr(competition, "gold_submission", None)
    sample_submission_path = getattr(competition, "sample_submission", None)
    validate_fn = getattr(competition, "validate_fn", None)
    grade_fn = getattr(getattr(competition, "grader", None), "grade_fn", None)
    explicit_api_version = getattr(competition, "api_version", None)
    api_version = _detect_api_version(
        explicit_api_version=explicit_api_version,
        evaluation_mode=detected_mode,
        grade_fn=grade_fn,
    )
    semantics = _resolve_semantics(competition)
    output_path = output_submission_path or Path("submission.csv")

    if detected_mode == "artifact_submission":
        sample_name = sample_submission_path.name if isinstance(sample_submission_path, Path) else ""
        validation = SubmissionValidationSpec(
            expected_kind="file",
            expected_name=output_path.name,
            allowed_suffixes=(output_path.suffix.lower(),) if output_path.suffix else (),
        )
        submission = SubmissionArtifactContract(
            sample_submission_path=sample_submission_path if isinstance(sample_submission_path, Path) else None,
            output_submission_path=output_path,
            submission_filename=str(getattr(competition, "submission_filename", "") or sample_name),
            submission_format=output_path.suffix.lower(),
            validation=validation,
        )
        references = ReferenceArtifacts(
            task_root=raw_dir.parent,
            raw_dir=raw_dir,
            public_dir=public_dir,
            private_dir=private_dir,
            answers_path=answers_path,
            gold_submission_path=gold_submission_path if isinstance(gold_submission_path, Path) else None,
            sample_submission_path=sample_submission_path if isinstance(sample_submission_path, Path) else None,
        )
        grading = TaskGradingContract(
            task_id=task_id,
            source_id=source_id,
            engine_id=engine_id,
            api_version=api_version,
            grade_fn=grade_fn,
            validate_fn=validate_fn,
            submission=submission,
            references=references,
            leaderboard_path=Path(getattr(competition, "leaderboard"))
            if getattr(competition, "leaderboard", None) is not None
            else None,
        )
        judging = None
    else:
        grading = None
        judging = TaskJudgeContract(
            task_id=task_id,
            source_id=source_id,
            engine_id=engine_id,
            api_version=api_version,
            rubric_path=getattr(competition, "rubric_path", None),
            reference_artifacts_dir=raw_dir,
            judge_metadata={},
            judge_fn=getattr(competition, "judge_fn", None),
        )

    contract = TaskEvaluationContract(
        task_id=task_id,
        source_id=source_id,
        engine_id=engine_id,
        evaluation_mode=detected_mode,  # type: ignore[arg-type]
        api_version=api_version,
        evaluation_semantics=semantics,
        grading=grading,
        judging=judging,
    )
    ref = TaskEvaluationContractRef(
        task_id=task_id,
        source_id=source_id,
        engine_id=engine_id,
        evaluation_mode=detected_mode,
        api_version=api_version,
        registry_root=registry_root,
        data_root=data_root,
        mode=mode,
    )
    return contract, ref
