"""Grader for ScienceBench task 97 (formation energy prediction)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from benchmarks.sciencebench.grade_helpers import InvalidSubmissionError

TARGET_COL = "formation_energy"


def grade(submission, answers) -> float:
    """
    Return the actual evaluation metric (MSE; lower is better).

    `submission` and `answers` are pandas DataFrames loaded from CSV.
    """
    if not isinstance(submission, pd.DataFrame) or not isinstance(answers, pd.DataFrame):
        raise InvalidSubmissionError("Submission/answers must be CSV tables.")
    if TARGET_COL not in submission.columns:
        raise InvalidSubmissionError(f"Missing required column: {TARGET_COL}")
    if TARGET_COL not in answers.columns:
        raise InvalidSubmissionError(f"Answers missing required column: {TARGET_COL}")

    pred = pd.to_numeric(submission[TARGET_COL], errors="coerce").to_numpy(dtype=float)
    gold = pd.to_numeric(answers[TARGET_COL], errors="coerce").to_numpy(dtype=float)

    if pred.shape != gold.shape:
        raise InvalidSubmissionError(f"Shape mismatch: {pred.shape} vs {gold.shape}")
    if np.isnan(pred).any():
        raise InvalidSubmissionError("Submission contains non-numeric values.")

    mse = float(np.mean((pred - gold) ** 2))
    return mse
