from __future__ import annotations

import re

import pandas as pd

TASK_NAME = 'mosci-terra-14'
FAMILY = 'terra'
LOCAL_TASK_ID = 14
GLOBAL_TASK_ID = 88
JUDGE_TYPE = '>'
TOLERANCE = 0.10


def _extract_row(df: pd.DataFrame) -> pd.Series:
    if df is None or df.empty:
        raise ValueError('Submission or answer dataframe is empty')
    if 'id' in df.columns:
        matched = df[df['id'].astype(str) == str(GLOBAL_TASK_ID)]
        if not matched.empty:
            return matched.iloc[0]
    return df.iloc[0]


def _unwrap_answer(value: object) -> str:
    text = '' if value is None else str(value).strip()
    if text.startswith('@answer[') and text.endswith(']'):
        text = text[len('@answer['):-1].strip()
    if text.lower().startswith('answer:'):
        text = text.split(':', 1)[1].strip()
    return text.strip().strip('"').strip("'")


def _normalized_text(text: str) -> str:
    return ' '.join(str(text).strip().lower().split())


def _to_bool(text: str):
    lowered = _normalized_text(text)
    if re.search(r'\btrue\b', lowered) and not re.search(r'\bfalse\b', lowered):
        return True
    if re.search(r'\bfalse\b', lowered) and not re.search(r'\btrue\b', lowered):
        return False
    if lowered in {'1', 'yes', 'on'}:
        return True
    if lowered in {'0', 'no', 'off'}:
        return False
    return None


def _extract_float(text: str):
    matches = re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', text)
    if not matches:
        return None
    try:
        return float(matches[-1])
    except ValueError:
        return None


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    try:
        submission_row = _extract_row(submission)
        answer_row = _extract_row(answers)
        pred = _unwrap_answer(submission_row['answer'])
        gold = _unwrap_answer(answer_row['answer'])

        gold_bool = _to_bool(gold)
        if gold_bool is not None:
            pred_bool = _to_bool(pred)
            return 1.0 if pred_bool is not None and pred_bool == gold_bool else 0.0

        gold_num = _extract_float(gold)
        if gold_num is not None:
            pred_num = _extract_float(pred)
            if pred_num is None:
                return 0.0
            if JUDGE_TYPE == '=':
                tol = abs(gold_num) * TOLERANCE if gold_num != 0 else TOLERANCE
                return 1.0 if abs(pred_num - gold_num) <= tol else 0.0
            if JUDGE_TYPE == '>':
                return 1.0 if pred_num > gold_num else 0.0
            if JUDGE_TYPE == '>=':
                return 1.0 if pred_num >= gold_num else 0.0
            if JUDGE_TYPE == '<':
                return 1.0 if pred_num < gold_num else 0.0
            if JUDGE_TYPE == '<=':
                return 1.0 if pred_num <= gold_num else 0.0

        norm_pred = _normalized_text(pred)
        norm_gold = _normalized_text(gold)
        if norm_pred == norm_gold:
            return 1.0
        if norm_gold and norm_gold in norm_pred:
            return 1.0
        return 0.0
    except Exception as exc:
        print(f'Grading error in {TASK_NAME}: {exc}')
        return 0.0
