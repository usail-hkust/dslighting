"""
Data preparation for ScienceBench task 63.
"""

from __future__ import annotations

import base64
import shutil
from pathlib import Path

import pandas as pd

DATASET_NAME = "biosignals"
EXPECTED_FILES = [
    "bio_ecg_plot.png",
    "bio_rsp_plot.png",
]
GOLD_MAPPING = {
    "bio_ecg_plot.png": "bio_ecg_plot_gold.png",
    "bio_rsp_plot.png": "bio_rsp_plot_gold.png",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _dataset_dir() -> Path:
    return _repo_root() / "ScienceAgent-bench" / "benchmark" / "datasets" / DATASET_NAME


def _gold_dir() -> Path:
    return _repo_root() / "ScienceAgent-bench" / "benchmark" / "eval_programs" / "gold_results"


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
    print("Preparing ScienceBench Task 63")
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

    sample_df = pd.DataFrame([{"file_name": name, "image_base64": ""} for name in EXPECTED_FILES])
    sample_df.to_csv(public / "sample_submission.csv", index=False)
    print("✓ Created sample_submission.csv")

    gold_dir = _gold_dir()
    answer_rows = []
    for filename, gold_name in GOLD_MAPPING.items():
        gold_path = gold_dir / gold_name
        if not gold_path.exists():
            raise FileNotFoundError(f"Missing gold image: {gold_path}")
        encoded = base64.b64encode(gold_path.read_bytes()).decode("utf-8")
        answer_rows.append({"file_name": filename, "image_base64": encoded})
        target = private / gold_path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(gold_path, target)
    answer_df = pd.DataFrame(answer_rows)
    answer_df.to_csv(private / "answer.csv", index=False)
    print("✓ Created answer.csv and copied gold images")

    print("Data preparation completed.")
