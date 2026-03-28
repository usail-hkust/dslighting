"""Grader for ScienceBench task 87 (polynomial fit)."""

from __future__ import annotations

import csv

from pathlib import Path

from dslighting.benchmark.grading.models import GradingRequest

PRED_FILENAME = "polynomial_fit_pred.csv"
GOLD_FILENAME = "answer.csv"


def _load_sorted_csv(path: Path) -> tuple[list[str], list[list[str]]]:
    if not path.exists():
        raise FileNotFoundError(f"Required file missing: {path}")
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        headers = next(reader)
        rows = sorted(reader)
    return headers, rows


def grade(request: GradingRequest) -> float:
    submission_path = request.submission.root
    if submission_path.is_file():
        pred_path = submission_path
    else:
        pred_path = submission_path / PRED_FILENAME
    gold_path = request.references.private_dir / GOLD_FILENAME

    pred_headers, pred_rows = _load_sorted_csv(pred_path)
    gold_headers, gold_rows = _load_sorted_csv(gold_path)

    if pred_headers != gold_headers:
        print("Header mismatch between prediction and gold.")
        return 0.0
    if pred_rows != gold_rows:
        print("Row contents differ from the gold reference.")
        return 0.0
    return 1.0
