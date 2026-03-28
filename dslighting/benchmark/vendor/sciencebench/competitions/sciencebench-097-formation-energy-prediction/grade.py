"""Grader for ScienceBench task 97 (formation energy prediction)."""

from __future__ import annotations

import numpy as np

from dslighting.benchmark.grading.models import GradingRequest

PRED_FILENAME = "formation_energy_prediction_pred.txt"
GOLD_FILENAME = "answer.txt"
THRESHOLD = 0.1


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

    pred = np.loadtxt(pred_path)
    gold = np.loadtxt(gold_path)

    if pred.shape != gold.shape:
        print(f"Shape mismatch: {pred.shape} vs {gold.shape}")
        return 0.0

    mse = float(np.mean((pred - gold) ** 2))
    print(f"MSE: {mse}")
    return 1.0 if mse <= THRESHOLD else 0.0
