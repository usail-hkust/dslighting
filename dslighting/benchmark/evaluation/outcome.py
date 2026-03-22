from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping


@dataclass(frozen=True)
class EvaluationOutcome:
    score: float | None
    submission_exists: bool
    valid_submission: bool
    error_kind: Literal["none", "invalid_submission", "execution_error", "judge_error"]
    error_message: str | None
    diagnostics: Mapping[str, Any]
