"""Data preparation for ScienceBench task 53."""

from __future__ import annotations

import shutil
from pathlib import Path

DATASET_NAME = "MountainLionNew"
EXPECTED_FILES = [
    "landCover_reclassified.tif",
    "protected_status_reclassified.tif",
]
SAMPLE_MAPPING = {
    "landCover_reclassified.tif": "landcover_reclassified.tif",
    "protected_status_reclassified.tif": "protected_status_reclassified.tif",
}
GOLD_MAPPING = {
    "landCover_reclassified.tif": "landCover_reclassified_gold.tif",
    "protected_status_reclassified.tif": "protected_status_reclassified_gold.tif",
}


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
    for item in src.rglob("*"):
        if not item.is_file():
            continue
        rel = item.relative_to(src)
        target = dest_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        copied += 1
    print(f"✓ Copied {copied} dataset files to {dest_root}")


def prepare(raw: Path, public: Path, private: Path) -> None:
    print("=" * 60)
    print("Preparing ScienceBench Task 53")
    print("Dataset:", DATASET_NAME)
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    source_dir = raw if raw.exists() else _dataset_dir()
    if not source_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {source_dir}")

    _ensure_dir(public)
    _ensure_dir(private)
    _copy_dataset(source_dir, public)

    sample_root = public / 'pred_results'
    sample_root.mkdir(parents=True, exist_ok=True)
    dataset_root = public / DATASET_NAME
    for expected_name, source_name in SAMPLE_MAPPING.items():
        sample_source = dataset_root / source_name
        if not sample_source.exists():
            raise FileNotFoundError(f"Sample raster not found: {sample_source}")
        shutil.copy2(sample_source, sample_root / expected_name)
    print("✓ Created sample submission rasters")

    gold_dir = _gold_dir()
    for expected_name, gold_name in GOLD_MAPPING.items():
        gold_path = gold_dir / gold_name
        if not gold_path.exists():
            raise FileNotFoundError(f"Missing gold raster: {gold_path}")
        shutil.copy2(gold_path, private / gold_name)
    print("✓ Copied gold rasters")

    print("Data preparation completed.")
