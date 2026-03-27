"""
Data preparation for ScienceBench task 34
Dataset: biosignals
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

GOLD_FILE = None  # set inside prepare()
SOURCE_DATASET = "biosignals"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def prepare(raw: Path, public: Path, private: Path) -> None:
    """
    Prepare the ScienceAgent task data.

    Args:
        raw: Path to raw data directory (ScienceAgent-bench datasets)
        public: Path to public directory (visible to participants)
        private: Path to private directory (used for grading)
    """
    global GOLD_FILE
    GOLD_FILE = raw / "hrv_analysis_gold.csv"
    print("=" * 60)
    print("Preparing ScienceBench Task 34")
    print("Dataset:", SOURCE_DATASET)
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    _ensure_dir(public)
    _ensure_dir(private)

    if not raw.exists():
        print(f"\n⚠ Warning: Raw data directory not found: {raw}")
        _create_placeholder_files(public, private)
        return

    print("\nCopying data files to public directory...")
    file_count = 0
    for file in raw.rglob("*"):
        if file.is_file() and not file.name.startswith("."):
            rel_path = file.relative_to(raw)
            target = public / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, target)
            file_count += 1
            if file_count <= 10:
                print("  ✓ Copied:", rel_path)

    if file_count > 10:
        print("  ... and", file_count - 10, "more files")
    print("  Total files copied:", file_count)

    if GOLD_FILE.exists():
        gold_df = pd.read_csv(GOLD_FILE)
        sample_rows = gold_df.head(1).copy()
        sample_rows.to_csv(public / "sample_submission.csv", index=False)
        gold_df.to_csv(private / "answer.csv", index=False)
        print("✓ Created sample_submission.csv and answer.csv from gold data")
    else:
        print(f"⚠ Gold file not found: {GOLD_FILE}")
        _create_placeholder_files(public, private)
        return

    print("\nData preparation completed!")
    print("  Public files:", list(public.glob("*")))
    print("  Private files:", list(private.glob("*")))


def _create_placeholder_files(public: Path, private: Path) -> None:
    """Create placeholder CSVs when raw or gold data are unavailable."""
    pd.DataFrame().to_csv(public / "sample_submission.csv", index=False)
    pd.DataFrame().to_csv(private / "answer.csv", index=False)
    print("Placeholder files created")
