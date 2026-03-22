from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Literal, Mapping


@dataclass(frozen=True)
class SubmissionValidationSpec:
    expected_kind: Literal["file", "directory", "either"]
    expected_name: str | None
    required_children: tuple[str, ...] = ()
    allowed_suffixes: tuple[str, ...] = ()


@dataclass(frozen=True)
class SubmissionArtifactContract:
    sample_submission_path: Path | None
    output_submission_path: Path
    submission_filename: str
    submission_format: str
    validation: SubmissionValidationSpec

    def to_payload(self) -> dict[str, Any]:
        return {
            "sample_submission_path": str(self.sample_submission_path) if self.sample_submission_path else "",
            "submission_filename": self.submission_filename,
            "submission_format": self.submission_format,
            "output_submission_path": str(self.output_submission_path),
            "submission_artifact_contract": {
                "sample_submission_path": str(self.sample_submission_path) if self.sample_submission_path else "",
                "output_submission_path": str(self.output_submission_path),
                "submission_filename": self.submission_filename,
                "submission_format": self.submission_format,
                "validation": {
                    "expected_kind": self.validation.expected_kind,
                    "expected_name": self.validation.expected_name,
                    "required_children": list(self.validation.required_children),
                    "allowed_suffixes": list(self.validation.allowed_suffixes),
                },
            },
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "SubmissionArtifactContract | None":
        nested = payload.get("submission_artifact_contract")
        source = nested if isinstance(nested, Mapping) else payload

        output_value = str(source.get("output_submission_path") or "").strip()
        if not output_value:
            return None

        sample_value = str(source.get("sample_submission_path") or "").strip()
        validation_payload = source.get("validation")
        if not isinstance(validation_payload, Mapping):
            submission_filename = str(source.get("submission_filename") or "").strip()
            expected_name = Path(output_value).name or None
            suffix = Path(output_value).suffix.lower()
            validation = SubmissionValidationSpec(
                expected_kind="file",
                expected_name=expected_name,
                allowed_suffixes=(suffix,) if suffix else (),
            )
        else:
            validation = SubmissionValidationSpec(
                expected_kind=str(validation_payload.get("expected_kind") or "file"),
                expected_name=str(validation_payload.get("expected_name") or "").strip() or None,
                required_children=tuple(str(x) for x in validation_payload.get("required_children") or ()),
                allowed_suffixes=tuple(str(x) for x in validation_payload.get("allowed_suffixes") or ()),
            )
            submission_filename = str(source.get("submission_filename") or "").strip()

        return cls(
            sample_submission_path=Path(sample_value) if sample_value else None,
            output_submission_path=Path(output_value),
            submission_filename=submission_filename,
            submission_format=str(source.get("submission_format") or "").strip(),
            validation=validation,
        )

    def with_output_path(self, output_path: Path) -> "SubmissionArtifactContract":
        validation = replace(
            self.validation,
            expected_name=output_path.name if self.validation.expected_name else None,
            allowed_suffixes=(output_path.suffix.lower(),)
            if output_path.suffix
            else self.validation.allowed_suffixes,
        )
        return replace(self, output_submission_path=output_path, validation=validation)


@dataclass(frozen=True)
class SubmissionArtifact:
    root: Path
    kind: Literal["file", "directory"]
    format_hint: str | None
    expected_name: str | None


@dataclass(frozen=True)
class ReferenceArtifacts:
    task_root: Path
    raw_dir: Path
    public_dir: Path
    private_dir: Path
    answers_path: Path
    gold_submission_path: Path | None
    sample_submission_path: Path | None


@dataclass(frozen=True)
class GradingContext:
    task_id: str
    source_id: str
    engine_id: str
    mode: str
    metadata: Mapping[str, Any]


@dataclass(frozen=True)
class GradingRequest:
    submission: SubmissionArtifact
    references: ReferenceArtifacts
    context: GradingContext


@dataclass(frozen=True)
class TaskGradingContract:
    task_id: str
    source_id: str
    engine_id: str
    api_version: str
    grade_fn: Callable[..., float]
    validate_fn: Callable[[GradingRequest], None] | None
    submission: SubmissionArtifactContract
    references: ReferenceArtifacts
    leaderboard_path: Path | None
