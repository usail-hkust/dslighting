"""Data preparation for ScienceBench Task 17 (DrugEx visualization)."""

from pathlib import Path
import shutil
import base64
import pandas as pd

DATA_DIR = None  # set inside prepare()
SOURCE_FILE = None  # set inside prepare()
GOLD_IMAGE = None  # set inside prepare()
EXPECTED_FILENAME = "drugex_vis_pred.png"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _encode_image(path: Path) -> str:
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode("utf-8")


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

    print("Preparation complete. Expected submission file: pred_results/drugex_vis_pred.png")


if __name__ == "__main__":
    raise SystemExit("Use this module via the benchmark preparation tooling.")
