"""Grading function for ScienceBench task 15 (admet_ai)."""

from __future__ import annotations

import pandas as pd
from sklearn.metrics import roc_auc_score

REQUIRED_COLUMNS = {"Drug", "Y"}
AUC_THRESHOLD = 0.84


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    """Return 1.0 if ordering matches and ROC AUC >= threshold, else 0.0."""
    if submission.empty:
        print("Submission is empty.")
        return 0.0

    if not REQUIRED_COLUMNS.issubset(submission.columns):
        print(f"Submission missing required columns: {REQUIRED_COLUMNS - set(submission.columns)}")
        return 0.0

    if not REQUIRED_COLUMNS.issubset(answers.columns):
        print("Answer file is missing required columns.")
        return 0.0

    if list(submission["Drug"]) != list(answers["Drug"]):
        print("Drug ordering mismatch.")
        return 0.0

    try:
        auc = roc_auc_score(answers["Y"].values, submission["Y"].values)
    except ValueError as exc:
        print(f"Unable to compute ROC AUC: {exc}")
        return 0.0

    print(f"ROC AUC: {auc}")
    return 1.0 if auc >= AUC_THRESHOLD else 0.0
