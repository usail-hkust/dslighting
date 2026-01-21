"""
Grading function for ScienceBench task 78 (protein stability prediction).
"""

from __future__ import annotations

import pandas as pd
from sklearn.metrics import mean_absolute_error

from benchmarks.sciencebench.grade_helpers import InvalidSubmissionError

REQUIRED_COLUMNS = {"test_data_id", "deltaTm"}


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    """
    Return the actual evaluation metric (MAE; lower is better).

    Both submission and answers must have columns: test_data_id, deltaTm.
    """
    if submission is None or submission.empty:
        raise InvalidSubmissionError("Submission is empty.")
    if answers is None or answers.empty:
        raise InvalidSubmissionError("Answer data is empty.")

    if not REQUIRED_COLUMNS.issubset(submission.columns):
        raise InvalidSubmissionError(f"Submission missing columns: {REQUIRED_COLUMNS - set(submission.columns)}")
    if not REQUIRED_COLUMNS.issubset(answers.columns):
        raise InvalidSubmissionError(f"Answers missing columns: {REQUIRED_COLUMNS - set(answers.columns)}")

    merged = pd.merge(
        answers[["test_data_id", "deltaTm"]],
        submission[["test_data_id", "deltaTm"]],
        on="test_data_id",
        how="inner",
        suffixes=("_true", "_pred"),
    )
    if len(merged) != len(answers):
        raise InvalidSubmissionError(
            f"Row alignment mismatch: merged={len(merged)} answers={len(answers)}. "
            "Ensure you predict for every test_data_id exactly once."
        )

    metric = mean_absolute_error(merged["deltaTm_true"], merged["deltaTm_pred"])
    print(f"MAE: {metric}")
    return float(metric)
