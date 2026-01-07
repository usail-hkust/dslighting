"""Grader for ScienceBench task 101 (experimental band-gap prediction)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from benchmarks.sciencebench.grade_helpers import InvalidSubmissionError

ID_COLUMN = "Unnamed: 0"
TARGET_COLUMN = "gap_expt_eV"


def grade(submission, answers) -> float:
    """
    Return the actual evaluation metric (MAE; lower is better).

    `submission` and `answers` are pandas DataFrames loaded from CSV.
    """
    if not isinstance(submission, pd.DataFrame) or not isinstance(answers, pd.DataFrame):
        raise InvalidSubmissionError("Submission/answers must be CSV tables.")

    for col in (ID_COLUMN, TARGET_COLUMN):
        if col not in submission.columns:
            raise InvalidSubmissionError(f"Missing required column in submission: {col}")
        if col not in answers.columns:
            raise InvalidSubmissionError(f"Missing required column in answers: {col}")

    sub = submission[[ID_COLUMN, TARGET_COLUMN]].copy()
    gold = answers[[ID_COLUMN, TARGET_COLUMN]].copy()

    sub[TARGET_COLUMN] = pd.to_numeric(sub[TARGET_COLUMN], errors="coerce")
    gold[TARGET_COLUMN] = pd.to_numeric(gold[TARGET_COLUMN], errors="coerce")

    if sub[TARGET_COLUMN].isna().any():
        raise InvalidSubmissionError("Submission contains non-numeric values.")

    merged = gold.merge(sub, on=ID_COLUMN, suffixes=("_gold", "_pred"), how="inner")
    if merged.empty:
        raise InvalidSubmissionError("No overlapping ids between submission and answers.")

    mae = float(
        np.mean(
            np.abs(
                merged[f"{TARGET_COLUMN}_gold"].to_numpy()
                - merged[f"{TARGET_COLUMN}_pred"].to_numpy()
            )
        )
    )
    return mae
