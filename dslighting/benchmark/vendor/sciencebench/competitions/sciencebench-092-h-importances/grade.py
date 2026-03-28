"""Grader for ScienceBench task 92 (JNMF H importances)."""

from __future__ import annotations

import json

from pathlib import Path

from dslighting.benchmark.grading.models import GradingRequest

PRED_FILENAME = "jnmf_h_importances.json"
GOLD_FILENAME = "answer.json"
TOLERANCE = 1e-4


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= TOLERANCE


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

    with open(pred_path, "r", encoding="utf-8") as f:
        pred = json.load(f)

    with open(gold_path, "r", encoding="utf-8") as f:
        gold = json.load(f)

    if set(gold.keys()) != set(pred.keys()):
        print("Key mismatch between prediction and gold JSON.")
        return 0.0

    for key, gold_value in gold.items():
        pred_value = pred[key]
        if not _close(gold_value, pred_value):
            print(f"Value mismatch for '{key}': gold={gold_value}, pred={pred_value}")
            return 0.0

    return 1.0
