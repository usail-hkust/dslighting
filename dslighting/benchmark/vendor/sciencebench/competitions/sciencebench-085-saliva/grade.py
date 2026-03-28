"""Grading function for ScienceBench Task 85 (BiopSyKit saliva analysis)."""

from __future__ import annotations

import json
import math

from pathlib import Path

from dslighting.benchmark.grading.models import GradingRequest

PRED_FILENAME = "saliva_pred.json"
GOLD_FILENAME = "answer.json"


def _values_close(gold_value, pred_value) -> bool:
    if isinstance(gold_value, float):
        try:
            return math.isclose(gold_value, float(pred_value), rel_tol=1e-9, abs_tol=1e-9)
        except (TypeError, ValueError):
            return False
    return gold_value == pred_value


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

    if not gold_path.exists():
        print(f"Gold file not found: {gold_path}")
        return 0.0
    gold = json.loads(gold_path.read_text())

    if set(gold.keys()) != set(pred.keys()):
        print("Subject keys do not match.")
        return 0.0

    for subject, gold_entry in gold.items():
        pred_entry = pred.get(subject)
        if set(gold_entry.keys()) != set(pred_entry.keys()):
            print(f"Field mismatch for subject {subject}.")
            return 0.0
        for key, gold_value in gold_entry.items():
            if not _values_close(gold_value, pred_entry.get(key)):
                print(f"Mismatch for subject {subject}, field '{key}'.")
                return 0.0

    return 1.0
