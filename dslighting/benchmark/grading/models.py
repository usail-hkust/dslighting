from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Literal, Mapping


@dataclass(frozen=True)
class SubmissionEntrySpec:
    relative_path: str
    kind: Literal["file", "directory"] = "file"
    format: str | None = None
    required: bool = True
    sample_path: Path | None = None
    description: str | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "kind": self.kind,
            "format": self.format,
            "required": self.required,
            "sample_path": str(self.sample_path) if self.sample_path else "",
            "description": self.description,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "SubmissionEntrySpec":
        sample_value = str(payload.get("sample_path") or "").strip()
        return cls(
            relative_path=str(payload.get("relative_path") or "").strip(),
            kind=str(payload.get("kind") or "file"),
            format=str(payload.get("format") or "").strip() or None,
            required=bool(payload.get("required", True)),
            sample_path=Path(sample_value) if sample_value else None,
            description=str(payload.get("description") or "").strip() or None,
        )


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
    entries: tuple[SubmissionEntrySpec, ...] = ()

    @property
    def root_kind(self) -> Literal["file", "directory"]:
        return "directory" if self.validation.expected_kind == "directory" else "file"

    @staticmethod
    def _normalize_suffix(value: str | None) -> str | None:
        raw = str(value or "").strip().lower()
        if not raw:
            return None
        if raw.startswith("."):
            return raw
        return f".{raw}"

    @classmethod
    def _build_validation(
        cls,
        *,
        expected_kind: Literal["file", "directory", "either"],
        output_path: Path,
        entries: tuple[SubmissionEntrySpec, ...],
        fallback_allowed_suffixes: tuple[str, ...] = (),
    ) -> SubmissionValidationSpec:
        if expected_kind == "directory":
            return SubmissionValidationSpec(
                expected_kind="directory",
                expected_name=output_path.name or None,
                required_children=tuple(
                    entry.relative_path for entry in entries if entry.required and entry.relative_path
                ),
            )

        allowed_suffixes: list[str] = []
        if output_path.suffix:
            allowed_suffixes.append(output_path.suffix.lower())
        elif entries:
            derived_suffix = cls._normalize_suffix(entries[0].format)
            if derived_suffix:
                allowed_suffixes.append(derived_suffix)
        allowed_suffixes.extend(
            suffix.lower()
            for suffix in fallback_allowed_suffixes
            if isinstance(suffix, str) and suffix
        )
        unique_suffixes = tuple(dict.fromkeys(allowed_suffixes))
        return SubmissionValidationSpec(
            expected_kind="file",
            expected_name=output_path.name or None,
            allowed_suffixes=unique_suffixes,
        )

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
                "root_kind": self.root_kind,
                "entries": [entry.to_payload() for entry in self.entries],
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
        raw_entries = source.get("entries") or ()
        entries = tuple(
            SubmissionEntrySpec.from_payload(entry)
            for entry in raw_entries
            if isinstance(entry, Mapping)
        )
        validation_payload = source.get("validation")
        if not isinstance(validation_payload, Mapping):
            submission_filename = str(source.get("submission_filename") or "").strip()
            expected_kind = str(source.get("root_kind") or "file")
            if not entries:
                entries = (
                    SubmissionEntrySpec(
                        relative_path=Path(output_value).name,
                        kind="file",
                        format=Path(output_value).suffix.lower().lstrip(".") or None,
                        required=True,
                        sample_path=Path(sample_value) if sample_value else None,
                    ),
                )
            validation = cls._build_validation(
                expected_kind="directory" if expected_kind == "directory" else "file",
                output_path=Path(output_value),
                entries=entries,
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
            entries=entries,
        )

    def with_output_path(self, output_path: Path) -> "SubmissionArtifactContract":
        entries = self.entries
        if self.root_kind == "file" and entries:
            first = entries[0]
            entries = (
                replace(
                    first,
                    relative_path=output_path.name,
                    format=first.format or (output_path.suffix.lower().lstrip(".") or None),
                ),
            ) + entries[1:]
        validation = self._build_validation(
            expected_kind=self.root_kind,
            output_path=output_path,
            entries=entries,
            fallback_allowed_suffixes=self.validation.allowed_suffixes,
        )
        return replace(self, output_submission_path=output_path, validation=validation, entries=entries)


@dataclass(frozen=True)
class SubmissionArtifact:
    root: Path
    kind: Literal["file", "directory"]
    format_hint: str | None
    expected_name: str | None
    entries: tuple[SubmissionEntrySpec, ...] = ()


@dataclass(frozen=True)
class ReferenceArtifacts:
    task_root: Path
    raw_dir: Path
    public_dir: Path
    private_dir: Path
    answers_path: Path | None
    gold_submission_path: Path | None
    sample_submission_path: Path | None
    answers_root: Path | None = None
    answer_entries: tuple[SubmissionEntrySpec, ...] = ()
    sample_entries: tuple[SubmissionEntrySpec, ...] = ()


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
