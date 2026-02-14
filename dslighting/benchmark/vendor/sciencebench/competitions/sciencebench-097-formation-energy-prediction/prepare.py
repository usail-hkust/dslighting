"""Data preparation for ScienceBench task 97 (formation energy prediction)."""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np


DATASET_NAME = "perovskite"
PRED_FILENAME = "formation_energy_prediction_pred.txt"
GOLD_FILENAME = "formation_energy_prediction_gold.txt"
SAMPLE_FILENAME = "sample_submission.txt"


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
    dest_root.mkdir(parents=True, exist_ok=True)
    copied = 0
    for item in src.iterdir():
        if not item.is_file():
            continue
        shutil.copy2(item, dest_root / item.name)
        copied += 1
    print(f"✓ Copied {copied} dataset file(s) to {dest_root}")


def prepare(raw: Path, public: Path, private: Path) -> None:
    print("=" * 60)
    print("Preparing ScienceBench Task 97")
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
        raise FileNotFoundError(f"Gold file not found: {gold_path}")

    _ensure_dir(public)
    _ensure_dir(private)

    _copy_dataset(source_dir, public)

    gold_values = np.loadtxt(gold_path)
    np.savetxt(public / SAMPLE_FILENAME, np.zeros_like(gold_values), fmt="%.6f")
    print("✓ Wrote sample_submission.txt placeholder")

    shutil.copy2(gold_path, private / "answer.txt")
    print("✓ Copied gold predictions to private directory")

    (private / "notes.txt").write_text(
        f"Expected submission: pred_results/{PRED_FILENAME}\nMSE threshold: 0.1\n",
        encoding="utf-8",
    )
    print("✓ Wrote notes.txt")

    print("Data preparation completed.")
