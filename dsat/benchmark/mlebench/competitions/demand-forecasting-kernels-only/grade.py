import numpy as np
import pandas as pd

from mlebench.grade_helpers import InvalidSubmissionError


def smape(y_true, y_pred):
    """Calculate SMAPE (Symmetric Mean Absolute Percentage Error)."""
    # SMAPE = 0 when both actual and predicted are 0
    denominator = (np.abs(y_true) + np.abs(y_pred))
    diff = np.abs(y_true - y_pred)

    # Handle division by zero: set SMAPE to 0 when denominator is 0
    smape_val = np.where(denominator == 0, 0, diff / denominator)

    return 100 * np.mean(smape_val)


def prepare_for_metric(submission: pd.DataFrame, answers: pd.DataFrame):
    """Prepare submission and answers for SMAPE calculation."""
    if len(submission) != len(answers):
        raise InvalidSubmissionError(
            f"Submission length ({len(submission)}) != answers length ({len(answers)})"
        )

    if "id" not in submission.columns:
        raise InvalidSubmissionError("Submission must have an 'id' column")

    if "sales" not in submission.columns:
        raise InvalidSubmissionError("Submission must have a 'sales' column")

    # Sort by id
    submission = submission.sort_values("id").reset_index(drop=True)
    answers = answers.sort_values("id").reset_index(drop=True)

    # Check id alignment
    if not (submission["id"] == answers["id"]).all():
        raise InvalidSubmissionError("Submission and answers id mismatch")

    # Extract predictions and true values
    y_pred = submission["sales"].values
    y_true = answers["sales"].values

    # Validate predictions
    try:
        y_pred = y_pred.astype(float)
    except (ValueError, TypeError):
        raise InvalidSubmissionError("Predictions must be numeric")

    if np.any(np.isnan(y_pred)):
        raise InvalidSubmissionError("Predictions cannot contain NaN values")

    if np.any(y_pred < 0):
        raise InvalidSubmissionError("Predictions cannot be negative")

    return y_true, y_pred


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    """Calculate SMAPE score."""
    y_true, y_pred = prepare_for_metric(submission, answers)

    # SMAPE
    smape_score = smape(y_true, y_pred)

    return smape_score
