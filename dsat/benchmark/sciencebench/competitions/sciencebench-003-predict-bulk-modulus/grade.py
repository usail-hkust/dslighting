"""Grading function for ScienceBench task 3 (predict bulk modulus)."""

import pandas as pd
from sklearn.metrics import root_mean_squared_error

from benchmarks.sciencebench.grade_helpers import InvalidSubmissionError


THRESHOLD = 24.0


def _round_numeric(df: pd.DataFrame, decimals: int = 4) -> pd.DataFrame:
    if df.empty:
        return df
    return df.round(decimals=decimals)


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    """Return the actual evaluation metric (RMSE; lower is better)."""

    submission = submission.copy()
    answers = answers.copy()

    # Ensure required columns exist
    required_cols = {"material_id", "K_VRH"}
    if not required_cols.issubset(submission.columns) or not required_cols.issubset(answers.columns):
        raise InvalidSubmissionError(
            f"Missing required columns {sorted(required_cols)}. "
            f"Submission columns: {list(submission.columns)}"
        )

    submission = submission["material_id"].to_frame().join(submission[["K_VRH"]])
    answers = answers["material_id"].to_frame().join(answers[["K_VRH"]])

    data_correctness = list(submission["material_id"]) == list(answers["material_id"])
    if not data_correctness:
        raise InvalidSubmissionError("material_id ordering mismatch between submission and answers")

    pred = _round_numeric(submission[["K_VRH"]])
    gold = _round_numeric(answers[["K_VRH"]])

    rmse = root_mean_squared_error(gold, pred)
    print(f"RMSE: {rmse}")
    print(f"Pass threshold ({THRESHOLD}): {rmse <= THRESHOLD}")

    return float(rmse)
