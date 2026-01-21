"""
Data preparation for ScienceBench task 51
Dataset: brain-blood
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

EXPECTED_FILE = "brain_blood_qsar.csv"
DATASET_DIR = Path("/path/to/ScienceAgent-bench/benchmark/datasets/brain-blood")
GOLD_FILE = Path("/path/to/ScienceAgent-bench/benchmark/eval_programs/gold_results/brain_blood_qsar_gold.csv")


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def prepare(raw: Path, public: Path, private: Path) -> None:
    print("=" * 60)
    print("Preparing ScienceBench Task 51")
    print("Dataset: brain-blood")
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    source = raw if raw.exists() else DATASET_DIR
    if not source.exists():
        raise FileNotFoundError(f"Dataset directory not found: {source}")

    _ensure_dir(public)
    _ensure_dir(private)

    required = [
        source / "logBB.sdf",
        source / "logBB_test.sdf",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing dataset files: " + ", ".join(missing))

    for path in required:
        target = public / path.relative_to(source.parent)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    print("✓ Copied logBB SDF files")

    sample_df = pd.DataFrame(
        {
            "label": [1, 0],
        }
    )
    sample_df.to_csv(public / "sample_submission.csv", index=False)
    print("✓ Created sample_submission.csv")

    if not GOLD_FILE.exists():
        raise FileNotFoundError(f"Gold CSV not found: {GOLD_FILE}")
    shutil.copy2(GOLD_FILE, private / "answer.csv")
    print("✓ Copied answer.csv")

    print("Preparation complete. Expected submission file: pred_results/brain_blood_qsar.csv")


if __name__ == "__main__":
    raise SystemExit("Use this module via the benchmark preparation tooling.")
