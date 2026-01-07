"""Grading function for ScienceBench task 15 (admet_ai)."""

from __future__ import annotations

import pandas as pd
from sklearn.metrics import roc_auc_score

from benchmarks.sciencebench.grade_helpers import InvalidSubmissionError

REQUIRED_COLUMNS = {"Drug_ID", "Y"}


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    """Return the actual evaluation metric (ROC-AUC; higher is better)."""
    if submission.empty:
        raise InvalidSubmissionError("Submission is empty.")

    if not REQUIRED_COLUMNS.issubset(submission.columns):
        raise InvalidSubmissionError(
            f"Submission missing required columns: {REQUIRED_COLUMNS - set(submission.columns)}"
        )

    if not REQUIRED_COLUMNS.issubset(answers.columns):
        raise InvalidSubmissionError("Answer file is missing required columns.")

    # Align on identifier (avoid relying on ordering).
    merged = pd.merge(
        answers[["Drug_ID", "Y"]],
        submission[["Drug_ID", "Y"]],
        on="Drug_ID",
        how="inner",
        suffixes=("_true", "_pred"),
    )
    if len(merged) != len(answers):
        raise InvalidSubmissionError(
            f"Row alignment mismatch: merged={len(merged)} answers={len(answers)}. "
            "Ensure you predict for every Drug_ID exactly once."
        )

    try:
        y_true = merged["Y_true"].astype(int).values
        y_pred = merged["Y_pred"].astype(float).values
        auc = roc_auc_score(y_true, y_pred)
    except ValueError as exc:
        raise InvalidSubmissionError(f"Unable to compute ROC AUC: {exc}") from exc

    print(f"ROC AUC: {auc}")
    return float(auc)
