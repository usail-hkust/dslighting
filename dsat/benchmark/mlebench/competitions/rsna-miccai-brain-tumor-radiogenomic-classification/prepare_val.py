import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from mlebench.utils import read_csv


def _create_split_files(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    public_dest: Path,
    private_dest: Path,
    raw_data_path: Path,
):
    """
    Helper function to populate public and private directories for a given split.

    This function handles copying images, creating label files, and generating
    a sample submission, ensuring a consistent structure across different data splits.
    """
    public_dest.mkdir(exist_ok=True)
    private_dest.mkdir(exist_ok=True)

    # Copy over images for the training set
    (public_dest / "train").mkdir(exist_ok=True)
    for file_id in train_df["BraTS21ID"]:
        (public_dest / "train" / file_id).mkdir(exist_ok=True)
        shutil.copytree(
            src=raw_data_path / "train" / file_id,
            dst=public_dest / "train" / file_id,
            dirs_exist_ok=True,
        )
    assert len(list(public_dest.glob("train/*"))) == len(
        train_df
    ), "Public train should have the same number of images as the train set"

    # Copy over images for the test set (without labels)
    (public_dest / "test").mkdir(exist_ok=True)
    for file_id in test_df["BraTS21ID"]:
        (public_dest / "test" / file_id).mkdir(exist_ok=True)
        shutil.copytree(
            src=raw_data_path / "train" / file_id,
            dst=public_dest / "test" / file_id,
            dirs_exist_ok=True,
        )
    assert len(list(public_dest.glob("test/*"))) == len(
        test_df
    ), "Public test should have the same number of images as the test set"

    # Create a sample submission file for the public directory
    submission_df = test_df.copy()
    submission_df["MGMT_value"] = 0.5

    # Copy over the final CSV files to their destinations
    train_df.to_csv(public_dest / "train_labels.csv", index=False)
    test_df.to_csv(private_dest / "test.csv", index=False)
    submission_df.to_csv(public_dest / "sample_submission.csv", index=False)


def prepare(raw: Path, public: Path, private: Path):
    # Load the full labeled dataset from the raw directory
    all_labeled_data = read_csv(raw / "train_labels.csv", dtype={"BraTS21ID": str, "MGMT_value": int})

    # --- Original Split (for public/private) ---
    # Create the original train and test splits from the full dataset
    train_df, test_df = train_test_split(all_labeled_data, test_size=0.1, random_state=0)

    # Generate the original public and private directories.
    # The output of this call will be identical to the original script's output.
    _create_split_files(
        train_df=train_df,
        test_df=test_df,
        public_dest=public,
        private_dest=private,
        raw_data_path=raw,
    )

    # --- New Validation Split (for public_val/private_val) ---
    # Define new paths for the validation split, parallel to the original ones
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Create a new train/validation split from the *original training data* (train_df).
    # The splitting logic (test_size, random_state) is intentionally replicated.
    train_val_df, test_val_df = train_test_split(train_df, test_size=0.1, random_state=0)

    # Generate the new public_val and private_val directories using the same helper function.
    # This ensures the directory structure and filenames are identical to the original split.
    _create_split_files(
        train_df=train_val_df,
        test_df=test_val_df,
        public_dest=public_val,
        private_dest=private_val,
        raw_data_path=raw,
    )