"""
Data preparation for ScienceBench task 45
Dataset: biopsykit_questionnaire_data
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

EXPECTED_FILE = "questionnaire_pred.csv"


def _default_dataset_dir() -> Path:
    root = Path(__file__).resolve().parents[5]
    return root / "ScienceAgent-bench" / "benchmark" / "datasets" / "biopsykit_questionnaire_data"


def _default_gold_path() -> Path:
    root = Path(__file__).resolve().parents[5]
    return root / "ScienceAgent-bench" / "benchmark" / "eval_programs" / "gold_results" / "biopsykit_questionnaire_gold.csv"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def prepare(raw: Path, public: Path, private: Path) -> None:
    print("=" * 60)
    print("Preparing ScienceBench Task 45")
    print("Dataset: biopsykit_questionnaire_data")
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    data_dir = raw if raw.exists() else _default_dataset_dir()
    if not data_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {data_dir}")

    _ensure_dir(public)
    _ensure_dir(private)

    data_file = data_dir / "questionnaire_data.pkl"
    if not data_file.exists():
        raise FileNotFoundError(f"Data file not found: {data_file}")
    shutil.copy2(data_file, public / "questionnaire_data.pkl")
    print("✓ Copied questionnaire data")

    sample_df = pd.DataFrame(
        {
            "subject": ["Vp01", "Vp02"],
            "score_1": [21, 18],
            "score_2": [7, 9],
            "score_3": [28, 27],
        }
    )
    sample_df.to_csv(public / "sample_submission.csv", index=False)
    print("✓ Created sample_submission.csv")

    gold_path = _default_gold_path()
    if not gold_path.exists():
        raise FileNotFoundError(f"Gold CSV not found: {gold_path}")
    shutil.copy2(gold_path, private / "answer.csv")
    print("✓ Copied answer.csv")

    print("Questionnaire task preparation complete")
