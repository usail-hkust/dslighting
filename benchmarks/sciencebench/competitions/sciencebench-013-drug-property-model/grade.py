"""Grading function for ScienceBench Task 13 (HIV property prediction)."""

from __future__ import annotations

import pandas as pd
from sklearn.metrics import f1_score

from benchmarks.sciencebench.grade_helpers import InvalidSubmissionError

REQUIRED_COLUMNS = {"smiles", "HIV_active"}


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    """
    Return the actual evaluation metric (F1; higher is better) with ordering validation.

    Args:
        submission: DataFrame produced by the participant.
        answers: Ground-truth DataFrame provided by the benchmark.

    Returns:
        F1 score (float).
    """
    if submission.empty:
        raise InvalidSubmissionError("Submission is empty.")

    if not REQUIRED_COLUMNS.issubset(submission.columns):
        raise InvalidSubmissionError(
            f"Submission missing required columns: {REQUIRED_COLUMNS - set(submission.columns)}"
        )

    if not REQUIRED_COLUMNS.issubset(answers.columns):
        raise InvalidSubmissionError("Answer file is missing required columns.")

    # Ensure ordering matches exactly.
    if list(submission["smiles"]) != list(answers["smiles"]):
        raise InvalidSubmissionError("SMILES ordering mismatch.")

    # Compute F1 score on the aligned columns.
    y_true = answers["HIV_active"].astype(int).values
    y_pred_raw = submission["HIV_active"].astype(float).values
    # Allow probability submissions by thresholding at 0.5.
    y_pred = (y_pred_raw >= 0.5).astype(int)

    metric = f1_score(y_true, y_pred)
    print(f"F1 score: {metric}")

    return float(metric)
