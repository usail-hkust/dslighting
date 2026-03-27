"""Grading function for ScienceBench task 34 (HRV analysis)."""

from __future__ import annotations

import math
from typing import Iterable

import pandas as pd

from dslighting.benchmark.grading.models import GradingRequest

TOLERANCE = 0.5
MIN_MATCH_RATIO = 0.9


def _iter_columns(df: pd.DataFrame) -> Iterable[str]:
    """Return columns in a deterministic order."""
    return list(df.columns)


def grade(request: GradingRequest) -> float:
    submission_path = request.submission.root
    answers_path = request.references.private_dir / "answer.csv"

    submission = pd.read_csv(submission_path)
    answers = pd.read_csv(answers_path)

    if submission.empty:
        print("Submission is empty.")
        return 0.0
    if answers.empty:
        print("Answer data is empty.")
        return 0.0

    missing_columns = set(answers.columns) - set(submission.columns)
    if missing_columns:
        print(f"Submission missing required columns: {sorted(missing_columns)}")
        return 0.0

    # Align column order and row count
    submission_aligned = submission[_iter_columns(answers)]
    if len(submission_aligned) != len(answers):
        print(f"Row count mismatch: submission {len(submission_aligned)} vs gold {len(answers)}")
        return 0.0

    matches = 0
    total = len(answers.columns)

    for column in answers.columns:
        diff = (submission_aligned[column] - answers[column]).abs().sum()
        if math.isnan(diff):
            print(f"Non-numeric values encountered in column '{column}'.")
            return 0.0
        if diff <= TOLERANCE:
            matches += 1

    ratio = matches / total if total else 0.0
    if ratio < MIN_MATCH_RATIO:
        print(f"HRV feature matches: {matches} / {total}")
        return 0.0

    return 1.0
