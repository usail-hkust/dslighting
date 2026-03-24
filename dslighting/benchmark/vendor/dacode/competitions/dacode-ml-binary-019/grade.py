from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

IGNORE_ORDER = False
ID_KEYWORDS = ("id", "passengerid", "essay_id", "row_id", "building_id", "id_lat_lon_year_week")


def _load_csv(obj):
    if isinstance(obj, pd.DataFrame):
        return obj.copy()
    path = Path(obj)
    return pd.read_csv(path)


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(col).strip().lower() for col in df.columns]
    return df


def _id_columns(columns: list[str]) -> list[str]:
    return [col for col in columns if col in ID_KEYWORDS or col.endswith('_id') or col == 'id']


def _align_frames(submission: pd.DataFrame, answers: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame] | tuple[None, None]:
    submission = _normalize_columns(submission)
    answers = _normalize_columns(answers)

    if set(submission.columns) != set(answers.columns):
        return None, None

    answers = answers[sorted(answers.columns)]
    submission = submission[sorted(submission.columns)]

    id_cols = _id_columns(list(answers.columns))
    if id_cols:
        try:
            answers = answers.sort_values(id_cols).reset_index(drop=True)
            submission = submission.sort_values(id_cols).reset_index(drop=True)
        except Exception:
            pass

    if len(submission) != len(answers):
        return None, None
    return submission.reset_index(drop=True), answers.reset_index(drop=True)


def _series_is_integral(values: pd.Series) -> bool:
    numeric = pd.to_numeric(values, errors='coerce').dropna()
    if numeric.empty:
        return False
    return bool(np.all(np.isclose(numeric, np.round(numeric))))


def _classification_score(pred: pd.Series, gold: pd.Series) -> float:
    pred_norm = pred.fillna('__NA__').astype(str).str.strip().str.lower()
    gold_norm = gold.fillna('__NA__').astype(str).str.strip().str.lower()
    return float((pred_norm == gold_norm).mean())


def _regression_score(pred: pd.Series, gold: pd.Series) -> float:
    pred_num = pd.to_numeric(pred, errors='coerce')
    gold_num = pd.to_numeric(gold, errors='coerce')
    valid = ~(pred_num.isna() | gold_num.isna())
    if not valid.any():
        return 0.0
    pred_num = pred_num[valid]
    gold_num = gold_num[valid]
    mae = float(np.mean(np.abs(pred_num - gold_num)))
    scale = float(np.mean(np.abs(gold_num)))
    if not np.isfinite(scale) or scale <= 1e-12:
        scale = 1.0
    return float(1.0 / (1.0 + (mae / scale)))


def grade(submission, answers) -> float:
    try:
        submission_df = _load_csv(submission)
        answers_df = _load_csv(answers)
    except Exception:
        return 0.0

    submission_df, answers_df = _align_frames(submission_df, answers_df)
    if submission_df is None or answers_df is None:
        return 0.0

    id_cols = set(_id_columns(list(answers_df.columns)))
    target_cols = [col for col in answers_df.columns if col not in id_cols]
    if not target_cols:
        return 0.0

    scores = []
    for col in target_cols:
        gold = answers_df[col]
        pred = submission_df[col]
        gold_num = pd.to_numeric(gold, errors='coerce')
        pred_num = pd.to_numeric(pred, errors='coerce')
        numeric_ratio = float(gold_num.notna().mean())
        unique_count = int(gold_num.dropna().nunique()) if numeric_ratio > 0.95 else 0
        is_integral = _series_is_integral(gold) if numeric_ratio > 0.95 else False
        if numeric_ratio > 0.95 and not (is_integral and unique_count <= 20):
            scores.append(_regression_score(pred, gold))
        else:
            scores.append(_classification_score(pred, gold))

    return float(np.mean(scores)) if scores else 0.0
