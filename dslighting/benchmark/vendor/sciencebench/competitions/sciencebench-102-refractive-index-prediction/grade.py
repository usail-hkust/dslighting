"""Grader for ScienceBench task 102 (refractive index prediction)."""

from __future__ import annotations

import pandas as pd

from dslighting.benchmark.grading.models import GradingRequest

PRED_FILENAME = "ref_index_predictions_pred.csv"
GOLD_FILENAME = "answer.csv"
TARGET_COLUMN = "refractive_index"
THRESHOLD = 0.78


def grade(request: GradingRequest) -> float:
    submission_path = request.submission.root
    if submission_path.is_file():
        pred_path = submission_path
    else:
        pred_path = submission_path / PRED_FILENAME
    gold_path = request.references.answers_path or (request.references.private_dir / GOLD_FILENAME)

    if not pred_path.exists():
        print(f"Prediction file not found: {pred_path}")
        return 0.0

    pred_df = pd.read_csv(pred_path)
    gold_df = pd.read_csv(gold_path)

    if TARGET_COLUMN not in pred_df.columns:
        print(f"Missing '{TARGET_COLUMN}' column in prediction.")
        return 0.0

    merged = gold_df[[TARGET_COLUMN]].join(pred_df[[TARGET_COLUMN]], how="inner", rsuffix="_pred")
    if merged.empty:
        print("No overlapping rows between prediction and gold.")
        return 0.0

    mae = (merged[TARGET_COLUMN] - merged[f"{TARGET_COLUMN}_pred"]).abs().mean()
    print(f"MAE: {mae}")
    return 1.0 if mae < THRESHOLD else 0.0
