import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from mlebench.utils import read_csv


def _save_split(
    train_df: pd.DataFrame, test_df: pd.DataFrame, public_path: Path, private_path: Path
):
    """
    Saves a given train/test split to the specified public and private directories.

    This helper function ensures a consistent file structure and naming convention
    for any data split.

    Args:
        train_df: The training dataframe.
        test_df: The testing dataframe (with labels).
        public_path: The path to the public output directory.
        private_path: The path to the private output directory.
    """
    # Ensure output directories exist
    public_path.mkdir(parents=True, exist_ok=True)
    private_path.mkdir(parents=True, exist_ok=True)

    # Prepare dataframes for saving
    test_without_labels = test_df.drop(columns=["fare_amount"])
    submission_df = test_df.copy()[["key"]]
    submission_df["fare_amount"] = 11.35  # A sample constant value

    # Write CSVs to public and private directories
    train_df.to_csv(public_path / "train.csv", index=False)
    test_without_labels.to_csv(public_path / "test.csv", index=False)
    submission_df.to_csv(public_path / "sample_submission.csv", index=False)
    test_df.to_csv(private_path / "test.csv", index=False)

    # Run checks to ensure data integrity
    assert set(train_df["key"]).isdisjoint(
        set(test_df["key"])
    ), "Train and test sets share samples!"
    assert test_df.shape[1] == 8, f"Test set should have 8 columns, but has {test_df.shape[1]}"
    assert (
        test_without_labels.shape[1] == 7
    ), f"Test set without labels should have 7 columns, but has {test_without_labels.shape[1]}"
    assert train_df.shape[1] == 8, f"Train set should have 8 columns, but has {train_df.shape[1]}"
    assert (
        submission_df.shape[1] == 2
    ), f"Sample submission should have 2 columns, but has {submission_df.shape[1]}"
    assert (
        submission_df.shape[0] == test_df.shape[0]
    ), f"Sample submission should have {test_df.shape[0]} rows, but has {submission_df.shape[0]}"


def prepare(raw: Path, public: Path, private: Path):
    # Load the raw training data
    old_train = read_csv(raw / "train.csv")

    # --- 1. Create the original train/test split for the main competition files ---
    # This split creates the primary train and test sets.
    # The outputs in `public/` and `private/` will not be changed.
    train_orig, test_orig = train_test_split(old_train, test_size=9914, random_state=0)

    # Save the original split results
    _save_split(
        train_df=train_orig, test_df=test_orig, public_path=public, private_path=private
    )

    # Copy over other files to the original public directory
    shutil.copy(raw / "GCP-Coupons-Instructions.rtf", public / "GCP-Coupons-Instructions.rtf")

    # --- 2. Create the new train/validation split for local validation ---
    # This second split takes the `train_orig` set and splits it again to create
    # a smaller training set and a new validation set (`test_val`).
    # The logic and test size are identical to the first split.
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    train_val, test_val = train_test_split(train_orig, test_size=9914, random_state=0)

    # Save the validation split results to the new directories
    _save_split(
        train_df=train_val, test_df=test_val, public_path=public_val, private_path=private_val
    )

    # 复制相同的文件到 public_val 目录
    shutil.copy(raw / "GCP-Coupons-Instructions.rtf", public_val / "GCP-Coupons-Instructions.rtf")