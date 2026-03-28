"""
Data preparation for ScienceBench task 63.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image

DATASET_NAME = "biosignals"
EXPECTED_FILES = [
    "bio_ecg_plot.png",
    "bio_rsp_plot.png",
]
GOLD_MAPPING = {
    "bio_ecg_plot.png": "bio_ecg_plot_gold.png",
    "bio_rsp_plot.png": "bio_rsp_plot_gold.png",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _dataset_dir() -> Path:
    return _repo_root() / "ScienceAgent-bench" / "benchmark" / "datasets" / DATASET_NAME


def _gold_dir() -> Path:
    return _repo_root() / "ScienceAgent-bench" / "benchmark" / "eval_programs" / "gold_results"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_placeholder_png(target: Path, *, width: int, height: int) -> None:
    Image.new("RGBA", (max(1, width), max(1, height)), (255, 255, 255, 255)).save(target, format="PNG")


def _copy_dataset(src: Path, public: Path) -> None:
    dest_root = public / DATASET_NAME
    counter = 0
    for item in src.rglob("*"):
        if not item.is_file():
            continue
        rel = item.relative_to(src)
        target = dest_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        counter += 1
    print(f"✓ Copied {counter} dataset file(s) to {dest_root}")


def prepare(raw: Path, public: Path, private: Path) -> None:
    print("=" * 60)
    print("Preparing ScienceBench Task 63")
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

    sample_root = public / "pred_results"
    sample_root.mkdir(parents=True, exist_ok=True)

    gold_dir = _gold_dir()
    for filename, gold_name in GOLD_MAPPING.items():
        gold_path = gold_dir / gold_name
        if not gold_path.exists():
            raise FileNotFoundError(f"Missing gold image: {gold_path}")
        target = private / gold_path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(gold_path, target)
        gold_img = Image.open(gold_path).convert("RGBA")
        _write_placeholder_png(sample_root / filename, width=gold_img.width, height=gold_img.height)
    print("✓ Created placeholder prediction directory in public/pred_results")
    print("✓ Copied gold images")

    print("Data preparation completed.")
