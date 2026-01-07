"""
Grading function for ScienceBench task 5 (DKPES model development).

Mirrors the original ScienceAgentBench evaluation:
1. Verify the `index` column matches between submission and gold labels.
2. Compute ROC-AUC on `Signal-inhibition` (higher is better).
"""

import pandas as pd
from sklearn.metrics import roc_auc_score

from benchmarks.sciencebench.grade_helpers import InvalidSubmissionError

EXPECTED_COLUMNS = {"index", "Signal-inhibition"}


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    if not EXPECTED_COLUMNS.issubset(submission.columns):
        raise InvalidSubmissionError(f"Submission must contain columns: {EXPECTED_COLUMNS}")
    if not EXPECTED_COLUMNS.issubset(answers.columns):
        raise InvalidSubmissionError(f"Answers must contain columns: {EXPECTED_COLUMNS}")

    submission = submission.reset_index(drop=True)
    answers = answers.reset_index(drop=True)

    if list(submission["index"]) != list(answers["index"]):
        print("Index mismatch between submission and gold.")
        raise InvalidSubmissionError("Index mismatch between submission and gold.")

    try:
        auc = roc_auc_score(
            answers["Signal-inhibition"].astype(float),
            submission["Signal-inhibition"].astype(float),
        )
    except ValueError as exc:
        print(f"Failed to compute ROC-AUC: {exc}")
        raise InvalidSubmissionError(f"Failed to compute ROC-AUC: {exc}") from exc

    print(f"ROC-AUC: {auc}")
    return float(auc)
