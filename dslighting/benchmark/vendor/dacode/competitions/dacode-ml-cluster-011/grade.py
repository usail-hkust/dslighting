from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.metrics import adjusted_rand_score


CLUSTER_CANDIDATES = ("cluster", "clusters")


def _load_csv(obj):
    if isinstance(obj, pd.DataFrame):
        return obj.copy()
    return pd.read_csv(Path(obj))


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(col).strip().lower() for col in df.columns]
    return df


def _cluster_col(columns: list[str]) -> str | None:
    for col in columns:
        if col in CLUSTER_CANDIDATES:
            return col
    for col in columns:
        if 'cluster' in col:
            return col
    return None


def grade(submission, answers) -> float:
    try:
        submission_df = _normalize_columns(_load_csv(submission))
        answers_df = _normalize_columns(_load_csv(answers))
    except Exception:
        return 0.0

    if set(submission_df.columns) != set(answers_df.columns) or len(submission_df) != len(answers_df):
        return 0.0

    cluster_col = _cluster_col(list(answers_df.columns))
    if cluster_col is None:
        return 0.0

    feature_cols = [col for col in answers_df.columns if col != cluster_col]
    if feature_cols:
        try:
            submission_df = submission_df.sort_values(feature_cols).reset_index(drop=True)
            answers_df = answers_df.sort_values(feature_cols).reset_index(drop=True)
        except Exception:
            pass
        if not submission_df[feature_cols].equals(answers_df[feature_cols]):
            return 0.0

    try:
        score = adjusted_rand_score(answers_df[cluster_col], submission_df[cluster_col])
    except Exception:
        return 0.0
    return float(max(0.0, score))
