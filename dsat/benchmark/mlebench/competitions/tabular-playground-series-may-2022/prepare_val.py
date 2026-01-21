from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from mlebench.utils import read_csv


def _create_and_save_split(
    df_to_split: pd.DataFrame,
    public_path: Path,
    private_path: Path,
    test_size: int,
    random_state: int,
):
    """
    Helper function to perform a data split, re-index, and save all required files.

    Args:
        df_to_split (pd.DataFrame): The dataframe to be split.
        public_path (Path): The directory for public-facing files (train, test features).
        private_path (Path): The directory for private-facing files (test labels).
        test_size (int): The number of samples for the test set.
        random_state (int): The random state for reproducibility.

    Returns:
        pd.DataFrame: The new, smaller training dataframe from the split.
    """
    # Create output directories if they don't exist
    public_path.mkdir(parents=True, exist_ok=True)
    private_path.mkdir(parents=True, exist_ok=True)

    # Perform the split
    train_df, test_df = train_test_split(
        df_to_split, test_size=test_size, random_state=random_state
    )

    # make ids go from 0 to len(train_df) - 1
    train_df.id = np.arange(len(train_df))
    # and from len(train_df) to len(train_df) + len(test_df) - 1
    test_df.id = np.arange(len(train_df), len(train_df) + len(test_df))

    # make downstream files
    test_df_without_labels = test_df.drop(columns=["target"]).copy()
    gold_submission = test_df[["id", "target"]].copy()
    sample_submission = gold_submission.copy()
    sample_submission.target = 0.5

    # save files with required names
    train_df.to_csv(public_path / "train.csv", index=False)
    test_df.to_csv(private_path / "test.csv", index=False)
    test_df_without_labels.to_csv(public_path / "test.csv", index=False)
    gold_submission.to_csv(private_path / "gold_submission.csv", index=False)
    sample_submission.to_csv(public_path / "sample_submission.csv", index=False)

    # run checks for this split
    assert len(train_df) + len(test_df) == len(
        df_to_split
    ), "Expected the sum of the lengths of the new train and test to be equal to the length of the input data."
    assert len(test_df) == len(
        sample_submission
    ), "Expected the length of the private test to be equal to the length of the sample submission."
    assert len(test_df) == len(
        gold_submission
    ), "Expected the length of the private test to be equal to the length of the gold submission."
    assert (
        train_df.columns.to_list() == df_to_split.columns.to_list()
    ), "Expected the columns of the new train to be the same as the columns of the input data."
    assert (
        test_df.columns.to_list() == df_to_split.columns.to_list()
    ), "Expected the columns of the new test to be the same as the columns of the input data"
    assert set(train_df.id).isdisjoint(
        set(test_df.id)
    ), "Expected the ids of the new train and test to be disjoint."

    return train_df


def prepare(raw: Path, public: Path, private: Path):

    old_train = read_csv(raw / "train.csv")

    # --- Stage 1: Create the original train/test split ---
    # This section produces the primary competition data. Its outputs in `public/`
    # and `private/` are guaranteed to be identical to the original script.

    # 900k train, 1.6m - 900k = 700k test; so 700k/1.6m = 0.4375
    # We create our split at 100,000 test samples to get same OOM while keeping as many samples as possible in train
    new_train = _create_and_save_split(
        df_to_split=old_train,
        public_path=public,
        private_path=private,
        test_size=100_000,
        random_state=0,
    )

    # --- Stage 2: Create the new train/validation split ---
    # This section takes the `new_train` set from Stage 1 and splits it again
    # to create a smaller training set and a new validation set.
    # The outputs are saved to parallel `public_val/` and `private_val/` directories.

    # Define paths for the new validation set directories, parallel to the original ones.
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Split `new_train` again using the exact same logic and test size.
    # The resulting `test_val` set will have 100,000 samples, same as the original `test` set.
    # The filenames and directory structure are mirrored for consistency.
    _create_and_save_split(
        df_to_split=new_train,
        public_path=public_val,
        private_path=private_val,
        test_size=100_000,
        random_state=0,
    )