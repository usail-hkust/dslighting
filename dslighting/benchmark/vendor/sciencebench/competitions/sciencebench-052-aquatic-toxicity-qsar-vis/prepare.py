"""
Data preparation for ScienceBench task 52
Dataset: aquatic_toxicity
"""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image

EXPECTED_FILENAME = "aquatic_toxicity_qsar_vis.png"


def _dataset_dir() -> Path:
    root = Path(__file__).resolve().parents[5]
    return root / "ScienceAgent-bench" / "benchmark" / "datasets" / "aquatic_toxicity"


def _gold_path() -> Path:
    root = Path(__file__).resolve().parents[5]
    return root / "ScienceAgent-bench" / "benchmark" / "eval_programs" / "gold_results" / "aquatic_toxicity_qsar_vis_gold.png"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_placeholder_png(target: Path, *, width: int, height: int) -> None:
    Image.new("RGBA", (max(1, width), max(1, height)), (255, 255, 255, 255)).save(target, format="PNG")


def prepare(raw: Path, public: Path, private: Path) -> None:
    print("=" * 60)
    print("Preparing ScienceBench Task 52")
    print("Dataset: aquatic_toxicity")
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    data_dir = raw if raw.exists() else _dataset_dir()
    if not data_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {data_dir}")

    _ensure_dir(public)
    _ensure_dir(private)

    required = [
        data_dir / "Tetrahymena_pyriformis_OCHEM.sdf",
        data_dir / "Tetrahymena_pyriformis_OCHEM_test_ex.sdf",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing dataset files: " + ", ".join(missing))

    for path in required:
        target = public / path.relative_to(data_dir.parent)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    print("✓ Copied aquatic toxicity SDF files")

    gold_path = _gold_path()
    if not gold_path.exists():
        raise FileNotFoundError(f"Gold image not found: {gold_path}")
    gold_img = Image.open(gold_path).convert("RGBA")
    _write_placeholder_png(public / "sample_submission.png", width=gold_img.width, height=gold_img.height)
    print("✓ Created sample_submission.png")
    gold_img.save(private / "result.png", format="PNG")
    print("✓ Copied result.png")

    print("Aquatic toxicity visualization task preparation complete")


if __name__ == "__main__":
    raise SystemExit("Use this module via the benchmark preparation tooling.")
