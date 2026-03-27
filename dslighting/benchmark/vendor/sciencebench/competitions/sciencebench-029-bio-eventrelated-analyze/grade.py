"""Grading function for ScienceBench task 29 (biosignal event analysis)."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from dslighting.benchmark.grading.models import GradingRequest

REQUIRED_COLUMNS = ["Condition", "ECG_Rate_Mean", "RSP_Rate_Mean", "EDA_Peak_Amplitude"]


def _rounded(value: Any, digits: int = 3) -> float:
    """Round a scalar to the desired precision, returning NaN on failure."""
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return float("nan")


def grade(request: GradingRequest) -> float:
    submission_path = request.submission.root
    answers_path = request.references.private_dir / "answer.csv"

    submission = pd.read_csv(submission_path)
    answers = pd.read_csv(answers_path)

    if submission.empty:
        print("Submission is empty.")
        return 0.0
    if answers.empty:
        print("Answer data is empty.")
        return 0.0

    if not set(REQUIRED_COLUMNS).issubset(submission.columns):
        print("Submission missing required columns.")
        return 0.0
    if not set(REQUIRED_COLUMNS).issubset(answers.columns):
        print("Answers missing required columns.")
        return 0.0

    pred = submission[REQUIRED_COLUMNS].copy().reset_index(drop=True)
    gold = answers[REQUIRED_COLUMNS].copy().reset_index(drop=True)

    if len(pred) != len(gold):
        print(f"Row count mismatch: submission {len(pred)} vs gold {len(gold)}")
        return 0.0

    total_cells = len(gold) * len(REQUIRED_COLUMNS)
    cell_matches = 0

    for idx, gold_row in gold.iterrows():
        pred_row = pred.iloc[idx]

        matches = [0] * len(REQUIRED_COLUMNS)
        matches[0] = int(pred_row["Condition"] == gold_row["Condition"])

        ecg_pred = _rounded(pred_row["ECG_Rate_Mean"])
        ecg_gold = _rounded(gold_row["ECG_Rate_Mean"])

        rsp_pred = _rounded(pred_row["RSP_Rate_Mean"])
        rsp_gold = _rounded(gold_row["RSP_Rate_Mean"])

        eda_pred = _rounded(pred_row["EDA_Peak_Amplitude"])
        eda_gold = _rounded(gold_row["EDA_Peak_Amplitude"])

        if any(math.isnan(value) for value in (ecg_pred, ecg_gold, rsp_pred, rsp_gold, eda_pred, eda_gold)):
            print(f"Non-numeric values detected at row {idx}.")
            return 0.0

        matches[1] = int(abs(ecg_pred - ecg_gold) <= 0.5)
        matches[2] = int(abs(rsp_pred - rsp_gold) <= 0.5)
        matches[3] = int(abs(eda_pred - eda_gold) <= 1.0)

        cell_matches += sum(matches)

    if cell_matches != total_cells:
        print(f"Biosignal event analysis matches: {cell_matches} / {total_cells}")

    return float(cell_matches == total_cells)
