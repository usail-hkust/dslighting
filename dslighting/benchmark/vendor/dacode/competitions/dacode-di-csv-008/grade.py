import pandas as pd
import math

IGNORE_ORDER = True
FLOAT_TOLERANCE = 1e-3


def normalize_col(name: str) -> str:
    return str(name).strip().lower()


def parse_cell(val) -> object:
    if pd.isna(val):
        return None
    text = str(val).strip()
    try:
        if text.endswith("%"):
            return float(text[:-1]) / 100.0
        return float(text)
    except ValueError:
        return text.lower()


def compare_cells(gold_val, pred_val) -> bool:
    gold = parse_cell(gold_val)
    pred = parse_cell(pred_val)

    if gold is None and pred is None:
        return True
    if gold is None or pred is None:
        return False

    if isinstance(gold, float) and isinstance(pred, float):
        if gold == 0.0:
            return abs(pred) < 1e-9
        return abs(gold - pred) / abs(gold) <= FLOAT_TOLERANCE

    return str(gold) == str(pred)


def grade(submission, answers) -> float:
    if isinstance(submission, str):
        submission = pd.read_csv(submission)
    if isinstance(answers, str):
        answers = pd.read_csv(answers)

    if len(submission) == 0 or len(answers) == 0:
        return 0.0

    submission.columns = [normalize_col(c) for c in submission.columns]
    answers.columns = [normalize_col(c) for c in answers.columns]

    if list(submission.columns) != list(answers.columns):
        return 0.0

    if len(submission) != len(answers):
        return 0.0

    if IGNORE_ORDER:
        sort_cols = list(answers.columns)
        try:
            submission = submission.sort_values(sort_cols).reset_index(drop=True)
            answers = answers.sort_values(sort_cols).reset_index(drop=True)
        except Exception:
            pass

    for col in answers.columns:
        for sub_val, ans_val in zip(submission[col], answers[col]):
            if not compare_cells(ans_val, sub_val):
                return 0.0

    return 1.0
