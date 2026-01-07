"""Grading function for ScienceBench task 51 (brain-blood QSAR)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.metrics import balanced_accuracy_score

EXPECTED_FILE = "pred_results/brain_blood_qsar.csv"
GOLD_FILE = Path("benchmark/eval_programs/gold_results/brain_blood_qsar_gold.csv")
THRESHOLD = 0.70


def _extract_labels(data: Any) -> pd.Series:
    if isinstance(data, pd.DataFrame):
        if "label" not in data.columns:
            raise ValueError("Data must contain a 'label' column.")
        return data["label"]
    if isinstance(data, (str, Path)):
        df = pd.read_csv(data)
        if "label" not in df.columns:
            raise ValueError(f"CSV at {data} must contain a 'label' column.")
        return df["label"]
    raise TypeError(f"Unsupported data type: {type(data)}")


def _load_submission(submission: Any) -> pd.Series:
    try:
        return _extract_labels(submission)
    except TypeError:
        path = Path(EXPECTED_FILE)
        if not path.exists():
            raise FileNotFoundError(f"Expected prediction file missing: {EXPECTED_FILE}")
        return _extract_labels(path)


def _load_answers(answers: Any) -> pd.Series:
    try:
        return _extract_labels(answers)
    except TypeError:
        if not GOLD_FILE.exists():
            raise FileNotFoundError(f"Gold file not found: {GOLD_FILE}")
        return _extract_labels(GOLD_FILE)


def grade(submission: Any, answers: Any) -> float:
    pred_labels = _load_submission(submission)
    gold_labels = _load_answers(answers)

    if len(pred_labels) != len(gold_labels):
        print(f"Row count mismatch: {len(pred_labels)} vs {len(gold_labels)}")
        return 0.0

    score = balanced_accuracy_score(gold_labels, pred_labels)
    print(f"Balanced accuracy: {score}")
    return 1.0 if score >= THRESHOLD else 0.0
