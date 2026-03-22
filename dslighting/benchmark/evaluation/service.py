from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from dslighting.benchmark.evaluation.judge import JudgeEvaluationService
from dslighting.benchmark.evaluation.models import TaskEvaluationContract
from dslighting.benchmark.evaluation.outcome import EvaluationOutcome
from dslighting.benchmark.grading.errors import GradingExecutionError
from dslighting.benchmark.grading.service import SubmissionGradingService


class TaskEvaluationService:
    def __init__(
        self,
        submission_grading_service: SubmissionGradingService | None = None,
        judge_evaluation_service: JudgeEvaluationService | None = None,
    ) -> None:
        self.submission_grading_service = submission_grading_service or SubmissionGradingService()
        self.judge_evaluation_service = judge_evaluation_service or JudgeEvaluationService()

    async def evaluate(
        self,
        *,
        submission_path: Path,
        contract: TaskEvaluationContract,
        mode: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> EvaluationOutcome:
        if contract.evaluation_mode == "judge_based":
            if contract.judging is None:
                return EvaluationOutcome(
                    score=None,
                    submission_exists=submission_path.exists(),
                    valid_submission=False,
                    error_kind="judge_error",
                    error_message=f"No judge contract configured for task '{contract.task_id}'.",
                    diagnostics={},
                )
            return await self.judge_evaluation_service.evaluate(
                submission_path=submission_path,
                contract=contract.judging,
                mode=mode,
                metadata=metadata,
            )

        if contract.grading is None:
            return EvaluationOutcome(
                score=None,
                submission_exists=submission_path.exists(),
                valid_submission=False,
                error_kind="execution_error",
                error_message=f"No grading contract configured for task '{contract.task_id}'.",
                diagnostics={},
            )

        try:
            request = self.submission_grading_service.build_request(
                submission_path=submission_path,
                contract=contract.grading,
                mode=mode,
                metadata=metadata,
            )
            return self.submission_grading_service.grade(request, contract.grading)
        except GradingExecutionError as exc:
            return EvaluationOutcome(
                score=None,
                submission_exists=submission_path.exists(),
                valid_submission=False,
                error_kind="execution_error",
                error_message=str(exc),
                diagnostics={"exception_type": type(exc.__cause__ or exc).__name__},
            )
