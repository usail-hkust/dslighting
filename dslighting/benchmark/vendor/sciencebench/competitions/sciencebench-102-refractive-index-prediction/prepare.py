"""Data preparation for ScienceBench task 102 (refractive index prediction)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd


DATASET_NAME = "ref_index"
PRED_FILENAME = "ref_index_predictions_pred.csv"
GOLD_FILENAME = "ref_index_predictions_gold.csv"
SAMPLE_FILENAME = "sample_submission.csv"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _dataset_dir() -> Path:
    return _repo_root() / "ScienceAgent-bench" / "benchmark" / "datasets" / DATASET_NAME


def _gold_path() -> Path:
    return (
        _repo_root()
        / "ScienceAgent-bench"
        / "benchmark"
        / "eval_programs"
        / "gold_results"
        / GOLD_FILENAME
    )


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _copy_dataset(src: Path, public: Path) -> None:
    dest_root = public / DATASET_NAME
    dest_root.mkdir(parents=True, exist_ok=True)
    copied = 0
    for item in src.iterdir():
        if not item.is_file():
            continue
        shutil.copy2(item, dest_root / item.name)
        copied += 1
    print(f"✓ Copied {copied} dataset file(s) to {dest_root}")


def prepare(raw: Path, public: Path, private: Path) -> None:
    print("=" * 60)
    print("Preparing ScienceBench Task 102")
    print("Dataset:", DATASET_NAME)
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    source_dir = raw if raw.exists() else _dataset_dir()
    if not source_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {source_dir}")

    gold_path = _gold_path()
    if not gold_path.exists():
        raise FileNotFoundError(f"Gold CSV not found: {gold_path}")

    _ensure_dir(public)
    _ensure_dir(private)

    _copy_dataset(source_dir, public)

    gold_df = pd.read_csv(gold_path)
    sample = gold_df.head(3).copy()
    sample["refractive_index"] = 0.0
    sample.to_csv(public / SAMPLE_FILENAME, index=False)
    print("✓ Created sample_submission.csv placeholder")

    gold_df.to_csv(private / "answer.csv", index=False)
    print("✓ Copied gold CSV to private directory")

    (private / "notes.txt").write_text(
        f"Expected submission: pred_results/{PRED_FILENAME}\nMAE threshold: 0.78\n",
        encoding="utf-8",
    )
    print("✓ Wrote notes.txt")

    print("Data preparation completed.")
