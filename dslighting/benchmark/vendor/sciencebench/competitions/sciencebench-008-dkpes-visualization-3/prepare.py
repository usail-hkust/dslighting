"""Data preparation for ScienceBench Task 8 (dkpes visualization)."""

from pathlib import Path
import shutil
import base64
import pandas as pd

DATA_DIR = None  # set inside prepare()
TRAIN_FILE = None  # set inside prepare()
TEST_FILE = None  # set inside prepare()
GOLD_IMAGE = None  # set inside prepare()
EXPECTED_FILENAME = "dkpes_feature_selection_analysis_pred.png"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _encode_image(path: Path) -> str:
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode("utf-8")


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

    sample_df = pd.DataFrame([
        {"file_name": EXPECTED_FILENAME, "image_base64": ""}
    ])
    sample_df.to_csv(public / "sample_submission.csv", index=False)
    print("✓ Wrote sample_submission.csv")

    encoded = _encode_image(GOLD_IMAGE)
    answer_df = pd.DataFrame([
        {"file_name": EXPECTED_FILENAME, "image_base64": encoded}
    ])
    answer_df.to_csv(private / "answer.csv", index=False)
    print("✓ Wrote answer.csv")

    if GOLD_IMAGE.exists():
        shutil.copy2(GOLD_IMAGE, private / GOLD_IMAGE.name)
        print("✓ Copied gold image for reference")

    print("Preparation complete.")


if __name__ == "__main__":
    raise SystemExit("Use this module via the benchmark preparation tooling.")
