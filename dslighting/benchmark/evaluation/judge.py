from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Mapping

from dslighting.benchmark.evaluation.models import TaskJudgeContract
from dslighting.benchmark.evaluation.outcome import EvaluationOutcome


class JudgeEvaluationService:
    async def evaluate(
        self,
        *,
        submission_path: Path,
        contract: TaskJudgeContract,
        mode: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> EvaluationOutcome:
        if contract.judge_fn is None:
            return EvaluationOutcome(
                score=None,
                submission_exists=submission_path.exists(),
                valid_submission=False,
                error_kind="judge_error",
                error_message=f"No judge_fn configured for task '{contract.task_id}'.",
                diagnostics={"mode": mode},
            )

        try:
            result = contract.judge_fn(
                submission_path=submission_path,
                contract=contract,
                mode=mode,
                metadata=dict(metadata or {}),
            )
            if inspect.isawaitable(result):
                result = await result
            if isinstance(result, EvaluationOutcome):
                return result
            score = float(result) if result is not None else None
            return EvaluationOutcome(
                score=score,
                submission_exists=submission_path.exists(),
                valid_submission=score is not None,
                error_kind="none" if score is not None else "judge_error",
                error_message=None if score is not None else "Judge returned no score.",
                diagnostics={},
            )
        except Exception as exc:
            return EvaluationOutcome(
                score=None,
                submission_exists=submission_path.exists(),
                valid_submission=False,
                error_kind="judge_error",
                error_message=str(exc),
                diagnostics={"exception_type": type(exc).__name__},
            )
