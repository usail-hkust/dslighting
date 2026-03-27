"""Grading function for ScienceBench task 58 (nvc-gen-ind)."""

from __future__ import annotations

import pandas as pd

from dslighting.benchmark.grading.models import GradingRequest

EXPECTED_COLUMNS = ["Model", "Rule", "Num persons"]


def _normalise(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

    if all(column in df.columns for column in EXPECTED_COLUMNS):
        result = df[EXPECTED_COLUMNS].copy()
    elif len(df.columns) == 1:
        column = df.columns[0]
        split = df[column].astype(str).str.split(";", expand=True)
        if split.shape[1] != 3:
            raise ValueError("Unable to parse semicolon-separated submission format.")
        split.columns = EXPECTED_COLUMNS
        result = split
    else:
        raise ValueError("Submission must contain columns 'Model', 'Rule', 'Num persons'.")

    result["Model"] = result["Model"].astype(str).str.strip()
    result["Rule"] = result["Rule"].astype(str).str.strip()
    result["Num persons"] = result["Num persons"].astype(int)
    return result


def grade(request: GradingRequest) -> float:
    submission_path = request.submission.root
    answers_path = request.references.private_dir / "answer.csv"

    submission = pd.read_csv(submission_path)
    answers = pd.read_csv(answers_path)

    submission_norm = _normalise(submission)
    answers_norm = _normalise(answers)

    submission_sorted = submission_norm.sort_values(["Model", "Rule"]).reset_index(drop=True)
    answers_sorted = answers_norm.sort_values(["Model", "Rule"]).reset_index(drop=True)

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
