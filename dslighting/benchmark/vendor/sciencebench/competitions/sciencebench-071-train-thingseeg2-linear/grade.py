"""Grading function for ScienceBench Task 71 (ThingseEG2 linear mapping)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from dslighting.benchmark.grading.models import GradingRequest

THRESHOLD = 0.6
PRED_FILENAME = "linear_sub01tosub03_pred.npy"


def grade(request: GradingRequest) -> float:
    submission_path = request.submission.root
    if submission_path.is_file():
        pred_path = submission_path
    else:
        pred_path = submission_path / PRED_FILENAME

    if not pred_path.exists():
        print(f"Submission file not found: {pred_path}")
        return 0.0

    pred = np.load(pred_path)

    gold_path = request.references.answers_path or (request.references.private_dir / "answer.npy")
    if not gold_path.exists():
        print(f"Gold file not found: {gold_path}")
        return 0.0

    gold = np.load(gold_path)

    if pred.shape != gold.shape:
        print(f"Shape mismatch: submission {pred.shape} vs gold {gold.shape}")
        return 0.0

    corr = spearmanr(pred.flatten(), gold.flatten())[0]
    print(f"Spearman correlation: {corr}")
    return 1.0 if corr >= THRESHOLD else 0.0
