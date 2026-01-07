import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_log_error

from mlebench.grade_helpers import InvalidSubmissionError


TARGET_COLUMNS = ['num_views', 'num_votes', 'num_comments']


def prepare_for_metric(submission: pd.DataFrame, answers: pd.DataFrame):
    """Prepare submission and answers for RMSLE calculation."""
    if len(submission) != len(answers):
        raise InvalidSubmissionError(
            f"Submission length ({len(submission)}) != answers length ({len(answers)})"
        )

    if "id" not in submission.columns:
        raise InvalidSubmissionError("Submission must have an 'id' column")

    for col in TARGET_COLUMNS:
        if col not in submission.columns:
            raise InvalidSubmissionError(f"Submission must have a '{col}' column")

    # Sort by id
    submission = submission.sort_values("id").reset_index(drop=True)
    answers = answers.sort_values("id").reset_index(drop=True)

    # Check id alignment
    if not (submission["id"] == answers["id"]).all():
        raise InvalidSubmissionError("Submission and answers id mismatch")

    # Validate predictions
    for col in TARGET_COLUMNS:
        try:
            submission[col] = submission[col].astype(float)
        except (ValueError, TypeError):
            raise InvalidSubmissionError(f"'{col}' predictions must be numeric")

        if submission[col].isnull().any():
            raise InvalidSubmissionError(f"'{col}' predictions cannot contain NaN values")

        if (submission[col] < 0).any():
            raise InvalidSubmissionError(f"'{col}' predictions cannot be negative")

    return submission, answers


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    """Calculate RMSLE score across all target columns."""
    submission, answers = prepare_for_metric(submission, answers)

    # Concatenate all predictions and true values
    all_pred = []
    all_true = []
    for col in TARGET_COLUMNS:
        all_pred.extend(submission[col].values)
        all_true.extend(answers[col].values)

    all_pred = np.array(all_pred)
    all_true = np.array(all_true)

    # RMSLE
    rmsle = np.sqrt(mean_squared_log_error(all_true, all_pred))

    return rmsle
