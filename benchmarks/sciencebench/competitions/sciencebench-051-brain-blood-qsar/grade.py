"""Grading function for ScienceBench task 51 (brain-blood QSAR)."""

from __future__ import annotations

import pandas as pd
from sklearn.metrics import balanced_accuracy_score

from benchmarks.sciencebench.grade_helpers import InvalidSubmissionError

REQUIRED_COLUMNS = {"MolID", "label"}


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    """
    Return the actual evaluation metric (balanced accuracy; higher is better).

    Both submission and answers must have columns: MolID,label.
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
        answers[["MolID", "label"]],
        submission[["MolID", "label"]],
        on="MolID",
        how="inner",
        suffixes=("_true", "_pred"),
    )
    if len(merged) != len(answers):
        raise InvalidSubmissionError(
            f"Row alignment mismatch: merged={len(merged)} answers={len(answers)}. "
            "Ensure you predict for every MolID exactly once."
        )

    score = balanced_accuracy_score(merged["label_true"], merged["label_pred"])
    print(f"Balanced accuracy: {score}")
    return float(score)
