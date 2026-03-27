"""
Data preparation for ScienceBench task 29
Dataset: biosignals
"""

import pandas as pd
from pathlib import Path
import shutil


GOLD_FILE = None  # set inside prepare()
EXPECTED_OUTPUT = "bio_eventrelated_100hz_analysis_pred.csv"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


SOURCE_DATASET = "biosignals"


def prepare(raw: Path, public: Path, private: Path):
    """
    Prepare the ScienceAgent task data.

    Args:
        raw: Path to raw data directory (ScienceAgent-bench datasets)
        public: Path to public directory (visible to participants)
        private: Path to private directory (used for grading)
    """
    global GOLD_FILE
    GOLD_FILE = raw / "bio_eventrelated_100hz_analysis_gold.csv"
    print(f"=" * 60)
    print(f"Preparing ScienceBench Task 29")
    print(f"Dataset: biosignals")
    print(f"=" * 60)
    print(f"Raw directory: {raw}")
    print(f"Public directory: {public}")
    print(f"Private directory: {private}")

    _ensure_dir(public)
    _ensure_dir(private)

    # 检查原始数据是否存在
    if not raw.exists():
        print(f"\n⚠ Warning: Raw data directory not found: {raw}")
        print("Creating placeholder files...")
        create_placeholder_files(public, private)
        return

    # 复制所有数据文件到 public
    print(f"\nCopying data files to public directory...")
    file_count = 0
    for file in raw.rglob('*'):
        if file.is_file() and not file.name.startswith('.'):
            rel_path = file.relative_to(raw)
            target = public / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, target)
            file_count += 1
            if file_count <= 10:  # Only print first 10 files
                print(f"  ✓ Copied: {rel_path}")

    if file_count > 10:
        print(f"  ... and {file_count - 10} more files")
    print(f"  Total files copied: {file_count}")

    # 创建 sample_submission 文件
    if GOLD_FILE.exists():
        gold_df = pd.read_csv(GOLD_FILE)
        sample_submission = gold_df.head(min(3, len(gold_df))).copy()
        sample_submission.to_csv(public / "sample_submission.csv", index=False)
        gold_df.to_csv(private / "answer.csv", index=False)
        print("Created sample_submission.csv and answer.csv from gold data")
    else:
        columns = ["Condition", "ECG_Rate_Mean", "RSP_Rate_Mean", "EDA_Peak_Amplitude"]
        sample_submission = pd.DataFrame({col: [] for col in columns})
        sample_submission.to_csv(public / "sample_submission.csv", index=False)
        print("Created empty sample_submission.csv (gold file missing)")

    print(f"\nData preparation completed!")
    print(f"  Public files: {list(public.glob('*'))}")
    print(f"  Private files: {list(private.glob('*'))}")


def create_placeholder_files(public: Path, private: Path):
    """创建占位符文件"""
    # Public
    pd.DataFrame({"info": ["Data not available"]}).to_csv(
        public / "sample_submission.csv", index=False
    )

    # Private
    pd.DataFrame({"info": ["Answer not available"]}).to_csv(
        private / "answer.csv", index=False
    )

    print("Placeholder files created")
