"""
Data preparation for ScienceBench task 42
Dataset: biosignals
"""

from __future__ import annotations

import base64
import shutil
from pathlib import Path

import pandas as pd

EXPECTED_FILENAME = "EDR_analyze_pred.png"


def _default_dataset_dir() -> Path:
    root = Path(__file__).resolve().parents[5]
    return root / "ScienceAgent-bench" / "benchmark" / "datasets" / "biosignals"


def _default_gold_path() -> Path:
    root = Path(__file__).resolve().parents[5]
    return root / "ScienceAgent-bench" / "benchmark" / "eval_programs" / "gold_results" / "EDR_analyze_gold.png"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def prepare(raw: Path, public: Path, private: Path) -> None:
    print("=" * 60)
    print("Preparing ScienceBench Task 42")
    print("Dataset: biosignals")
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    data_dir = raw if raw.exists() else _default_dataset_dir()
    if not data_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {data_dir}")

    _ensure_dir(public)
    _ensure_dir(private)

    source_file = data_dir / "bio_eventrelated_100hz.csv"
    if not source_file.exists():
        raise FileNotFoundError(f"Data file not found: {source_file}")
    shutil.copy2(source_file, public / "bio_eventrelated_100hz.csv")
    print("✓ Copied biosignal data")

    sample_df = pd.DataFrame([{"file_name": EXPECTED_FILENAME, "image_base64": ""}])
    sample_df.to_csv(public / "sample_submission.csv", index=False)
    print("✓ Created sample_submission.csv")

    gold_path = _default_gold_path()
    if not gold_path.exists():
        raise FileNotFoundError(f"Gold image not found: {gold_path}")
    gold_bytes = gold_path.read_bytes()
    answer_df = pd.DataFrame(
        [{"file_name": EXPECTED_FILENAME, "image_base64": base64.b64encode(gold_bytes).decode("utf-8")}]
    )
    answer_df.to_csv(private / "answer.csv", index=False)
    print("✓ Created answer.csv with encoded gold image")

    print("EDR analysis task preparation complete")
