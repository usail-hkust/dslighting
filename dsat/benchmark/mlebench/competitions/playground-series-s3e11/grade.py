import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_log_error

from mlebench.grade_helpers import InvalidSubmissionError


def prepare_for_metric(submission: pd.DataFrame, answers: pd.DataFrame):
    """Prepare submission and answers for RMSLE calculation."""
    if len(submission) != len(answers):
        raise InvalidSubmissionError(
            f"Submission length ({len(submission)}) != answers length ({len(answers)})"
        )

    if "id" not in submission.columns:
        raise InvalidSubmissionError("Submission must have an 'id' column")

    if "cost" not in submission.columns:
        raise InvalidSubmissionError("Submission must have a 'cost' column")

    # Sort by id
    submission = submission.sort_values("id").reset_index(drop=True)
    answers = answers.sort_values("id").reset_index(drop=True)

    # Check id alignment
    if not (submission["id"] == answers["id"]).all():
        raise InvalidSubmissionError("Submission and answers id mismatch")

    # Extract predictions and true values
    y_pred = submission["cost"].values
    y_true = answers["cost"].values

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
    """Calculate RMSLE score."""
    y_true, y_pred = prepare_for_metric(submission, answers)

    # RMSLE
    rmsle = np.sqrt(mean_squared_log_error(y_true, y_pred))

    return rmsle
