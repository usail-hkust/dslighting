"""Grading function for ScienceBench task 2 (mat_feature_select)."""

import pandas as pd

from dslighting.benchmark.grading.models import GradingRequest


THRESHOLD = 14  # minimum number of exactly-matching columns required


def _round_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Round numeric columns to 4 decimal places to mirror original evaluation."""
    if df.empty:
        return df
    return df.round(decimals=4)


def grade(request: GradingRequest) -> float:
    """Return 1.0 when at least `THRESHOLD` columns match exactly, else 0.0."""
    submission_path = request.submission.root
    answers_path = request.references.private_dir / "answer.csv"

    submission = pd.read_csv(submission_path)
    answers = pd.read_csv(answers_path)

    # Align formatting with the reference evaluation script
    submission_rounded = _round_numeric(submission.copy())
    answers_rounded = _round_numeric(answers.copy())

    overlap = 0
    for column in answers_rounded.columns:
        if column not in submission_rounded.columns:
            continue
        if submission_rounded[column].equals(answers_rounded[column]):
            overlap += 1

    if overlap >= THRESHOLD:
        return 1.0
    return 0.0
