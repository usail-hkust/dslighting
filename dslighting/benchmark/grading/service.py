from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Mapping

from dslighting.benchmark.evaluation.outcome import EvaluationOutcome
from dslighting.benchmark.grading.errors import (
    GradingExecutionError,
    InvalidSubmissionError,
    SubmissionValidationError,
)
from dslighting.benchmark.grading.helpers import load_artifact
from dslighting.benchmark.grading.models import (
    GradingContext,
    GradingRequest,
    SubmissionArtifact,
    SubmissionArtifactContract,
    TaskGradingContract,
)


class SubmissionGradingService:
    def build_request(
        self,
        *,
        submission_path: Path,
        contract: TaskGradingContract,
        mode: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> GradingRequest:
        artifact_contract = contract.submission.with_output_path(submission_path)
        kind = artifact_contract.root_kind
        if submission_path.exists():
            kind = "directory" if submission_path.is_dir() else "file"
        artifact = SubmissionArtifact(
            root=submission_path,
            kind=kind,
            format_hint=submission_path.suffix.lower() or artifact_contract.submission_format or None,
            expected_name=artifact_contract.validation.expected_name,
            entries=artifact_contract.entries,
        )
        context = GradingContext(
            task_id=contract.task_id,
            source_id=contract.source_id,
            engine_id=contract.engine_id,
            mode=mode,
            metadata=dict(metadata or {}),
        )
        return GradingRequest(
            submission=artifact,
            references=contract.references,
            context=context,
        )

    def validate(self, request: GradingRequest, contract: TaskGradingContract) -> None:
        path = request.submission.root
        validation = contract.submission.with_output_path(path).validation

        if not path.exists():
            raise SubmissionValidationError(f"Submission path does not exist: {path}")

        if validation.expected_kind == "file" and not path.is_file():
            raise SubmissionValidationError(f"Expected submission file, got: {path}")
        if validation.expected_kind == "directory" and not path.is_dir():
            raise SubmissionValidationError(f"Expected submission directory, got: {path}")

        if validation.expected_name and path.name != validation.expected_name:
            raise SubmissionValidationError(
                f"Unexpected submission name '{path.name}', expected '{validation.expected_name}'."
            )

        if validation.allowed_suffixes and path.is_file():
            suffix = path.suffix.lower()
            if suffix not in validation.allowed_suffixes:
                raise SubmissionValidationError(
                    f"Unexpected submission suffix '{suffix}', expected one of {validation.allowed_suffixes}."
                )

        if validation.required_children and path.is_dir():
            missing = [child for child in validation.required_children if not (path / child).exists()]
            if missing:
                raise SubmissionValidationError(
                    f"Submission directory is missing required children: {missing}"
                )

        if contract.validate_fn is not None:
            contract.validate_fn(request)

    def _invoke_legacy_dataframe(
        self,
        request: GradingRequest,
        contract: TaskGradingContract,
    ) -> float | None:
        submission_obj = load_artifact(request.submission.root)
        answers_obj = load_artifact(request.references.answers_path)
        return contract.grade_fn(submission_obj, answers_obj)

    def _invoke_grade_fn(
        self,
        request: GradingRequest,
        contract: TaskGradingContract,
    ) -> float | None:
        api_version = contract.api_version.strip()
        if api_version == "artifact_v1":
            return contract.grade_fn(request)
        if api_version in {"legacy_dataframe_v0", "artifact_v0"}:
            return self._invoke_legacy_dataframe(request, contract)

        # Best-effort escape hatch while the task catalog is still migrating.
        try:
            parameters = inspect.signature(contract.grade_fn).parameters
            if len(parameters) == 1:
                return contract.grade_fn(request)
        except (TypeError, ValueError):
            pass
        return self._invoke_legacy_dataframe(request, contract)

    def grade(self, request: GradingRequest, contract: TaskGradingContract) -> EvaluationOutcome:
        submission_exists = request.submission.root.exists()
        try:
            self.validate(request, contract)
            score = self._invoke_grade_fn(request, contract)
            score_value = float(score) if score is not None else None
            return EvaluationOutcome(
                score=score_value,
                submission_exists=submission_exists,
                valid_submission=score_value is not None,
                error_kind="none" if score_value is not None else "invalid_submission",
                error_message=None if score_value is not None else "Grader returned no score.",
                diagnostics={"api_version": contract.api_version},
            )
        except (InvalidSubmissionError, SubmissionValidationError) as exc:
            return EvaluationOutcome(
                score=None,
                submission_exists=submission_exists,
                valid_submission=False,
                error_kind="invalid_submission",
                error_message=str(exc),
                diagnostics={"api_version": contract.api_version},
            )
        except Exception as exc:
            raise GradingExecutionError(str(exc)) from exc
