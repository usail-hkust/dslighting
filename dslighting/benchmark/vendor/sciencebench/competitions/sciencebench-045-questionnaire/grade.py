"""Grading function for ScienceBench task 45 (questionnaire scoring)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from dslighting.benchmark.grading.models import GradingRequest


def _load_table(data: Any) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        return data.copy()
    if isinstance(data, (str, Path)):
        df = pd.read_csv(data)
        if "subject" not in df.columns:
            df = pd.read_csv(data, header=None)
        return df
    raise TypeError(f"Unsupported submission type: {type(data)}")


def _prepare_frame(df: pd.DataFrame) -> pd.DataFrame:
    columns = list(df.columns)
    if "subject" not in columns:
        first = columns[0]
        df = df.rename(columns={first: "subject"})
        columns[0] = "subject"
    normalized = ["subject"] + [f"value_{i}" for i in range(1, len(columns))]
    rename_map = {old: new for old, new in zip(columns, normalized)}
    df = df.rename(columns=rename_map)
    return df.set_index("subject").sort_index()


def grade(request: GradingRequest) -> float:
    submission_path = request.submission.root
    answers_path = request.references.private_dir / "answer.csv"

    try:
        pred_df = pd.read_csv(submission_path)
    except:
        print(f"Could not read submission file")
        return 0.0

    try:
        gold_df = pd.read_csv(answers_path)
    except:
        print(f"Could not read gold file")
        return 0.0

    pred_processed = _prepare_frame(pred_df)
    gold_processed = _prepare_frame(gold_df)

    if pred_processed.shape != gold_processed.shape:
        print(
            f"Shape mismatch: prediction {pred_processed.shape} vs gold {gold_processed.shape}"
        )
        return 0.0

    if list(pred_processed.columns) != list(gold_processed.columns):
        print("Column mismatch between prediction and gold reference.")
        return 0.0

    matches = (pred_processed == gold_processed).all(axis=1)
    if not matches.all():
        mismatched = matches[~matches].index.tolist()
        print(f"Rows with mismatched responses: {mismatched}")
        return 0.0

    return 1.0
