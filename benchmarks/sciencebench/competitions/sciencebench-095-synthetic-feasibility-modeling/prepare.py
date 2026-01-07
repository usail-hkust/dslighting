"""Data preparation for ScienceBench task 95 (synthetic feasibility modeling)."""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np


DATASET_NAME = "tox21"
PRED_FILENAME = "tox21_mol_scscores_pred.npy"
GOLD_FILENAME = "tox21_mol_scscores_gold.npy"
SAMPLE_FILENAME = "sample_submission.npy"


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
    print("Preparing ScienceBench Task 95")
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
        raise FileNotFoundError(f"Gold array not found: {gold_path}")

    _ensure_dir(public)
    _ensure_dir(private)

    _copy_dataset(source_dir, public)

    gold_array = np.load(gold_path)
    np.save(public / SAMPLE_FILENAME, np.zeros_like(gold_array, dtype=np.float32))
    print("✓ Wrote sample_submission.npy placeholder")

    np.save(private / "answer.npy", gold_array)
    print("✓ Saved answer.npy with gold scores")

    (private / "notes.txt").write_text(
        f"Expected submission: pred_results/{PRED_FILENAME}\nMSE threshold: 0.4\n",
        encoding="utf-8",
    )
    print("✓ Wrote notes.txt")

    print("Data preparation completed.")
