"""Grading function for ScienceBench task 37 (Cold Face Test analysis)."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict

from dslighting.benchmark.grading.models import GradingRequest

EXPECTED_KEYS = {"baseline_hr", "onset_hr", "onset_hr_percent"}


def _load_json(data: Any) -> Dict[str, Any]:
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        return json.loads(data)
    raise TypeError("Submission must be a JSON object or string.")


def grade(request: GradingRequest) -> float:
    submission_path = request.submission.root
    answers_path = request.references.private_dir / "answer.json"

    # Read submission as text (JSON)
    submission_text = submission_path.read_text()
    answers_text = answers_path.read_text()

    try:
        pred = _load_json(submission_text)
        gold = _load_json(answers_text)
    except (TypeError, json.JSONDecodeError) as exc:
        print(f"Failed to parse JSON: {exc}")
        return 0.0

    missing_keys = EXPECTED_KEYS - pred.keys()
    if missing_keys:
        print(f"Submission missing required keys: {sorted(missing_keys)}")
        return 0.0

    correct = 0
    total = len(EXPECTED_KEYS)

    for key in EXPECTED_KEYS:
        if key not in gold:
            print(f"Gold data missing key '{key}'.")
            return 0.0
        if math.isclose(float(pred[key]), float(gold[key])):
            correct += 1

    if correct != total:
        print(f"CFT parameter matches: {correct} / {total}")
        return 0.0

    return 1.0
