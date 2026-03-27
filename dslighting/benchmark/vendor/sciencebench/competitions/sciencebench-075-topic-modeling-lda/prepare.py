"""
Data preparation for ScienceBench task 75 (Topic Modeling LDA).
"""

from __future__ import annotations

import base64
import shutil
from pathlib import Path

import pandas as pd

DATASET_NAME = "pbmc"
SOURCE_FILE = "pbmc_10k_protein_v3.h5ad"
EXPECTED_FILENAME = "topic_modeling_pred.png"
GOLD_FILENAME = "topic_modeling_gold.png"


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
    print("Preparing ScienceBench Task 75")
    print("Dataset:", DATASET_NAME)
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    dataset_dir = raw if raw.exists() else _dataset_dir()
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")

    source_file = dataset_dir / SOURCE_FILE
    if not source_file.exists():
        raise FileNotFoundError(f"Missing dataset file: {source_file}")

    gold_path = _gold_path()
    if not gold_path.exists():
        raise FileNotFoundError(f"Gold image not found: {gold_path}")

    _ensure_dir(public)
    _ensure_dir(private)

    target = public / DATASET_NAME / SOURCE_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_file, target)
    print(f"✓ Copied {SOURCE_FILE} to public directory")

    sample_df = pd.DataFrame([{"file_name": EXPECTED_FILENAME, "image_base64": ""}])
    sample_df.to_csv(public / "sample_submission.csv", index=False)
    print("✓ Created sample_submission.csv")

    encoded = base64.b64encode(gold_path.read_bytes()).decode("utf-8")
    answer_df = pd.DataFrame([{"file_name": EXPECTED_FILENAME, "image_base64": encoded}])
    answer_df.to_csv(private / "answer.csv", index=False)
    shutil.copy2(gold_path, private / gold_path.name)
    print("✓ Stored encoded gold image and copied original")

    print("Data preparation completed.")
