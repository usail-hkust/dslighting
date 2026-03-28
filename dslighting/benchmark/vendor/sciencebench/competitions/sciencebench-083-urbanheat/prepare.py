"""
Data preparation for ScienceBench task 83 (Urban Heat interpolation).
"""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image


DATASET_NAME = "UrbanHeat"
EXPECTED_FILENAME = "interpolated_urban_heat.png"
GOLD_FILENAME = "interpolated_urban_heat_gold.png"


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
    print("Preparing ScienceBench Task 83")
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
        raise FileNotFoundError(f"Gold image not found: {gold_path}")

    _ensure_dir(public)
    _ensure_dir(private)

    _copy_dataset(source_dir, public)
    gold_path = _gold_path()
    if not gold_path.exists():
        raise FileNotFoundError(f"Gold image not found: {gold_path}")

    gold_img = Image.open(gold_path).convert("RGBA")
    _write_placeholder_png(public / "sample_submission.png", width=gold_img.width, height=gold_img.height)
    print("✓ Created sample_submission.png")

    gold_img.save(private / "result.png", format="PNG")
    print("✓ Copied result.png")

    print("Data preparation completed.")
