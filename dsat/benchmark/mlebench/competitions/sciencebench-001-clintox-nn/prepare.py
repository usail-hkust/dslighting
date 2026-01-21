"""
Data preparation for ScienceBench Task 1: clintox_nn
Dataset: clintox
"""

import pandas as pd
import numpy as np
from pathlib import Path
import shutil


def prepare(raw: Path, public: Path, private: Path):
    """
    Prepare the clintox task data.

    Args:
        raw: Path to raw data directory (/path/to/ScienceAgent-bench/benchmark/datasets/clintox)
        public: Path to public directory (visible to participants)
        private: Path to private directory (used for grading)
    """
    print(f"=" * 60)
    print(f"Preparing ScienceBench Task 1: clintox_nn")
    print(f"=" * 60)
    print(f"Raw directory: {raw}")
    print(f"Public directory: {public}")
    print(f"Private directory: {private}")

    # Source dataset path
    source_dir = Path("/path/to/ScienceAgent-bench/benchmark/datasets/clintox")

    if not source_dir.exists():
        raise FileNotFoundError(f"Source dataset not found: {source_dir}")

    # Copy training and test data to public
    train_file = source_dir / "clintox_train.csv"
    test_file = source_dir / "clintox_test.csv"

    if not train_file.exists() or not test_file.exists():
        raise FileNotFoundError(f"Required data files not found in {source_dir}")

    print(f"\nCopying data files to public directory...")
    shutil.copy2(train_file, public / "clintox_train.csv")
    shutil.copy2(test_file, public / "clintox_test.csv")
    print(f"  ✓ Copied: clintox_train.csv")
    print(f"  ✓ Copied: clintox_test.csv")

    # Read test file to get structure
    test_df = pd.read_csv(test_file)

    # Create sample_submission with expected format
    # The submission should contain: smiles, FDA_APPROVED, CT_TOX
    sample_submission = pd.DataFrame({
        "smiles": test_df["smiles"],
        "FDA_APPROVED": 0.5,  # Probability placeholder
        "CT_TOX": 0.5  # Probability placeholder
    })
    sample_submission.to_csv(public / "sample_submission.csv", index=False)
    print(f"\n✓ Created sample_submission.csv with {len(sample_submission)} rows")

    # Load gold results for answer
    gold_file = Path("/path/to/ScienceAgent-bench/benchmark/eval_programs/gold_results/clintox_gold.csv")
    if gold_file.exists():
        gold_df = pd.read_csv(gold_file)
        gold_df.to_csv(private / "answer.csv", index=False)
        print(f"✓ Created answer.csv with {len(gold_df)} rows from gold results")
    else:
        # If gold file doesn't exist, create placeholder
        print(f"⚠ Warning: Gold results not found at {gold_file}")
        answer = sample_submission.copy()
        answer.to_csv(private / "answer.csv", index=False)
        print(f"✓ Created placeholder answer.csv")

    print(f"\nData preparation completed!")
    print(f"  Public files: {sorted([f.name for f in public.glob('*')])}")
    print(f"  Private files: {sorted([f.name for f in private.glob('*')])}")
