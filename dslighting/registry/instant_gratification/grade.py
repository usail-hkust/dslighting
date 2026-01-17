import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from mlebench.grade_helpers import InvalidSubmissionError


def prepare_for_metric(submission: pd.DataFrame, answers: pd.DataFrame):
    """Prepare submission and answers for AUC-ROC calculation."""
    if len(submission) != len(answers):
        raise InvalidSubmissionError(
            f"Submission length ({len(submission)}) != answers length ({len(answers)})"
        )

    if "id" not in submission.columns:
        raise InvalidSubmissionError("Submission must have an 'id' column")

    if "target" not in submission.columns:
        raise InvalidSubmissionError("Submission must have a 'target' column")

    # Sort by id
    submission = submission.sort_values("id").reset_index(drop=True)
    answers = answers.sort_values("id").reset_index(drop=True)

    # Check id alignment
    if not (submission["id"] == answers["id"]).all():
        raise InvalidSubmissionError("Submission and answers id mismatch")

    # Extract predictions and true values
    y_pred = submission["target"].values
    y_true = answers["target"].values

    # Validate predictions
    try:
        y_pred = y_pred.astype(float)
    except (ValueError, TypeError):
        raise InvalidSubmissionError("Predictions must be numeric")

    if np.any(np.isnan(y_pred)):
        raise InvalidSubmissionError("Predictions cannot contain NaN values")

    if np.any((y_pred < 0) | (y_pred > 1)):
        raise InvalidSubmissionError("Predictions must be probabilities between 0 and 1")

    return y_true, y_pred


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    """Calculate AUC-ROC score."""
    y_true, y_pred = prepare_for_metric(submission, answers)

    # AUC-ROC
    auc = roc_auc_score(y_true, y_pred)

    return auc
