"""Grading function for ScienceBench task 21 (deforestation rate)."""

from __future__ import annotations

import pandas as pd

REQUIRED_COLUMN = "percentage_deforestation"


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    """Return 1 - relative error (clipped at 0) between submission and answers."""
    if submission.empty:
        print("Submission is empty.")
        return 0.0
    if answers.empty:
        print("Answer data is empty.")
        return 0.0

    if REQUIRED_COLUMN not in submission.columns:
        print(f"Submission missing column: {REQUIRED_COLUMN}")
        return 0.0
    if REQUIRED_COLUMN not in answers.columns:
        print("Answers missing required column.")
        return 0.0

    pred_value = float(submission[REQUIRED_COLUMN].iloc[0])
    gold_value = float(answers[REQUIRED_COLUMN].iloc[0])

    if gold_value == 0:
        relative_error = abs(pred_value - gold_value)
    else:
        relative_error = abs(pred_value - gold_value) / abs(gold_value)

    print(f"Relative error: {relative_error}")
    return max(0.0, 1.0 - relative_error)
