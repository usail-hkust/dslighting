"""Grading function for ScienceBench task 67 (cogsci-pattern-high-sim)."""

from __future__ import annotations

import pandas as pd

from dslighting.benchmark.grading.models import GradingRequest

EXPECTED_COLUMNS = {"conscientiousness", "openness"}


def _listify(df: pd.DataFrame) -> list:
    if not EXPECTED_COLUMNS.issubset(df.columns):
        raise ValueError(f"Submission must include columns: {', '.join(sorted(EXPECTED_COLUMNS))}")
    rounded = df.copy()
    numeric_cols = [col for col in EXPECTED_COLUMNS if pd.api.types.is_numeric_dtype(df[col])]
    rounded[numeric_cols] = rounded[numeric_cols].round()
    return rounded["conscientiousness"].tolist() + rounded["openness"].tolist()


def grade(request: GradingRequest) -> float:
    submission_path = request.submission.root
    answers_path = request.references.private_dir / "answer.csv"

    submission = pd.read_csv(submission_path)
    answers = pd.read_csv(answers_path)

    submission_vector = _listify(submission)
    answers_vector = _listify(answers)

    if len(submission_vector) != len(answers_vector):
        print("Vector length mismatch between submission and answers.")
        return 0.0

    matches = sum(int(a == b) for a, b in zip(submission_vector, answers_vector))
    total = len(answers_vector)
    if matches != total:
        print(f"Matched {matches} of {total} rounded entries.")
        return 0.0

    return 1.0
