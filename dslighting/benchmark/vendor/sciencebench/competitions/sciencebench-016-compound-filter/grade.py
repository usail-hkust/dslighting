"""Grading function for ScienceBench task 16 (compound filter)."""

from __future__ import annotations

import pandas as pd

from dslighting.benchmark.grading.models import GradingRequest

REQUIRED_COLUMN = "SMILES"


def _normalize(df: pd.DataFrame) -> pd.Series:
    if REQUIRED_COLUMN in df.columns:
        series = df[REQUIRED_COLUMN]
    else:
        # Fallback: use the first column if it appears unnamed.
        series = df.iloc[:, 0]
    return series.dropna().astype(str).str.strip()


def grade(request: GradingRequest) -> float:
    """Return 1.0 when the submitted SMILES set matches the gold set."""
    submission_path = request.submission.root
    answers_path = request.references.private_dir / "answer.csv"

    # Try to read as CSV first, fall back to txt
    try:
        submission = pd.read_csv(submission_path)
    except:
        submission = pd.read_csv(submission_path, sep=None, header=None)

    answers = pd.read_csv(answers_path)

    if submission.empty:
        print("Submission is empty.")
        return 0.0
    if answers.empty:
        print("Answer set is empty.")
        return 0.0

    submitted = set(_normalize(submission))
    gold = set(_normalize(answers))

    if not gold:
        print("Gold result set is empty after normalization.")
        return 0.0

    overlap = len(submitted.intersection(gold)) / len(gold)
    print(f"Overlap: {overlap}")
    return 1.0 if overlap == 1.0 else 0.0
