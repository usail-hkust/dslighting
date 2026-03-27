"""
Grading function for ScienceBench task 1: clintox_nn
"""

import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score

from dslighting.benchmark.grading.models import GradingRequest


THRESHOLD = 0.77


def grade(request: GradingRequest) -> float:
    """
    Grade submission using ROC-AUC metric with threshold 0.77.

    Mirrors the original ScienceAgentBench evaluation:
    1. Verify SMILES ordering matches
    2. Compute ROC-AUC on FDA_APPROVED and CT_TOX columns
    3. Require metric >= 0.77
    """
    submission_path = request.submission.root
    answers_path = request.references.private_dir / "answer.csv"

    submission = pd.read_csv(submission_path)
    answers = pd.read_csv(answers_path)

    # Check data correctness (smiles ordering)
    data_correctness = list(submission["smiles"]) == list(answers["smiles"])
    if not data_correctness:
        print("SMILES ordering mismatch between submission and answers")
        return 0.0

    # Compute ROC-AUC
    try:
        metric = roc_auc_score(
            answers[["FDA_APPROVED", "CT_TOX"]],
            submission[["FDA_APPROVED", "CT_TOX"]]
        )
    except ValueError as exc:
        print(f"Failed to compute ROC-AUC: {exc}")
        return 0.0

    print(f"ROC-AUC: {metric:.4f} (threshold: {THRESHOLD})")

    return 1.0 if metric >= THRESHOLD else 0.0
