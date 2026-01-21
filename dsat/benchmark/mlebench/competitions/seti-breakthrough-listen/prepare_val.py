import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from mlebench.utils import read_csv


def _create_and_populate_split(
    input_df: pd.DataFrame,
    test_size: float,
    random_state: int,
    raw_data_path: Path,
    public_dest_path: Path,
    private_dest_path: Path,
) -> (pd.DataFrame, pd.DataFrame):
    """
    Splits a dataframe and populates the corresponding public and private directories.

    This function performs a train-test split, copies the necessary .npy files,
    creates the ground truth file for the test set, and a sample submission file.
    It's designed to be called multiple times for creating different data splits
    (e.g., train/test and train/validation).

    Args:
        input_df: The dataframe to be split.
        test_size: The proportion of the dataset to allocate to the test split.
        random_state: The seed used by the random number generator.
        raw_data_path: The path to the raw data directory.
        public_dest_path: The destination path for public-facing files.
        private_dest_path: The destination path for private/solution files.

    Returns:
        A tuple containing the training and testing dataframes from the split.
    """
    # Ensure destination directories exist
    public_dest_path.mkdir(parents=True, exist_ok=True)
    private_dest_path.mkdir(parents=True, exist_ok=True)

    # 1. Create train, test from the input dataframe
    split_train, split_test = train_test_split(
        input_df, test_size=test_size, random_state=random_state
    )

    # 2. Copy over files
    split_train.to_csv(public_dest_path / "train_labels.csv", index=False)
    split_test.to_csv(private_dest_path / "test.csv", index=False)

    # Copy shared, non-data-specific files if they exist
    if (raw_data_path / "old_leaky_data").exists():
        shutil.copytree(
            raw_data_path / "old_leaky_data",
            public_dest_path / "old_leaky_data",
            dirs_exist_ok=True,
        )

    for file_id in tqdm(split_train["id"], desc=f"Copying train files to {public_dest_path.name}"):
        subdir = file_id[0]
        src = raw_data_path / "train" / subdir / f"{file_id}.npy"
        dst = public_dest_path / "train" / subdir / f"{file_id}.npy"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)

    for file_id in tqdm(split_test["id"], desc=f"Copying test files to {public_dest_path.name}"):
        subdir = file_id[0]
        src = raw_data_path / "train" / subdir / f"{file_id}.npy"
        dst = public_dest_path / "test" / subdir / f"{file_id}.npy"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)

    # 3. Create sample submission
    sample_submission = split_test.copy()
    sample_submission["target"] = 0.5  # Overwrite with dummy values
    sample_submission.to_csv(public_dest_path / "sample_submission.csv", index=False)

    # 4. Perform checks for this specific split
    assert len(sample_submission) == len(
        split_test
    ), f"Sample submission length mismatch in {public_dest_path.name}."
    assert not set(split_train["id"]).intersection(
        set(split_test["id"])
    ), f"Overlapping IDs in train/test sets for {public_dest_path.name}."

    train_files = {
        file_path.name
        for file_path in (public_dest_path / "train").rglob("*.npy")
        if file_path.is_file()
    }
    test_files = {
        file_path.name
        for file_path in (public_dest_path / "test").rglob("*.npy")
        if file_path.is_file()
    }

    assert len(train_files) == len(
        split_train
    ), f"Train file count mismatch in {public_dest_path.name}."
    assert len(test_files) == len(
        split_test
    ), f"Test file count mismatch in {public_dest_path.name}."
    assert train_files.isdisjoint(
        test_files
    ), f"Overlapping files in train/test directories for {public_dest_path.name}."

    return split_train, split_test


def prepare(raw: Path, public: Path, private: Path):
    """
    Prepares the data by creating two parallel splits:
    1. A standard train/test split (outputs to `public` and `private`).
    2. A subsequent train/validation split (outputs to `public_val` and `private_val`).
    """
    # Read the full raw training data manifest
    full_train_df = read_csv(raw / "train_labels.csv")

    # --- Stage 1: Create the original train/test split ---
    # This split generates the main competition files in `public` and `private`.
    # The logic and outputs here remain identical to the original script.
    print("--- Creating main train/test split ---")
    new_train, new_test = _create_and_populate_split(
        input_df=full_train_df,
        test_size=0.1,
        random_state=0,
        raw_data_path=raw,
        public_dest_path=public,
        private_dest_path=private,
    )
    print("--- Main train/test split created successfully ---\n")

    # --- Stage 2: Create the new train/validation split ---
    # This split takes the `new_train` set from Stage 1 and splits it again.
    # The outputs go into new, parallel directories (`public_val`, `private_val`).
    # The number of samples in the validation set (`test_val`) is designed to be
    # the same as the number of samples in the original test set (`new_test`).
    print("--- Creating train/validation split ---")
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # To make the new validation set size equal to the original test set size,
    # we calculate the required proportion.
    # test_size = len(new_test) / len(new_train)
    # Since len(new_test) is 0.1 * total and len(new_train) is 0.9 * total,
    # the ratio is 0.1 / 0.9 = 1/9.
    validation_test_size = 1 / 9

    # We reuse the same function, ensuring the logic is identical.
    # The returned dataframes are not needed, as this is the final split.
    _create_and_populate_split(
        input_df=new_train,  # Use the training set from the first split as input
        test_size=validation_test_size,
        random_state=0,  # Use the same random state for consistency
        raw_data_path=raw,
        public_dest_path=public_val,
        private_dest_path=private_val,
    )
    print("--- Train/validation split created successfully ---")