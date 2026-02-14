"""
Data preparation for ScienceBench Task 1: clintox_nn
Dataset: clintox
"""

import pandas as pd
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
    train_df = pd.read_csv(train_file)
    test_df = pd.read_csv(test_file)

    # Write training data as-is (includes labels)
    train_output = train_df.copy()
    train_output.to_csv(public / "clintox_train.csv", index=False)
    print(f"  ✓ Saved: clintox_train.csv ({train_output.shape[0]} rows, {train_output.shape[1]} columns)")

    # Remove any legacy duplicate files that may exist from earlier conversions
    for legacy_name in ["train.csv", "test.csv"]:
        legacy_path = public / legacy_name
        if legacy_path.exists():
            legacy_path.unlink()
            print(f"  ↺ Removed legacy artifact: {legacy_name}")

    # Create sample_submission with expected format
    # The submission should contain: smiles, FDA_APPROVED, CT_TOX
    sample_submission = pd.DataFrame({
        "smiles": test_df["smiles"],
        "FDA_APPROVED": 0.5,  # Probability placeholder
        "CT_TOX": 0.5  # Probability placeholder
    })
    sample_submission.to_csv(public / "sample_submission.csv", index=False)
    print(f"\n✓ Created sample_submission.csv with {len(sample_submission)} rows")

    # Provide a public test file that mirrors the sample submission format
    test_output = pd.DataFrame({
        "smiles": test_df["smiles"],
        "FDA_APPROVED": "",
        "CT_TOX": ""
    })
    test_output.to_csv(public / "clintox_test.csv", index=False)
    print(f"  ✓ Saved: clintox_test.csv ({test_output.shape[0]} rows, {test_output.shape[1]} columns) with original SMILES")

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
