"""
Data preparation for ScienceBench task 71 (ThingseEG2 linear mapping).
"""

from __future__ import annotations

from pathlib import Path
import shutil

import numpy as np

DATASET_NAME = "thingseeg2"
EXPECTED_FILENAME = "linear_sub01tosub03_pred.npy"
SOURCE_FILES = [
    Path("train/sub01.npy"),
    Path("train/sub03.npy"),
    Path("test/sub01.npy"),
]
GOLD_FILENAME = "sub03.npy"
SAMPLE_FILENAME = "sample_submission.npy"
ANSWER_FILENAME = "answer.npy"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _dataset_dir() -> Path:
    return _repo_root() / "ScienceAgent-bench" / "benchmark" / "datasets" / DATASET_NAME


def _gold_path() -> Path:
    return _repo_root() / "ScienceAgent-bench" / "benchmark" / "eval_programs" / "gold_results" / GOLD_FILENAME


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _reshape_gold(array: np.ndarray, train_stats: np.ndarray) -> np.ndarray:
    mean = float(train_stats.mean())
    std = float(train_stats.std())
    normalized = (array - mean) / std
    reshaped = np.transpose(normalized, (1, 0, 2)).reshape(200, 3400)
    return reshaped.astype(np.float32)


def prepare(raw: Path, public: Path, private: Path) -> None:
    print("=" * 60)
    print("Preparing ScienceBench Task 71: ThingseEG2 linear mapping")
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    dataset_dir = raw if raw.exists() else _dataset_dir()
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")

    gold_path = _gold_path()
    if not gold_path.exists():
        raise FileNotFoundError(f"Gold file not found: {gold_path}")

    _ensure_dir(public)
    _ensure_dir(private)

    for relative in SOURCE_FILES:
        source = dataset_dir / relative
        if not source.exists():
            raise FileNotFoundError(f"Missing dataset file: {source}")
        target = public / DATASET_NAME / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    print("✓ Copied ThingseEG2 train/test arrays")

    train_sub3 = np.load(dataset_dir / "train" / "sub03.npy")
    gold_raw = np.load(gold_path)
    gold_array = _reshape_gold(gold_raw, train_sub3)

    sample_path = public / SAMPLE_FILENAME
    np.save(sample_path, np.zeros_like(gold_array, dtype=np.float32))
    print(f"✓ Wrote {SAMPLE_FILENAME} as a zero baseline")

    answer_path = private / ANSWER_FILENAME
    np.save(answer_path, gold_array)
    print(f"✓ Saved {ANSWER_FILENAME} with normalized gold array")

    shutil.copy2(gold_path, private / gold_path.name)
    print("✓ Copied raw gold array for reference")

    metadata = (
        f"Expected submission: pred_results/{EXPECTED_FILENAME}\n"
        f"Output shape after reshape: {gold_array.shape}\n"
        f"Train sub03 mean/std: {train_sub3.mean():.6f}, {train_sub3.std():.6f}\n"
    )
    (private / "metadata.txt").write_text(metadata, encoding="utf-8")
    print("✓ Wrote metadata.txt")

    print("Preparation complete.")
