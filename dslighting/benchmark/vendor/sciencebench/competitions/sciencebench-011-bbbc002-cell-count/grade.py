"""Grading function for ScienceBench task 11."""

from __future__ import annotations

from typing import Tuple
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error

from dslighting.benchmark.grading.models import GradingRequest

MAE_THRESHOLD = 30.0


def _extract_vectors(submission: pd.DataFrame, answers: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """Align submission with answers and return numeric vectors."""
    if "id" in submission.columns and "id" in answers.columns:
        merged = pd.merge(answers, submission, on="id", suffixes=("_true", "_pred"))
        pred_col = next((c for c in merged.columns if c.endswith("_pred")), None)
        if pred_col is None:
            raise ValueError("Could not locate prediction column in merged submission.")
        true_col = pred_col.replace("_pred", "_true")
        preds = merged[pred_col].to_numpy()
        labels = merged[true_col].to_numpy()
    else:
        pred_col = "count" if "count" in submission.columns else submission.columns[0]
        true_col = "count" if "count" in answers.columns else answers.columns[0]

        if len(submission) != len(answers):
            raise ValueError(
                f"Submission length ({len(submission)}) does not match answers length ({len(answers)})."
            )
        preds = submission[pred_col].to_numpy()
        labels = answers[true_col].to_numpy()

    return preds.astype(float), labels.astype(float)


def grade(request: GradingRequest) -> float:
    """
    Grade submission using mean absolute error with a pass/fail threshold.

    Returns:
        1.0 if MAE <= threshold else 0.0
    """
    submission_path = request.submission.root
    answers_path = request.references.private_dir / "answer.csv"

    submission = pd.read_csv(submission_path)
    answers = pd.read_csv(answers_path)

    preds, labels = _extract_vectors(submission, answers)
    mae = mean_absolute_error(labels, preds)
    return float(mae <= MAE_THRESHOLD)
