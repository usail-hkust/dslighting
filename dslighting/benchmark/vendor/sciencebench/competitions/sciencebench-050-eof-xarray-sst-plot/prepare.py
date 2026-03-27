"""
Data preparation for ScienceBench task 50
Dataset: EOF_xarray_sst
"""

import base64
from pathlib import Path
import shutil
import pandas as pd


EXPECTED_FILENAME = "EOF_xarray_sst.png"
GOLD_IMAGE_PATH = None  # set inside prepare()
SOURCE_DATASET = "EOF_xarray_sst"


def prepare(raw: Path, public: Path, private: Path):
    """Prepare data for image-based ScienceBench task."""
    global GOLD_IMAGE_PATH
    GOLD_IMAGE_PATH = raw / "EOF_xarray_sst_plot_gold.png"
    print("=" * 60)
    print("Preparing ScienceBench Task 50")
    print("Dataset:", SOURCE_DATASET)
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    if not raw.exists():
        print("\n⚠ Warning: Raw data directory not found:", raw)
        public.mkdir(parents=True, exist_ok=True)
        private.mkdir(parents=True, exist_ok=True)
        placeholder = pd.DataFrame([
            {"file_name": EXPECTED_FILENAME, "image_base64": ""}
        ])
        placeholder.to_csv(public / "sample_submission.csv", index=False)
        placeholder.to_csv(private / "answer.csv", index=False)
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

    gold_base64 = ""
    if GOLD_IMAGE_PATH.exists():
        gold_bytes = GOLD_IMAGE_PATH.read_bytes()
        (private / EXPECTED_FILENAME).write_bytes(gold_bytes)
        gold_base64 = base64.b64encode(gold_bytes).decode("utf-8")
        print("✓ Embedded gold image from", GOLD_IMAGE_PATH)
    else:
        print("⚠ Gold image not found; creating empty placeholder.")

    sample_df = pd.DataFrame([
        {"file_name": EXPECTED_FILENAME, "image_base64": ""}
    ])
    sample_df.to_csv(public / "sample_submission.csv", index=False)
    print("✓ Created sample_submission.csv")

    answer_df = pd.DataFrame([
        {"file_name": EXPECTED_FILENAME, "image_base64": gold_base64}
    ])
    answer_df.to_csv(private / "answer.csv", index=False)
    print("✓ Created answer.csv with encoded gold image")

    print("\nData preparation completed!")
