"""
Data preparation for ScienceBench task 59.
"""

from __future__ import annotations

import base64
import shutil
from pathlib import Path

import pandas as pd

DATASET_NAME = "nvc"
EXPECTED_FILENAME = "nvc_heatmap.png"
GOLD_FILENAME = "nvc_heatmap_gold.png"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _dataset_dir() -> Path:
    return _repo_root() / "ScienceAgent-bench" / "benchmark" / "datasets" / DATASET_NAME


def _gold_path() -> Path:
    return _repo_root() / "ScienceAgent-bench" / "benchmark" / "eval_programs" / "gold_results" / GOLD_FILENAME


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _copy_dataset(src: Path, public: Path) -> None:
    dest_root = public / DATASET_NAME
    counter = 0
    for item in src.rglob("*"):
        if not item.is_file():
            continue
        rel = item.relative_to(src)
        target = dest_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        counter += 1
    print(f"✓ Copied {counter} dataset file(s) to {dest_root}")


def prepare(raw: Path, public: Path, private: Path) -> None:
    print("=" * 60)
    print("Preparing ScienceBench Task 59")
    print("Dataset:", DATASET_NAME)
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    source_dir = raw if raw.exists() else _dataset_dir()
    if not source_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {source_dir}")

    _ensure_dir(public)
    _ensure_dir(private)
    _copy_dataset(source_dir, public)

    sample_df = pd.DataFrame([{"file_name": EXPECTED_FILENAME, "image_base64": ""}])
    sample_df.to_csv(public / "sample_submission.csv", index=False)
    print("✓ Created sample_submission.csv")

    gold_path = _gold_path()
    if not gold_path.exists():
        raise FileNotFoundError(f"Gold image not found: {gold_path}")
    encoded = base64.b64encode(gold_path.read_bytes()).decode("utf-8")
    answer_df = pd.DataFrame([{"file_name": EXPECTED_FILENAME, "image_base64": encoded}])
    answer_df.to_csv(private / "answer.csv", index=False)
    target = private / gold_path.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(gold_path, target)
    print("✓ Stored encoded gold image and copied original")

    print("Data preparation completed.")
