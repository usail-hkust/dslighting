from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from mlebench.utils import read_csv


def _save_split_data(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    public_dir: Path,
    private_dir: Path,
):
    """
    Saves a train/test split to the specified public and private directories,
    maintaining a consistent file structure and naming convention.

    Args:
        train_df (pd.DataFrame): The training dataframe.
        test_df (pd.DataFrame): The testing dataframe with labels.
        public_dir (Path): The directory to save public-facing files.
        private_dir (Path): The directory to save private/ground-truth files.
    """
    # Ensure directories exist
    public_dir.mkdir(exist_ok=True, parents=True)
    private_dir.mkdir(exist_ok=True, parents=True)

    # Make copies to avoid side-effects from ID resetting on the original dataframes
    train_df = train_df.copy()
    test_df = test_df.copy()

    # Reset the 'id' column of train and test, starting at 1
    train_df["id"] = range(1, len(train_df) + 1)
    test_df["id"] = range(1, len(test_df) + 1)

    assert set(train_df["breath_id"]).isdisjoint(
        set(test_df["breath_id"])
    ), "Test set contains breath_ids that are in the train set"

    # Create public test
    test_without_labels = test_df.drop(columns=["pressure"])

    # Create sample submission
    sample_submission = test_without_labels.copy()[["id"]]
    sample_submission["pressure"] = 0

    # Write CSVs with identical filenames for both original and validation splits
    train_df.to_csv(public_dir / "train.csv", index=False, float_format="%.10g")
    test_without_labels.to_csv(public_dir / "test.csv", index=False, float_format="%.10g")
    sample_submission.to_csv(
        public_dir / "sample_submission.csv", index=False, float_format="%.10g"
    )
    test_df.to_csv(private_dir / "test.csv", index=False, float_format="%.10g")

    # Checks
    assert (
        sample_submission.shape[0] == test_without_labels.shape[0]
    ), "Sample submission and new_test should have the same number of rows"
    assert sample_submission.shape[1] == 2, "Sample submission should have 2 columns"
    assert (
        test_without_labels.shape[1] == 7
    ), f"Expected 7 columns in test_without_labels, but got {test_without_labels.shape[1]}"
    assert (
        train_df.shape[1] == 8
    ), f"Expected 8 columns in new_train, but got {train_df.shape[1]}"


def prepare(raw: Path, public: Path, private: Path):

    # Create train, test from train split
    dtypes = {
        "id": "int32",
        "breath_id": "int32",
        "R": "int8",
        "C": "int8",
        "time_step": "float64",
        "u_in": "float64",
        "u_out": "int8",
        "pressure": "float64",
    }

    old_train = read_csv(raw / "train.csv", dtype=dtypes)

    # Group by 'breath_id' and maintain the groups as lists of indices
    groups = [df.index.tolist() for _, df in old_train.groupby("breath_id")]

    # Split the groups into train and test sets such that train and test sets
    # do not contain the same 'breath_id's
    train_groups, test_groups = train_test_split(groups, test_size=0.1, random_state=0)

    # Flatten the list of indices to get indices for train and test sets
    train_idx = [idx for sublist in train_groups for idx in sublist]
    test_idx = [idx for sublist in test_groups for idx in sublist]

    # Create train and test DataFrames using the indices
    new_train = old_train.loc[train_idx]
    new_test = old_train.loc[test_idx]

    # --- Original Output Generation ---
    # This part remains unchanged in its output. The original script's file
    # creation logic is now encapsulated and called here to produce the
    # final competition assets.
    _save_split_data(new_train, new_test, public, private)

    # Check that original total size is preserved
    assert len(old_train) == len(new_train) + len(
        new_test
    ), "New train and test should sum up to the old train size"

    # --- New Validation Set Generation ---

    # Define paths for the new validation split
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # To make the validation set size match the original test set size,
    # we use the number of groups from the original test split as the test_size.
    val_test_group_size = len(test_groups)

    # Split the train_groups again to create a new, smaller training set and a validation set.
    # We use the same random_state for reproducibility.
    train_val_groups, test_val_groups = train_test_split(
        train_groups, test_size=val_test_group_size, random_state=0
    )

    # Flatten the list of indices for the new split
    train_val_idx = [idx for sublist in train_val_groups for idx in sublist]
    test_val_idx = [idx for sublist in test_val_groups for idx in sublist]

    # Create the new train_val and test_val DataFrames from the original data
    train_val = old_train.loc[train_val_idx]
    test_val = old_train.loc[test_val_idx]

    # Save the new validation split using the same helper function to ensure
    # identical file structure and naming in the new `_val` directories.
    _save_split_data(train_val, test_val, public_val, private_val)

    # Check that the validation split correctly partitioned the new_train set
    assert len(new_train) == len(train_val) + len(
        test_val
    ), "train_val and test_val should sum up to the new_train size"