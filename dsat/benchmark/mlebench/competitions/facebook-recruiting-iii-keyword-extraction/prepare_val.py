from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from mlebench.utils import extract, get_logger, read_csv

logger = get_logger(__name__)


def _create_dataset_split(
    source_df: pd.DataFrame, public_dir: Path, private_dir: Path
) -> None:
    """
    Splits a source dataframe and saves the resulting files to public and private dirs.

    This helper function encapsulates the logic for:
    1. Splitting data into train/test sets.
    2. Creating public (unlabeled) and private (labeled) test sets.
    3. Saving all files (train.csv, test.csv, sample_submission.csv) to the
       specified directories with a consistent naming scheme.
    """
    # Create directories if they don't exist
    public_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)

    # Split the source dataframe
    train_split, test_split = train_test_split(
        source_df, test_size=0.1, random_state=0
    )
    test_split_without_labels = test_split.drop(columns=["Tags"])
    sample_submission = test_split_without_labels.copy()
    sample_submission["Tags"] = "javascript c# python php java"

    # Copy over files to private and public directories
    logger.info(f"Copying files to {private_dir} and {public_dir}.")

    train_split.to_csv(public_dir / "train.csv", index=False)
    test_split_without_labels.to_csv(public_dir / "test.csv", index=False)
    sample_submission.to_csv(public_dir / "sample_submission.csv", index=False)
    test_split.to_csv(private_dir / "test.csv", index=False)

    # Sanity checks
    logger.info(f"Performing sanity checks for {public_dir.name}.")

    assert len(test_split_without_labels) == len(
        test_split
    ), f"Expected {len(test_split)} public test samples, got {len(test_split_without_labels)}."
    assert len(source_df) == len(train_split) + len(
        test_split
    ), f"Mismatch in number of samples! Expected {len(source_df)} samples, got {len(train_split) + len(test_split)}."
    assert len(sample_submission) == len(
        test_split
    ), f"Expected {len(test_split)} public test samples, got {len(sample_submission)}."


def prepare(raw: Path, public: Path, private: Path) -> None:
    extract(raw / "Train.zip", raw)

    # Read the full original training dataset
    old_train = read_csv(raw / "Train.csv", dtype={"Id": str, "Tags": str})

    # --- Original Data Split (public/private) ---
    # This block creates the main train/test split. Its outputs in the `public`
    # and `private` directories will remain identical to the original script.
    logger.info(
        "Creating original train/test split for public and private directories."
    )
    _create_dataset_split(source_df=old_train, public_dir=public, private_dir=private)

    # --- New Validation Data Split (public_val/private_val) ---
    # This block creates a new, independent validation split. It takes the
    # training set from the *first* split and splits it again, creating a
    # smaller training set and a validation set.
    logger.info(
        "Creating new train/validation split for public_val and private_val directories."
    )
    # Define the new output directories, parallel to the original ones.
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # We must use the training set from the first split as the source for the second.
    train_from_first_split, _ = train_test_split(
        old_train, test_size=0.1, random_state=0
    )

    # Create the second split and save to the new _val directories.
    _create_dataset_split(
        source_df=train_from_first_split,
        public_dir=public_val,
        private_dir=private_val,
    )