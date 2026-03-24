from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dslighting.benchmark.grading.models import GradingRequest

UNORDERED_PAIR_TASKS = {"dacode-di-text-029"}
UNORDERED_LIST_TASKS = {"dacode-di-text-035"}


def _task_id() -> str:
    return Path(__file__).resolve().parent.name


def _load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _sort_key(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _compare_numeric(gold: Any, pred: Any) -> bool:
    if gold == 0:
        return pred == 0
    return abs(float(gold) - float(pred)) / abs(float(gold)) < 1e-3


def _compare_values(gold: Any, pred: Any, *, unordered_lists: bool, unordered_pairs: bool) -> bool:
    if gold is None and pred is None:
        return True

    if isinstance(gold, dict) and isinstance(pred, dict):
        if set(gold.keys()) != set(pred.keys()):
            return False
        return all(
            _compare_values(gold[key], pred[key], unordered_lists=unordered_lists, unordered_pairs=unordered_pairs)
            for key in gold
        )

    if isinstance(gold, list) and isinstance(pred, list):
        if len(gold) != len(pred):
            return False
        gold_items = list(gold)
        pred_items = list(pred)
        if unordered_pairs and all(isinstance(item, list) and len(item) == 2 for item in gold_items + pred_items):
            gold_items = sorted((sorted(item, key=_sort_key) for item in gold_items), key=_sort_key)
            pred_items = sorted((sorted(item, key=_sort_key) for item in pred_items), key=_sort_key)
            return all(
                _compare_values(g_item, p_item, unordered_lists=False, unordered_pairs=False)
                for g_item, p_item in zip(gold_items, pred_items)
            )
        if unordered_lists:
            gold_items = sorted(gold_items, key=_sort_key)
            pred_items = sorted(pred_items, key=_sort_key)
        return all(
            _compare_values(g_item, p_item, unordered_lists=unordered_lists, unordered_pairs=unordered_pairs)
            for g_item, p_item in zip(gold_items, pred_items)
        )

    if isinstance(gold, (int, float)) and isinstance(pred, (int, float)):
        return _compare_numeric(gold, pred)

    return str(gold).lower().strip() == str(pred).lower().strip()


def grade(request: GradingRequest) -> float:
    submission_path = request.submission.root
    answers_path = request.references.answers_path
    if answers_path is None or not submission_path.exists():
        return 0.0

    task_id = _task_id()
    unordered_pairs = task_id in UNORDERED_PAIR_TASKS
    unordered_lists = task_id in UNORDERED_LIST_TASKS

    submission = _load_json(submission_path)
    answers = _load_json(answers_path)
    if submission is None or answers is None:
        return 0.0
    return 1.0 if _compare_values(answers, submission, unordered_lists=unordered_lists, unordered_pairs=unordered_pairs) else 0.0
