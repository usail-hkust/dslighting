"""Data preparation for ScienceBench task 90 (joint NMF reconstruction)."""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np


DATASET_NAME = "jnmf_data"
EXPECTED_FILES = [
    "fit_result_conscientiousness_W_high.npy",
    "fit_result_conscientiousness_H_high.npy",
    "fit_result_conscientiousness_W_low.npy",
    "fit_result_conscientiousness_H_low.npy",
]
GOLD_FACTORS = {
    "fit_result_conscientiousness_W_high.npy": "fit_result_conscientiousness_W_high_gold.npy",
    "fit_result_conscientiousness_H_high.npy": "fit_result_conscientiousness_H_high_gold.npy",
    "fit_result_conscientiousness_W_low.npy": "fit_result_conscientiousness_W_low_gold.npy",
    "fit_result_conscientiousness_H_low.npy": "fit_result_conscientiousness_H_low_gold.npy",
}
DATA_FILES = ["X1_conscientiousness.npy", "X2_conscientiousness.npy"]
THRESHOLDS = "Reconstruction thresholds — X1 < 34, X2 < 32"


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
    copied = 0
    for name in DATA_FILES:
        source_file = src / name
        if not source_file.exists():
            raise FileNotFoundError(f"Missing dataset file: {source_file}")
        target = dest_root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target)
        copied += 1
    print(f"✓ Copied {copied} dataset file(s) to {dest_root}")


def prepare(raw: Path, public: Path, private: Path) -> None:
    print("=" * 60)
    print("Preparing ScienceBench Task 90")
    print("Dataset:", DATASET_NAME)
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    source_dir = raw if raw.exists() else _dataset_dir()
    if not source_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {source_dir}")

    gold_dir = _gold_dir()
    for gold_name in GOLD_FACTORS.values():
        gold_path = gold_dir / gold_name
        if not gold_path.exists():
            raise FileNotFoundError(f"Gold factor missing: {gold_path}")

    _ensure_dir(public)
    _ensure_dir(private)

    _copy_dataset(source_dir, public)

    sample_dir = public / "sample_submission"
    sample_dir.mkdir(parents=True, exist_ok=True)
    for pred_name, gold_name in GOLD_FACTORS.items():
        gold_array = np.load(gold_dir / gold_name)
        np.save(sample_dir / pred_name, np.zeros_like(gold_array, dtype=np.float32))
    print("✓ Wrote zero baseline factors in sample_submission/")

    answer_dir = private / "gold_factors"
    answer_dir.mkdir(parents=True, exist_ok=True)
    for gold_name in GOLD_FACTORS.values():
        shutil.copy2(gold_dir / gold_name, answer_dir / gold_name)
    print("✓ Copied gold factor matrices for reference")

    (private / "notes.txt").write_text(
        f"Expected files in pred_results/: {', '.join(EXPECTED_FILES)}\n{THRESHOLDS}\n",
        encoding="utf-8",
    )
    print("✓ Wrote evaluation notes")

    print("Data preparation completed.")
