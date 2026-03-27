"""
Data preparation for ScienceBench task 44
Dataset: sleep_imu_data
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

EXPECTED_FILE = "imu_pred.json"


def _default_dataset_dir() -> Path:
    root = Path(__file__).resolve().parents[5]
    return root / "ScienceAgent-bench" / "benchmark" / "datasets" / "sleep_imu_data"


def _default_gold_path() -> Path:
    root = Path(__file__).resolve().parents[5]
    return root / "ScienceAgent-bench" / "benchmark" / "eval_programs" / "gold_results" / "biopsykit_imu_gold.json"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def prepare(raw: Path, public: Path, private: Path) -> None:
    print("=" * 60)
    print("Preparing ScienceBench Task 44")
    print("Dataset: sleep_imu_data")
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    data_dir = raw if raw.exists() else _default_dataset_dir()
    if not data_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {data_dir}")

    _ensure_dir(public)
    _ensure_dir(private)

    data_file = data_dir / "sleep_data.pkl"
    if not data_file.exists():
        raise FileNotFoundError(f"Data file not found: {data_file}")
    shutil.copy2(data_file, public / "sleep_data.pkl")
    print("✓ Copied IMU sleep data")

    sample_json = {
        "sleep_onset": "2019-09-03T02:15:00+02:00",
        "wake_onset": "2019-09-03T09:05:00+02:00",
        "total_sleep_duration": 24540,
    }
    (public / "sample_submission.json").write_text(json.dumps(sample_json, indent=2))
    print("✓ Created sample_submission.json")

    gold_path = _default_gold_path()
    if not gold_path.exists():
        raise FileNotFoundError(f"Gold JSON not found: {gold_path}")
    shutil.copy2(gold_path, private / "answer.json")
    print("✓ Copied answer.json")

    print("IMU analysis task preparation complete")
