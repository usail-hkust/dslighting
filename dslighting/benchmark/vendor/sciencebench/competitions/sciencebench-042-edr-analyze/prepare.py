"""Data preparation for ScienceBench task 42 (EDR analysis)."""

from __future__ import annotations

import io
import shutil
from pathlib import Path

from PIL import Image


def _default_dataset_dir() -> Path:
    root = Path(__file__).resolve().parents[5]
    return root / "ScienceAgent-bench" / "benchmark" / "datasets" / "biosignals"


def _default_gold_path() -> Path:
    root = Path(__file__).resolve().parents[5]
    return root / "ScienceAgent-bench" / "benchmark" / "eval_programs" / "gold_results" / "EDR_analyze_gold.png"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_placeholder_png(target: Path, *, width: int, height: int) -> None:
    Image.new("RGBA", (max(1, width), max(1, height)), (255, 255, 255, 255)).save(target, format="PNG")


def prepare(raw: Path, public: Path, private: Path) -> None:
    print("=" * 60)
    print("Preparing ScienceBench Task 42")
    print("Dataset: biosignals")
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    data_dir = raw if raw.exists() else _default_dataset_dir()
    if not data_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {data_dir}")

    _ensure_dir(public)
    _ensure_dir(private)

    source_file = data_dir / "bio_eventrelated_100hz.csv"
    if not source_file.exists():
        raise FileNotFoundError(f"Data file not found: {source_file}")
    shutil.copy2(source_file, public / "bio_eventrelated_100hz.csv")
    print("✓ Copied biosignal data")

    gold_path = _default_gold_path()
    if not gold_path.exists():
        raise FileNotFoundError(f"Gold image not found: {gold_path}")
    gold_bytes = gold_path.read_bytes()
    gold_img = Image.open(io.BytesIO(gold_bytes)).convert("RGBA")
    _write_placeholder_png(public / "sample_submission.png", width=gold_img.width, height=gold_img.height)
    print("✓ Created sample_submission.png")

    gold_img.save(private / "result.png", format="PNG")
    print("✓ Copied result.png")

    print("EDR analysis task preparation complete")
