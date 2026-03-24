from __future__ import annotations

import pandas as pd

from dslighting.benchmark.grading.helpers import read_reference_child_csv, read_submission_child_csv, require_submission_dir
from dslighting.benchmark.grading.models import GradingRequest

IGNORE_ORDER = False
FLOAT_TOLERANCE = 0
FILES = ("allEvents.csv", "allGames.csv")


def normalize_col(name: str) -> str:
    return str(name).strip().lower()


def parse_cell(val):
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


def compare_frame(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    if len(submission) == 0 or len(answers) == 0:
        return 0.0

    submission = submission.copy()
    answers = answers.copy()
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


def grade(request: GradingRequest) -> float:
    require_submission_dir(request)
    scores = []
    for name in FILES:
        submission = read_submission_child_csv(request, name)
        answers = read_reference_child_csv(request, name)
        scores.append(compare_frame(submission, answers))
    return sum(scores) / len(scores) if scores else 0.0
