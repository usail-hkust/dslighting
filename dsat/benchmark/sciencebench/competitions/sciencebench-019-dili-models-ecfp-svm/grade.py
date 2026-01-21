"""Grading function for ScienceBench Task 19 (DILI SVM models)."""

from __future__ import annotations

import pandas as pd
from sklearn.metrics import f1_score

from benchmarks.sciencebench.grade_helpers import InvalidSubmissionError

REQUIRED_COLUMNS = {"standardised_smiles", "label"}


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    """Return the F1 score between submission and answers."""
    if submission.empty:
        raise InvalidSubmissionError("Submission is empty.")
    if answers.empty:
        raise InvalidSubmissionError("Answer data is empty.")

    if not REQUIRED_COLUMNS.issubset(submission.columns):
        raise InvalidSubmissionError(f"Submission missing columns: {REQUIRED_COLUMNS - set(submission.columns)}")
    if not REQUIRED_COLUMNS.issubset(answers.columns):
        raise InvalidSubmissionError("Answers missing required columns.")

    if list(submission["standardised_smiles"]) != list(answers["standardised_smiles"]):
        raise InvalidSubmissionError("SMILES ordering mismatch.")

    gold_binary = (answers["label"].astype(str).str.upper() == "DILI").astype(int)
    pred_binary = (submission["label"].astype(str).str.upper() == "DILI").astype(int)

    f1 = f1_score(gold_binary, pred_binary, average="binary")
    print(f"F1 score: {f1}")
    return float(f1)
