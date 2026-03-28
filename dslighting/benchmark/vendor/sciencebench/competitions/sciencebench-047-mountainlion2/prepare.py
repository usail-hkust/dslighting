"""
Data preparation for ScienceBench task 47
Dataset: MountainLionNew
"""

from __future__ import annotations

from pathlib import Path
import shutil

from PIL import Image


EXPECTED_FILENAME = "distance_to_habitat.png"
GOLD_FILENAME = "distance_to_habitat_gold.png"
SOURCE_DATASET = "MountainLionNew"


def _write_placeholder_png(target: Path, *, width: int, height: int) -> None:
    Image.new("RGBA", (max(1, width), max(1, height)), (255, 255, 255, 255)).save(target, format="PNG")


def prepare(raw: Path, public: Path, private: Path) -> None:
    """Prepare data for image-based ScienceBench task."""
    gold_path = raw / GOLD_FILENAME
    print("=" * 60)
    print("Preparing ScienceBench Task 47")
    print("Dataset:", SOURCE_DATASET)
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    if not raw.exists():
        print("\n⚠ Warning: Raw data directory not found:", raw)
        public.mkdir(parents=True, exist_ok=True)
        private.mkdir(parents=True, exist_ok=True)
        _write_placeholder_png(public / "sample_submission.png", width=1, height=1)
        return

    file_count = 0
    for file in raw.rglob('*'):
        if file.is_file() and not file.name.startswith('.'):
            rel_path = file.relative_to(raw)
            target = public / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, target)
            file_count += 1
            if file_count <= 10:
                print("  ✓ Copied:", rel_path)

    if file_count > 10:
        print("  ... and", file_count - 10, "more files")
    print("  Total files copied:", file_count)

    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    if gold_path.exists():
        with Image.open(gold_path).convert("RGBA") as gold_img:
            _write_placeholder_png(public / "sample_submission.png", width=gold_img.width, height=gold_img.height)
            gold_img.save(private / "result.png", format="PNG")
        print("✓ Created sample_submission.png")
        print("✓ Copied result.png")
    else:
        print("⚠ Gold image not found; creating blank sample_submission.png.")
        _write_placeholder_png(public / "sample_submission.png", width=1, height=1)

    print("\nData preparation completed!")
