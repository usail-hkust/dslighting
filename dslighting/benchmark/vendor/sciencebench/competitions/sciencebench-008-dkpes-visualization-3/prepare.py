"""Data preparation for ScienceBench Task 8 (dkpes visualization)."""

from __future__ import annotations

from pathlib import Path
import shutil

from PIL import Image

DATA_DIR = None  # set inside prepare()
TRAIN_FILE = None  # set inside prepare()
TEST_FILE = None  # set inside prepare()
GOLD_IMAGE = None  # set inside prepare()
EXPECTED_FILENAME = "dkpes_feature_selection_analysis_pred.png"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_placeholder_png(target: Path, *, width: int, height: int) -> None:
    Image.new("RGBA", (max(1, width), max(1, height)), (255, 255, 255, 255)).save(target, format="PNG")


def prepare(raw: Path, public: Path, private: Path) -> None:
    global DATA_DIR, TRAIN_FILE, TEST_FILE, GOLD_IMAGE
    DATA_DIR = raw / "dkpes"
    TRAIN_FILE = DATA_DIR / "dkpes_train.csv"
    TEST_FILE = DATA_DIR / "dkpes_test.csv"
    GOLD_IMAGE = raw / "dkpes_feature_selection_analysis_gold.png"
    print("=" * 60)
    print("Preparing ScienceBench Task 8: dkpes visualization")
    print("=" * 60)
    print("Public directory:", public)
    print("Private directory:", private)

    _ensure_dir(public)
    _ensure_dir(private)

    if not TRAIN_FILE.exists() or not TEST_FILE.exists():
        raise FileNotFoundError("DKPES dataset files not found.")

    shutil.copy2(TRAIN_FILE, public / TRAIN_FILE.name)
    shutil.copy2(TEST_FILE, public / TEST_FILE.name)
    print("✓ Copied dkpes_train.csv and dkpes_test.csv")

    if GOLD_IMAGE.exists():
        with Image.open(GOLD_IMAGE).convert("RGBA") as gold_img:
            _write_placeholder_png(public / "sample_submission.png", width=gold_img.width, height=gold_img.height)
            gold_img.save(private / "result.png", format="PNG")
        print("✓ Created sample_submission.png")
        print("✓ Copied result.png")
    else:
        print("⚠ Gold image not found; creating blank sample_submission.png.")
        _write_placeholder_png(public / "sample_submission.png", width=1, height=1)

    print("Preparation complete.")


if __name__ == "__main__":
    raise SystemExit("Use this module via the benchmark preparation tooling.")
