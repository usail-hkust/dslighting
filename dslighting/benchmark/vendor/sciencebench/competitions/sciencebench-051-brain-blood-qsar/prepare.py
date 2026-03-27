"""
Data preparation for ScienceBench task 51
Dataset: brain-blood
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

EXPECTED_FILE = "brain_blood_qsar.csv"


def _dataset_dir() -> Path:
    root = Path(__file__).resolve().parents[5]
    return root / "ScienceAgent-bench" / "benchmark" / "datasets" / "brain-blood"


def _gold_path() -> Path:
    root = Path(__file__).resolve().parents[5]
    return root / "ScienceAgent-bench" / "benchmark" / "eval_programs" / "gold_results" / "brain_blood_qsar_gold.csv"


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

    data_dir = raw if raw.exists() else _dataset_dir()
    if not data_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {data_dir}")

    _ensure_dir(public)
    _ensure_dir(private)

    required = [
        data_dir / "logBB.sdf",
        data_dir / "logBB_test.sdf",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing dataset files: " + ", ".join(missing))

    for path in required:
        target = public / path.relative_to(data_dir.parent)
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

    gold_path = _gold_path()
    if not gold_path.exists():
        raise FileNotFoundError(f"Gold CSV not found: {gold_path}")
    shutil.copy2(gold_path, private / "answer.csv")
    print("✓ Copied answer.csv")

    print("brain-blood QSAR task preparation complete. Expected submission file: pred_results/brain_blood_qsar.csv")


if __name__ == "__main__":
    raise SystemExit("Use this module via the benchmark preparation tooling.")
