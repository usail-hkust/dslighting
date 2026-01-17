import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error

from mlebench.grade_helpers import InvalidSubmissionError


TARGET_COLUMNS = ['cohesion', 'syntax', 'vocabulary', 'phraseology', 'grammar', 'conventions']


def prepare_for_metric(submission: pd.DataFrame, answers: pd.DataFrame):
    """Prepare submission and answers for MCRMSE calculation."""
    if len(submission) != len(answers):
        raise InvalidSubmissionError(
            f"Submission length ({len(submission)}) != answers length ({len(answers)})"
        )

    if "text_id" not in submission.columns:
        raise InvalidSubmissionError("Submission must have a 'text_id' column")

    for col in TARGET_COLUMNS:
        if col not in submission.columns:
            raise InvalidSubmissionError(f"Submission must have a '{col}' column")

    # Sort by text_id
    submission = submission.sort_values("text_id").reset_index(drop=True)
    answers = answers.sort_values("text_id").reset_index(drop=True)

    # Check text_id alignment
    if not (submission["text_id"] == answers["text_id"]).all():
        raise InvalidSubmissionError("Submission and answers text_id mismatch")

    # Validate predictions
    for col in TARGET_COLUMNS:
        try:
            submission[col] = submission[col].astype(float)
        except (ValueError, TypeError):
            raise InvalidSubmissionError(f"'{col}' predictions must be numeric")

        if submission[col].isnull().any():
            raise InvalidSubmissionError(f"'{col}' predictions cannot contain NaN values")

    return submission, answers


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    """
    Calculate MCRMSE (Mean Columnwise Root Mean Squared Error).

    MCRMSE = mean of RMSE across all target columns
    """
    submission, answers = prepare_for_metric(submission, answers)

    rmse_scores = []
    for col in TARGET_COLUMNS:
        rmse = np.sqrt(mean_squared_error(answers[col], submission[col]))
        rmse_scores.append(rmse)

    mcrmse = np.mean(rmse_scores)
    return mcrmse
