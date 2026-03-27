"""Grading function for ScienceBench task 15 (admet_ai)."""

from __future__ import annotations

import pandas as pd
from sklearn.metrics import roc_auc_score

from dslighting.benchmark.grading.models import GradingRequest

REQUIRED_COLUMNS = {"Drug", "Y"}
THRESHOLD = 0.84


def grade(request: GradingRequest) -> float:
    """Return 1.0 if ROC AUC >= 0.84 and Drug ordering matches; otherwise 0.0."""
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

    if list(submission["Drug"]) != list(answers["Drug"]):
        print("Drug ordering mismatch.")
        return 0.0

    try:
        auc = roc_auc_score(answers["Y"].values, submission["Y"].values)
    except ValueError as exc:
        print(f"Unable to compute ROC AUC: {exc}")
        return 0.0

    print(f"ROC AUC: {auc:.4f} (threshold: {THRESHOLD})")
    return 1.0 if auc >= THRESHOLD else 0.0
