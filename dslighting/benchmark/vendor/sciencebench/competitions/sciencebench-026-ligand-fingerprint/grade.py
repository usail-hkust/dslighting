"""Grading function for ScienceBench task 26 (ligand fingerprint)."""

from __future__ import annotations

import pandas as pd
from sklearn.metrics import accuracy_score

from dslighting.benchmark.grading.models import GradingRequest


def grade(request: GradingRequest) -> float:
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

    required_cols = {"names", "Y"}
    if not required_cols.issubset(submission.columns):
        print("Submission missing required columns.")
        return 0.0
    if not required_cols.issubset(answers.columns):
        print("Answers missing required columns.")
        return 0.0

    submission_sorted = submission.sort_values(by="names").reset_index(drop=True)
    answers_sorted = answers.sort_values(by="names").reset_index(drop=True)

    data_correctness = list(submission_sorted["names"]) == list(answers_sorted["names"])
    metric = accuracy_score(answers_sorted["Y"], submission_sorted["Y"])
    func_correctness = metric == 1.0

    if not data_correctness:
        print("Ligand fingerprint submission names do not match the gold reference.")
    if not func_correctness:
        print(f"Ligand fingerprint accuracy: {metric}")

    return float(data_correctness and func_correctness)
