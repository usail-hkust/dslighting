"""Grading function for ScienceBench task 60 (nvc-accuracies)."""

from __future__ import annotations

import pandas as pd

from dslighting.benchmark.grading.models import GradingRequest


def _normalise(df: pd.DataFrame, column_order: pd.Index) -> pd.DataFrame:
    missing = set(column_order) - set(df.columns)
    if missing:
        raise ValueError(f"Submission missing required columns: {', '.join(sorted(missing))}")
    ordered = df.loc[:, column_order].copy()
    return ordered.sort_values(by=list(column_order)).reset_index(drop=True)


def grade(request: GradingRequest) -> float:
    submission_path = request.submission.root
    answers_path = request.references.private_dir / "answer.csv"

    submission = pd.read_csv(submission_path)
    answers = pd.read_csv(answers_path)

    column_order = answers.columns

    submission_sorted = _normalise(submission, column_order)
    answers_sorted = _normalise(answers, column_order)

    try:
        pd.testing.assert_frame_equal(
            submission_sorted,
            answers_sorted,
            check_dtype=False,
            check_exact=True,
        )
        return 1.0
    except AssertionError as exc:
        print(f"Mismatch detected: {exc}")
        return 0.0
