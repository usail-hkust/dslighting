import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from mlebench.grade_helpers import InvalidSubmissionError


def prepare_for_metric(submission: pd.DataFrame, answers: pd.DataFrame):
    """Prepare submission and answers for Macro F1 calculation."""
    if len(submission) != len(answers):
        raise InvalidSubmissionError(
            f"Submission length ({len(submission)}) != answers length ({len(answers)})"
        )

    if "time" not in submission.columns:
        raise InvalidSubmissionError("Submission must have a 'time' column")

    if "open_channels" not in submission.columns:
        raise InvalidSubmissionError("Submission must have an 'open_channels' column")

    # Sort by time
    submission = submission.sort_values("time").reset_index(drop=True)
    answers = answers.sort_values("time").reset_index(drop=True)

    # Check time alignment
    if not np.allclose(submission["time"].values, answers["time"].values, atol=1e-4):
        raise InvalidSubmissionError("Submission and answers time mismatch")

    # Extract predictions and true values
    y_pred = submission["open_channels"].values
    y_true = answers["open_channels"].values

    # Validate predictions
    try:
        y_pred = y_pred.astype(int)
    except (ValueError, TypeError):
        raise InvalidSubmissionError("Predictions must be integers")

    if np.any(np.isnan(y_pred)):
        raise InvalidSubmissionError("Predictions cannot contain NaN values")

    return y_true, y_pred


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    """Calculate Macro F1 score."""
    y_true, y_pred = prepare_for_metric(submission, answers)

    # Macro F1: compute F1 for each class and average
    macro_f1 = f1_score(y_true, y_pred, average='macro')

    return macro_f1
