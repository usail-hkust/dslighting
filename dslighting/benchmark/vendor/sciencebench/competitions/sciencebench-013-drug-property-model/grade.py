"""Grading function for ScienceBench Task 13 (HIV property prediction)."""

from __future__ import annotations

import pandas as pd
from sklearn.metrics import f1_score

from dslighting.benchmark.grading.models import GradingRequest

REQUIRED_COLUMNS = {"smiles", "HIV_active"}
F1_THRESHOLD = 0.43


def grade(request: GradingRequest) -> float:
    """
    Evaluate predictions using F1 score with ordering validation.

    Args:
        request: GradingRequest containing submission path and references

    Returns:
        1.0 if the SMILES ordering matches and F1 >= threshold; otherwise 0.0.
    """
    submission_path = request.submission.root
    answers_path = request.references.private_dir / "answer.csv"

    submission = pd.read_csv(submission_path)
    answers = pd.read_csv(answers_path)

    if submission.empty:
        print("Submission is empty.")
        return 0.0

    if not REQUIRED_COLUMNS.issubset(submission.columns):
        print(f"Submission missing required columns: {REQUIRED_COLUMNS - set(submission.columns)}")
        return 0.0

    if not REQUIRED_COLUMNS.issubset(answers.columns):
        print("Answer file is missing required columns.")
        return 0.0

    # Ensure ordering matches exactly.
    if list(submission["smiles"]) != list(answers["smiles"]):
        print("SMILES ordering mismatch.")
        return 0.0

    # Compute F1 score on the aligned columns.
    metric = f1_score(answers["HIV_active"].values, submission["HIV_active"].values)
    print(f"F1 score: {metric}")

    return 1.0 if metric >= F1_THRESHOLD else 0.0
