"""Grading function for ScienceBench task 44 (IMU sleep endpoints)."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from dslighting.benchmark.grading.models import GradingRequest

EXPECTED_KEYS = {"sleep_onset", "wake_onset", "total_sleep_duration"}


def _coerce_to_dict(data: Any) -> Dict[str, Any]:
    if isinstance(data, dict):
        return data
    if isinstance(data, (str, Path)):
        return json.loads(Path(data).read_text())
    if isinstance(data, pd.DataFrame):
        if EXPECTED_KEYS.issubset(data.columns):
            row = data.iloc[0]
            return {key: row[key] for key in EXPECTED_KEYS}
        if {"key", "value"}.issubset(data.columns):
            return dict(zip(data["key"], data["value"]))
    raise TypeError(f"Unsupported submission format: {type(data)}")


def grade(request: GradingRequest) -> float:
    submission_path = request.submission.root
    answers_path = request.references.private_dir / "answer.json"

    # Try to read as JSON first
    try:
        pred_text = submission_path.read_text()
        pred = json.loads(pred_text)
    except:
        # Fall back to CSV
        pred_df = pd.read_csv(submission_path)
        if EXPECTED_KEYS.issubset(pred_df.columns):
            pred = {key: pred_df.iloc[0][key] for key in EXPECTED_KEYS}
        else:
            print("Submission missing required keys")
            return 0.0

    try:
        gold_text = answers_path.read_text()
        gold = json.loads(gold_text)
    except:
        gold_df = pd.read_csv(answers_path)
        if EXPECTED_KEYS.issubset(gold_df.columns):
            gold = {key: gold_df.iloc[0][key] for key in EXPECTED_KEYS}
        else:
            print("Gold data missing required keys")
            return 0.0

    missing = EXPECTED_KEYS - pred.keys()
    if missing:
        print(f"Submission missing required keys: {sorted(missing)}")
        return 0.0

    for key in EXPECTED_KEYS:
        if key not in gold:
            print(f"Gold data missing key '{key}'.")
            return 0.0

    for key in EXPECTED_KEYS:
        pred_val = pred[key]
        gold_val = gold[key]
        if isinstance(gold_val, str):
            if pred_val != gold_val:
                print(f"String mismatch for '{key}': {pred_val} vs {gold_val}")
                return 0.0
        else:
            try:
                if not math.isclose(float(pred_val), float(gold_val), rel_tol=1e-5):
                    print(f"Numeric mismatch for '{key}': {pred_val} vs {gold_val}")
                    return 0.0
            except (TypeError, ValueError):
                print(f"Non-numeric value encountered for '{key}'.")
                return 0.0

    return 1.0
