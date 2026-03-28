"""
Data preparation for ScienceBench task 69.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image


DATASET_NAME = "hca"
SOURCE_FILE = "hca_subsampled_20k.h5ad"
EXPECTED_FILENAME = "hca_cell_type_pca.png"
GOLD_FILENAME = "hca_cell_type_pca_gold.png"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _dataset_dir() -> Path:
    return _repo_root() / "ScienceAgent-bench" / "benchmark" / "datasets" / DATASET_NAME


def _gold_path() -> Path:
    return _repo_root() / "ScienceAgent-bench" / "benchmark" / "eval_programs" / "gold_results" / GOLD_FILENAME


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_placeholder_png(target: Path, *, width: int, height: int) -> None:
    Image.new("RGBA", (max(1, width), max(1, height)), (255, 255, 255, 255)).save(target, format="PNG")


def prepare(raw: Path, public: Path, private: Path) -> None:
    print("=" * 60)
    print("Preparing ScienceBench Task 69")
    print("Dataset:", DATASET_NAME)
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    dataset_dir = raw if raw.exists() else _dataset_dir()
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")

    source_file = dataset_dir / SOURCE_FILE
    if not source_file.exists():
        raise FileNotFoundError(f"Missing dataset file: {source_file}")

    _ensure_dir(public)
    _ensure_dir(private)

    target = public / DATASET_NAME / SOURCE_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_file, target)
    print(f"✓ Copied {SOURCE_FILE} to public directory")
    gold_path = _gold_path()
    if not gold_path.exists():
        raise FileNotFoundError(f"Gold image not found: {gold_path}")

    gold_img = Image.open(gold_path).convert("RGBA")
    _write_placeholder_png(public / "sample_submission.png", width=gold_img.width, height=gold_img.height)
    print("✓ Created sample_submission.png")

    gold_img.save(private / "result.png", format="PNG")
    print("✓ Copied result.png")

    print("Data preparation completed.")
