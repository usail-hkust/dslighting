"""Grading function for ScienceBench task 78 (protein stability prediction)."""

from __future__ import annotations

import pandas as pd
from sklearn.metrics import mean_absolute_error

from dslighting.benchmark.grading.models import GradingRequest

THRESHOLD = 11.0
PRED_FILENAME = "pucci-proteins_test_pred.csv"


def grade(request: GradingRequest) -> float:
    submission_path = request.submission.root
    if submission_path.is_file():
        pred_path = submission_path
    else:
        pred_path = submission_path / PRED_FILENAME

    if not pred_path.exists():
        print(f"Submission file not found: {pred_path}")
        return 0.0

    gold_path = request.references.private_dir / "answer.csv"

    pred_df = pd.read_csv(pred_path)
    gold_df = pd.read_csv(gold_path)

    if "deltaTm" not in pred_df.columns or "deltaTm" not in gold_df.columns:
        raise ValueError("Both prediction and gold CSVs must contain a 'deltaTm' column.")

    if len(pred_df) != len(gold_df):
        print(f"Row count mismatch: submission {len(pred_df)} vs gold {len(gold_df)}")
        return 0.0

    metric = mean_absolute_error(gold_df["deltaTm"], pred_df["deltaTm"])
    print(f"Mean absolute error: {metric}")

    return 1.0 if metric <= THRESHOLD else 0.0
