"""Grading function for ScienceBench Task 19 (DILI SVM models)."""

from __future__ import annotations

import pandas as pd
from sklearn.metrics import f1_score

from dslighting.benchmark.grading.models import GradingRequest

REQUIRED_COLUMNS = {"standardised_smiles", "label"}
THRESHOLD = 0.73


def grade(request: GradingRequest) -> float:
    """Return 1.0 if F1 >= 0.73 and SMILES ordering matches."""
    submission_path = request.submission.root
    answers_path = request.references.private_dir / "answer.csv"

    submission = pd.read_csv(submission_path)
    answers = pd.read_csv(answers_path)

    if submission.empty:
        print("Submission is empty.")
        return 0.0
    if answers.empty:
        print("Answer data is empty.")
        return 0.0

    if not REQUIRED_COLUMNS.issubset(submission.columns):
        print(f"Submission missing columns: {REQUIRED_COLUMNS - set(submission.columns)}")
        return 0.0
    if not REQUIRED_COLUMNS.issubset(answers.columns):
        print("Answers missing required columns.")
        return 0.0

    if list(submission["standardised_smiles"]) != list(answers["standardised_smiles"]):
        print("SMILES ordering mismatch.")
        return 0.0

    gold_binary = (answers["label"].astype(str).str.upper() == "DILI").astype(int)
    pred_binary = (submission["label"].astype(str).str.upper() == "DILI").astype(int)

    f1 = f1_score(gold_binary, pred_binary, average="binary")
    print(f"F1 score: {f1:.4f} (threshold: {THRESHOLD})")
    return 1.0 if f1 >= THRESHOLD else 0.0
