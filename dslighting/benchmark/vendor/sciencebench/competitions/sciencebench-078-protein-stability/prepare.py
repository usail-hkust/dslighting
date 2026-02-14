"""
Data preparation for ScienceBench task 78 (protein stability prediction).
"""

from __future__ import annotations

from pathlib import Path
import shutil

import pandas as pd

DATASET_NAME = "pucci"
TRAIN_FILE = "pucci-proteins_train.csv"
TEST_FILE = "pucci-proteins_test.csv"
EXPECTED_FILENAME = "pucci-proteins_test_pred.csv"
GOLD_FILENAME = "pucci-proteins_test_gold.csv"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _dataset_dir() -> Path:
    return _repo_root() / "ScienceAgent-bench" / "benchmark" / "datasets" / DATASET_NAME


def _gold_path() -> Path:
    return _repo_root() / "ScienceAgent-bench" / "benchmark" / "eval_programs" / "gold_results" / GOLD_FILENAME


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def prepare(raw: Path, public: Path, private: Path) -> None:
    print("=" * 60)
    print("Preparing ScienceBench Task 78")
    print("Dataset:", DATASET_NAME)
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    dataset_dir = raw if raw.exists() else _dataset_dir()
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")

    train_path = dataset_dir / TRAIN_FILE
    test_path = dataset_dir / TEST_FILE
    if not train_path.exists() or not test_path.exists():
        raise FileNotFoundError("Missing Pucci dataset CSVs.")

    gold_path = _gold_path()
    if not gold_path.exists():
        raise FileNotFoundError(f"Gold CSV not found: {gold_path}")

    _ensure_dir(public)
    _ensure_dir(private)

    for source in (train_path, test_path):
        target = public / DATASET_NAME / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    print("✓ Copied Pucci train/test CSVs")

    sample_df = pd.DataFrame({"deltaTm": [0.0]})
    sample_df.to_csv(public / "sample_submission.csv", index=False)
    print("✓ Created sample_submission.csv with placeholder column")

    gold_df = pd.read_csv(gold_path)
    gold_df.to_csv(private / "answer.csv", index=False)
    print("✓ Wrote answer.csv containing gold deltaTm values")

    shutil.copy2(gold_path, private / gold_path.name)
    print("✓ Copied gold CSV for reference")

    print("Data preparation completed.")
