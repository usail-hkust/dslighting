"""Grading function for ScienceBench task 51 (brain-blood-qsar)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.metrics import balanced_accuracy_score

from dslighting.benchmark.grading.models import GradingRequest

THRESHOLD = 0.70
PRED_FILENAME = "brain_blood_qsar.csv"


def grade(request: GradingRequest) -> float:
    submission_path = request.submission.root
    if submission_path.is_file():
        pred_path = submission_path
    else:
        pred_path = submission_path / PRED_FILENAME
    answers_path = request.references.private_dir / "answer.csv"

    if not pred_path.exists():
        print(f"Submission file not found: {pred_path}")
        return 0.0

    submission_df = pd.read_csv(pred_path)
    answers_df = pd.read_csv(answers_path)

    if "label" not in submission_df.columns:
        raise ValueError("Submission must contain 'label' column")
    if "label" not in answers_df.columns:
        raise ValueError("Answers must contain 'label' column")

    pred_labels = submission_df["label"]
    gold_labels = answers_df["label"]

    if len(pred_labels) != len(gold_labels):
        print(f"Row count mismatch: {len(pred_labels)} vs {len(gold_labels)}")
        return 0.0

    score = balanced_accuracy_score(gold_labels, pred_labels)
    print(f"Balanced accuracy: {score}")
    return 1.0 if score >= THRESHOLD else 0.0
