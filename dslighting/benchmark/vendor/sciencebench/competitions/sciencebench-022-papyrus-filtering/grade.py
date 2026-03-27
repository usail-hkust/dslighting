"""Grading function for ScienceBench Task 22 (Papyrus filtering)."""

from __future__ import annotations

import pandas as pd
import pickle

from dslighting.benchmark.grading.models import GradingRequest

TARGET_ID_COLUMN = "Activity_ID"


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    numeric_cols = df.select_dtypes(include=["number"]).columns
    if len(numeric_cols):
        df[numeric_cols] = df[numeric_cols].round(3)
    if TARGET_ID_COLUMN in df.columns:
        df = df.sort_values(by=[TARGET_ID_COLUMN]).reset_index(drop=True)
    return df.astype(str)


def grade(request: GradingRequest) -> float:
    submission_path = request.submission.root
    answers_path = request.references.private_dir / "answer.pkl"

    # Read pickle files
    with open(submission_path, 'rb') as f:
        submission = pickle.load(f)
    with open(answers_path, 'rb') as f:
        answers = pickle.load(f)

    if submission.empty:
        print("Submission is empty.")
        return 0.0
    if answers.empty:
        print("Answer data is empty.")
        return 0.0

    pred = _normalize(submission)
    gold = _normalize(answers)

    if pred.shape != gold.shape:
        print(f"Shape mismatch: submission {pred.shape} vs gold {gold.shape}")
        return 0.0

    match_rows = 0
    for idx, gold_row in gold.iterrows():
        if list(pred.iloc[idx]) == list(gold_row):
            match_rows += 1

    total = len(gold)
    if match_rows != total:
        print(f"Papyrus filtering: {match_rows} / {total} rows matched the gold reference.")

    return float(match_rows == total)
