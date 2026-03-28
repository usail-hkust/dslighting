"""Data preparation for ScienceBench Task 17 (DrugEx visualization)."""

from __future__ import annotations

from pathlib import Path
import shutil

from PIL import Image

DATA_DIR = None  # set inside prepare()
SOURCE_FILE = None  # set inside prepare()
GOLD_IMAGE = None  # set inside prepare()
EXPECTED_FILENAME = "drugex_vis_pred.png"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_placeholder_png(target: Path, *, width: int, height: int) -> None:
    Image.new("RGBA", (max(1, width), max(1, height)), (255, 255, 255, 255)).save(target, format="PNG")


def prepare(raw: Path, public: Path, private: Path) -> None:
    global DATA_DIR, SOURCE_FILE, GOLD_IMAGE
    DATA_DIR = raw / "papyrus_vis"
    SOURCE_FILE = DATA_DIR / "A2AR_LIGANDS.tsv"
    GOLD_IMAGE = raw / "drugex_vis_gold.png"
    print("=" * 60)
    print("Preparing ScienceBench Task 17: DrugEx visualization")
    print("=" * 60)
    print("Public directory:", public)
    print("Private directory:", private)

    _ensure_dir(public)
    _ensure_dir(private)

    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"Missing dataset file: {SOURCE_FILE}")
    target_file = public / SOURCE_FILE.relative_to(DATA_DIR.parent)
    target_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_FILE, target_file)
    print("✓ Copied A2AR_LIGANDS.tsv to public directory")

    if GOLD_IMAGE.exists():
        with Image.open(GOLD_IMAGE).convert("RGBA") as gold_img:
            _write_placeholder_png(public / "sample_submission.png", width=gold_img.width, height=gold_img.height)
            gold_img.save(private / "result.png", format="PNG")
        print("✓ Created sample_submission.png")
        print("✓ Copied result.png")
    else:
        print("⚠ Gold image not found; creating blank sample_submission.png.")
        _write_placeholder_png(public / "sample_submission.png", width=1, height=1)

    print("Preparation complete. Expected submission file: pred_results/drugex_vis_pred.png")


if __name__ == "__main__":
    raise SystemExit("Use this module via the benchmark preparation tooling.")
