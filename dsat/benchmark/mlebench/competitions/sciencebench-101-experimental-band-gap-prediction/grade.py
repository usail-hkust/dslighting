"""Grader for ScienceBench task 101 (experimental band-gap prediction)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PRED_FILENAME = "experimental_band_gap_prediction_pred.csv"
GOLD_FILENAME = "experimental_band_gap_prediction_gold.csv"
TARGET_COLUMN = "gap_expt_eV"
THRESHOLD = 0.6


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _pred_path() -> Path:
    return Path("pred_results") / PRED_FILENAME


def _gold_path() -> Path:
    return (
        _repo_root()
        / "benchmark"
        / "eval_programs"
        / "gold_results"
        / GOLD_FILENAME
    )


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required file missing: {path}")
    return pd.read_csv(path)


def grade(submission, answers) -> float:
    pred_df = _load_csv(_pred_path())
    gold_df = _load_csv(_gold_path())

    if TARGET_COLUMN not in pred_df.columns:
        print(f"Missing '{TARGET_COLUMN}' column in prediction.")
        return 0.0

    merged = gold_df[[TARGET_COLUMN]].join(pred_df[[TARGET_COLUMN]], how="inner", rsuffix="_pred")
    if merged.empty:
        print("No overlapping rows between prediction and gold.")
        return 0.0

    mae = (merged[TARGET_COLUMN] - merged[f"{TARGET_COLUMN}_pred"]).abs().mean()
    print(f"MAE: {mae}")
    return 1.0 if mae < THRESHOLD else 0.0
