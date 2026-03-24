from __future__ import annotations

import math

import pandas as pd

from dslighting.benchmark.grading.helpers import (
    read_reference_child_csv,
    read_submission_child_csv,
    require_submission_dir,
)

IGNORE_ORDER = True
CONDITION_COLS = [1, 2, 3, 4]
MATRIX_FILES = (
    "sample_covariance_matrix.csv",
    "efficient_covariance_matrix.csv",
)


def _score_matrix(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    tol = 1e-2

    def norm(value):
        if pd.isna(value):
            return "__NA__"
        if isinstance(value, float):
            return round(value / tol) * tol
        if isinstance(value, str):
            return value.lower().strip()
        return value

    def vec_hash(column, do_sort):
        values = [norm(item) for item in column]
        return tuple(sorted(values, key=str) if do_sort else values)

    def match(gold_col, pred_col):
        if len(gold_col) != len(pred_col):
            return False
        if IGNORE_ORDER:
            gold_col = sorted(gold_col, key=lambda item: str(item))
            pred_col = sorted(pred_col, key=lambda item: str(item))
        for gold_value, pred_value in zip(gold_col, pred_col):
            if pd.isna(gold_value) and pd.isna(pred_value):
                continue
            if isinstance(gold_value, (int, float)) and isinstance(pred_value, (int, float)):
                if not math.isclose(float(gold_value), float(pred_value), abs_tol=tol):
                    return False
            elif isinstance(gold_value, str) and isinstance(pred_value, str):
                if gold_value.lower().strip() != pred_value.lower().strip():
                    return False
            elif gold_value != pred_value:
                return False
        return True

    gold = answers.iloc[:, CONDITION_COLS] if CONDITION_COLS else answers
    transposed_gold = gold.transpose().values.tolist()
    transposed_pred = submission.transpose().values.tolist()
    pred_hashes = {vec_hash(column, IGNORE_ORDER): True for column in transposed_pred}

    matches = 0
    for gold_column in transposed_gold:
        hashed = vec_hash(gold_column, IGNORE_ORDER)
        if hashed in pred_hashes or any(match(gold_column, pred_column) for pred_column in transposed_pred):
            matches += 1
    return matches / len(transposed_gold) if transposed_gold else 0.0


def grade(request) -> float:
    require_submission_dir(request)
    scores: list[float] = []
    for filename in MATRIX_FILES:
        submission = read_submission_child_csv(request, filename)
        answers = read_reference_child_csv(request, filename)
        scores.append(_score_matrix(submission, answers))
    return sum(scores) / len(scores) if scores else 0.0
