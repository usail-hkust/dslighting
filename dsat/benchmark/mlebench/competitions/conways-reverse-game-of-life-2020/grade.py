import numpy as np
import pandas as pd

from mlebench.grade_helpers import InvalidSubmissionError


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    """Return accuracy between predicted and true starting boards."""
    if "id" not in submission.columns:
        raise InvalidSubmissionError("Submission is missing required column 'id'.")

    start_cols = [col for col in answers.columns if col.startswith("start_")]
    if not start_cols:
        raise ValueError("Answers DataFrame does not contain any start_* columns.")

    missing_cols = [col for col in start_cols if col not in submission.columns]
    if missing_cols:
        raise InvalidSubmissionError(
            f"Submission is missing required start columns: {missing_cols[:5]}"
        )

    merged = answers[["id", *start_cols]].merge(
        submission[["id", *start_cols]],
        on="id",
        how="left",
        suffixes=("_true", "_pred"),
    )

    pred_cols = [f"{col}_pred" for col in start_cols]
    if merged[pred_cols].isna().any().any():
        raise InvalidSubmissionError("Submission contains missing predictions for some ids.")

    preds = merged[pred_cols].to_numpy(dtype=float)
    truths = merged[[f"{col}_true" for col in start_cols]].to_numpy(dtype=float)

    if not np.isin(preds, [0, 1]).all():
        raise InvalidSubmissionError("Predictions must be binary (0 or 1).")

    mae = np.abs(preds - truths).mean()
    return float(1.0 - mae)
