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
    SubmissionEntrySpec,
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


def _coerce_entry_specs(entries_payload: Any) -> tuple[SubmissionEntrySpec, ...]:
    entries: list[SubmissionEntrySpec] = []
    for entry in entries_payload or ():
        if not isinstance(entry, dict):
            continue
        sample_path = entry.get("sample_path")
        entries.append(
            SubmissionEntrySpec(
                relative_path=str(entry.get("relative_path") or "").strip(),
                kind=str(entry.get("kind") or "file"),
                format=str(entry.get("format") or "").strip() or None,
                required=bool(entry.get("required", True)),
                sample_path=Path(sample_path) if isinstance(sample_path, Path) else None,
                description=str(entry.get("description") or "").strip() or None,
            )
        )
    return tuple(entry for entry in entries if entry.relative_path)


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
    evaluator_config = getattr(competition, "evaluator_config", None) or {}
    submission_config = evaluator_config.get("submission") if isinstance(evaluator_config, dict) else {}
    reference_config = evaluator_config.get("references") if isinstance(evaluator_config, dict) else {}

    submission_entries = _coerce_entry_specs(
        submission_config.get("entries") if isinstance(submission_config, dict) else ()
    )
    submission_root_kind = (
        str(submission_config.get("root_kind") or "file")
        if isinstance(submission_config, dict)
        else "file"
    )
    submission_root_basename = (
        str(submission_config.get("root_basename") or "submission").strip() or "submission"
        if isinstance(submission_config, dict)
        else "submission"
    )
    sample_submission_path = getattr(competition, "sample_submission", None)

    if output_submission_path is None:
        if submission_root_kind == "directory":
            output_path = Path(submission_root_basename)
        else:
            derived_suffix = (
                SubmissionArtifactContract._normalize_suffix(submission_entries[0].format)
                if submission_entries
                else None
            )
            if not derived_suffix and isinstance(sample_submission_path, Path) and sample_submission_path.suffix:
                derived_suffix = sample_submission_path.suffix.lower()
            output_path = Path(f"{submission_root_basename}{derived_suffix or '.csv'}")
    else:
        output_path = output_submission_path

    if detected_mode == "artifact_submission":
        sample_name = sample_submission_path.name if isinstance(sample_submission_path, Path) else ""
        if not submission_entries:
            submission_entries = (
                SubmissionEntrySpec(
                    relative_path=output_path.name,
                    kind="file",
                    format=output_path.suffix.lower().lstrip(".") or None,
                    required=True,
                    sample_path=sample_submission_path if isinstance(sample_submission_path, Path) else None,
                ),
            )
        validation = SubmissionArtifactContract._build_validation(
            expected_kind="directory" if submission_root_kind == "directory" else "file",
            output_path=output_path,
            entries=submission_entries,
        )
        submission = SubmissionArtifactContract(
            sample_submission_path=sample_submission_path if isinstance(sample_submission_path, Path) else None,
            output_submission_path=output_path,
            submission_filename=str(getattr(competition, "submission_filename", "") or output_path.name or sample_name),
            submission_format=output_path.suffix.lower() if output_path.suffix else "",
            validation=validation,
            entries=submission_entries,
        )
        answer_entries = _coerce_entry_specs(
            reference_config.get("entries") if isinstance(reference_config, dict) else ()
        )
        if not answer_entries and submission_root_kind == "directory":
            answer_entries = tuple(
                SubmissionEntrySpec(
                    relative_path=entry.relative_path,
                    kind=entry.kind,
                    format=entry.format,
                    required=entry.required,
                    description=entry.description,
                )
                for entry in submission_entries
            )
        answers_root_value = (
            reference_config.get("root_path") if isinstance(reference_config, dict) else None
        )
        answers_root = (
            Path(answers_root_value)
            if isinstance(answers_root_value, Path)
            else (private_dir if submission_root_kind == "directory" else None)
        )
        references = ReferenceArtifacts(
            task_root=raw_dir.parent,
            raw_dir=raw_dir,
            public_dir=public_dir,
            private_dir=private_dir,
            answers_path=answers_path,
            gold_submission_path=gold_submission_path if isinstance(gold_submission_path, Path) else None,
            sample_submission_path=sample_submission_path if isinstance(sample_submission_path, Path) else None,
            answers_root=answers_root,
            answer_entries=answer_entries,
            sample_entries=tuple(
                SubmissionEntrySpec(
                    relative_path=entry.relative_path,
                    kind=entry.kind,
                    format=entry.format,
                    required=entry.required,
                    sample_path=entry.sample_path,
                    description=entry.description,
                )
                for entry in submission_entries
                if entry.sample_path is not None
            ),
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
