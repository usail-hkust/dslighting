"""Grading function for ScienceBench task 3 (predict bulk modulus)."""

from pathlib import Path

import pandas as pd
from sklearn.metrics import root_mean_squared_error

from dslighting.benchmark.grading.models import GradingRequest


THRESHOLD = 24.0


def _round_numeric(df: pd.DataFrame, decimals: int = 4) -> pd.DataFrame:
    if df.empty:
        return df
    return df.round(decimals=decimals)


def grade(request: GradingRequest) -> float:
    """Match the original evaluation: data correctness + RMSE threshold."""
    submission_path = request.submission.root
    answers_path = request.references.private_dir / "answer.csv"

    submission = pd.read_csv(submission_path)
    answers = pd.read_csv(answers_path)

    submission = submission.copy()
    answers = answers.copy()

    # Ensure required columns exist
    required_cols = {"material_id", "K_VRH"}
    if not required_cols.issubset(submission.columns) or not required_cols.issubset(answers.columns):
        print(f"Missing required columns. Submission columns: {submission.columns}")
        return 0.0

    submission = submission["material_id"].to_frame().join(submission[["K_VRH"]])
    answers = answers["material_id"].to_frame().join(answers[["K_VRH"]])

    data_correctness = list(submission["material_id"]) == list(answers["material_id"])
    if not data_correctness:
        print("material_id ordering mismatch between submission and answers")
        return 0.0

    pred = _round_numeric(submission[["K_VRH"]])
    gold = _round_numeric(answers[["K_VRH"]])

    rmse = root_mean_squared_error(gold, pred)
    print(f"RMSE: {rmse}")

    if rmse <= THRESHOLD:
        return 1.0
    return 0.0
