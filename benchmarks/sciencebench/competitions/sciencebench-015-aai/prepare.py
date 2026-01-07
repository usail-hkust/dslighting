"""
Data preparation for ScienceBench task 15
Dataset: ames
"""

import pandas as pd
import numpy as np
from pathlib import Path
import shutil
import json


SOURCE_DATASET = "ames"


def prepare(raw: Path, public: Path, private: Path):
    """
    Prepare the ScienceAgent task data.

    Args:
        raw: Path to raw data directory (ScienceAgent-bench datasets)
        public: Path to public directory (visible to participants)
        private: Path to private directory (used for grading)
    """
    print(f"=" * 60)
    print(f"Preparing ScienceBench Task 15")
    print(f"Dataset: ames")
    print(f"=" * 60)
    print(f"Raw directory: {raw}")
    print(f"Public directory: {public}")
    print(f"Private directory: {private}")

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
    # CSV 输出格式
    sample_submission = pd.DataFrame({
        "id": [0, 1, 2],
        "value": [0.0, 0.0, 0.0]
    })
    sample_submission.to_csv(public / "sample_submission.csv", index=False)
    print("Created sample_submission.csv")

    # 创建答案文件（placeholder）
    answer = pd.DataFrame({
        "id": [0, 1, 2],
        "value": [0.0, 0.0, 0.0]
    })
    answer.to_csv(private / "answer.csv", index=False)
    print("Created answer.csv (placeholder)")

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
