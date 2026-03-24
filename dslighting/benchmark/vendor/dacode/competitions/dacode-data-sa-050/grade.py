from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from dslighting.benchmark.grading.models import GradingRequest

IGNORE_ORDER = False
FLOAT_TOLERANCE = 1e-2


def _load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _sort_key(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _compare_values(gold: Any, pred: Any) -> bool:
    if gold is None and pred is None:
        return True

    if isinstance(gold, dict) and isinstance(pred, dict):
        if set(gold.keys()) != set(pred.keys()):
            return False
        return all(_compare_values(gold[key], pred[key]) for key in gold)

    if isinstance(gold, list) and isinstance(pred, list):
        if len(gold) != len(pred):
            return False
        gold_items = list(gold)
        pred_items = list(pred)
        if IGNORE_ORDER:
            gold_items = sorted(gold_items, key=_sort_key)
            pred_items = sorted(pred_items, key=_sort_key)
        return all(_compare_values(g_item, p_item) for g_item, p_item in zip(gold_items, pred_items))

    if isinstance(gold, (int, float)) and isinstance(pred, (int, float)):
        return math.isclose(float(gold), float(pred), abs_tol=FLOAT_TOLERANCE)

    return str(gold).lower().strip() == str(pred).lower().strip()


def grade(request: GradingRequest) -> float:
    submission_path = request.submission.root
    answers_path = request.references.answers_path
    if answers_path is None or not submission_path.exists():
        return 0.0

    submission = _load_json(submission_path)
    answers = _load_json(answers_path)
    if submission is None or answers is None:
        return 0.0
    return 1.0 if _compare_values(answers, submission) else 0.0
