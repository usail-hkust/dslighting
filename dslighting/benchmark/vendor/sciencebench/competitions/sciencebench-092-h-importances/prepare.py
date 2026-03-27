"""Data preparation for ScienceBench task 92 (JNMF H importances)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


DATASET_NAME = "jnmf_visualization"
PRED_FILENAME = "jnmf_h_importances.json"
GOLD_FILENAME = "jnmf_h_importances_gold.json"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _dataset_dir() -> Path:
    return _repo_root() / "ScienceAgent-bench" / "benchmark" / "datasets" / DATASET_NAME


def _gold_path() -> Path:
    return (
        _repo_root()
        / "ScienceAgent-bench"
        / "benchmark"
        / "eval_programs"
        / "gold_results"
        / GOLD_FILENAME
    )


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _copy_dataset(src: Path, public: Path) -> None:
    dest_root = public / DATASET_NAME
    copied = 0
    for item in src.rglob("*"):
        if not item.is_file():
            continue
        rel = item.relative_to(src)
        target = dest_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        copied += 1
    print(f"✓ Copied {copied} dataset file(s) to {dest_root}")


def prepare(raw: Path, public: Path, private: Path) -> None:
    print("=" * 60)
    print("Preparing ScienceBench Task 92")
    print("Dataset:", DATASET_NAME)
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    source_dir = raw if raw.exists() else _dataset_dir()
    if not source_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {source_dir}")

    gold_path = _gold_path()
    if not gold_path.exists():
        raise FileNotFoundError(f"Gold JSON not found: {gold_path}")

    _ensure_dir(public)
    _ensure_dir(private)

    _copy_dataset(source_dir, public)

    sample_path = public / "sample_submission.json"
    with sample_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "common_error": 0.0,
                "common_importance": 0.0,
                "high_importance": 0.0,
                "low_importance": 0.0,
                "distinct_error": 0.0,
                "distinct_importance": 0.0,
            },
            handle,
            indent=2,
        )
    print("✓ Created sample_submission.json placeholder")

    shutil.copy2(gold_path, private / PRED_FILENAME)
    print("✓ Copied gold JSON to private directory")

    print("Data preparation completed.")
