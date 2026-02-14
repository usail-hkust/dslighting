"""
Grading function for ScienceBench task 1
"""

import pandas as pd
from sklearn.metrics import roc_auc_score


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    """
    Grade submission using ROC-AUC (as configured in `config.yaml`).

    Args:
        submission: DataFrame with predictions
        answers: DataFrame with ground truth

    Returns:
        ROC-AUC score (higher is better)
    """
    if submission is None or answers is None:
        return None

    id_col = "smiles" if "smiles" in submission.columns and "smiles" in answers.columns else None

    # Align rows on identifier if available; otherwise assume same order.
    if id_col:
        merged = pd.merge(
            answers,
            submission,
            on=id_col,
            suffixes=("_true", "_pred"),
            how="inner",
        )
    else:
        merged = pd.concat(
            [answers.add_suffix("_true"), submission.add_suffix("_pred")],
            axis=1,
        )

    # Score all common target columns (exclude identifier column)
    target_cols = [c for c in answers.columns if c != id_col and c in submission.columns]
    if not target_cols:
        return None

    aucs: list[float] = []
    for col in target_cols:
        y_true = merged[f"{col}_true"]
        y_pred = merged[f"{col}_pred"]
        # ROC-AUC is undefined if only one class is present.
        if y_true.nunique(dropna=True) < 2:
            continue
        aucs.append(float(roc_auc_score(y_true, y_pred)))

    if not aucs:
        return None
    return float(sum(aucs) / len(aucs))
