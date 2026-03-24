from __future__ import annotations

from pathlib import Path
from typing import Any

from dslighting.benchmark.grading.models import SubmissionEntrySpec


def _normalize_suffix(value: str | None) -> str | None:
    raw = str(value or "").strip().lower()
    if not raw:
        return None
    return raw if raw.startswith(".") else f".{raw}"


def _resolve_single_file_suffix(
    *,
    preferred_submission_name: str | None,
    sample_submission_path: Path | None,
    submission_entries: tuple[SubmissionEntrySpec, ...] = (),
    fallback_suffix: str = ".csv",
) -> str:
    if preferred_submission_name:
        preferred_suffix = Path(preferred_submission_name).suffix
        if preferred_suffix:
            return _normalize_suffix(preferred_suffix) or fallback_suffix

    if isinstance(sample_submission_path, Path) and sample_submission_path.suffix:
        return _normalize_suffix(sample_submission_path.suffix) or fallback_suffix

    if submission_entries:
        entry_suffix = _normalize_suffix(submission_entries[0].format)
        if entry_suffix:
            return entry_suffix

    return fallback_suffix


def resolve_output_artifact_path(
    *,
    task_id: str,
    unique_suffix: str,
    root_kind: str = "file",
    root_basename: str = "submission",
    preferred_submission_name: str | None = None,
    sample_submission_path: Path | None = None,
    submission_entries: tuple[SubmissionEntrySpec, ...] = (),
) -> Path:
    if str(root_kind).strip().lower() == "directory":
        return Path(f"{root_basename}_{task_id}_{unique_suffix}")

    suffix = _resolve_single_file_suffix(
        preferred_submission_name=preferred_submission_name,
        sample_submission_path=sample_submission_path,
        submission_entries=submission_entries,
    )
    return Path(f"submission_{task_id}_{unique_suffix}{suffix}")


def resolve_output_artifact_path_for_competition(
    *,
    task_id: str,
    competition: Any,
    unique_suffix: str,
) -> Path:
    evaluator_config = getattr(competition, "evaluator_config", None) or {}
    submission_config = evaluator_config.get("submission") if isinstance(evaluator_config, dict) else {}
    root_kind = (
        str(submission_config.get("root_kind") or "file")
        if isinstance(submission_config, dict)
        else "file"
    )
    root_basename = (
        str(submission_config.get("root_basename") or "submission").strip() or "submission"
        if isinstance(submission_config, dict)
        else "submission"
    )

    entries_payload = submission_config.get("entries") if isinstance(submission_config, dict) else ()
    submission_entries = tuple(
        SubmissionEntrySpec(
            relative_path=str(entry.get("relative_path") or "").strip(),
            kind=str(entry.get("kind") or "file"),
            format=str(entry.get("format") or "").strip() or None,
            required=bool(entry.get("required", True)),
            sample_path=Path(str(entry.get("sample") or "").strip()) if str(entry.get("sample") or "").strip() else None,
            description=str(entry.get("description") or "").strip() or None,
        )
        for entry in (entries_payload or ())
        if isinstance(entry, dict) and str(entry.get("relative_path") or "").strip()
    )

    return resolve_output_artifact_path(
        task_id=task_id,
        unique_suffix=unique_suffix,
        root_kind=root_kind,
        root_basename=root_basename,
        preferred_submission_name=getattr(competition, "submission_filename", None),
        sample_submission_path=getattr(competition, "sample_submission", None),
        submission_entries=submission_entries,
    )
