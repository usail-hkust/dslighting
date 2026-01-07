import shutil
from pathlib import Path

# New import required for the data splitting
from sklearn.model_selection import train_test_split

from mlebench.utils import read_csv


def prepare(raw: Path, public: Path, private: Path):
    """
    Prepares the data for the competition.

    This script performs two main operations:
    1.  Processes the original raw data into `public` and `private` directories
        for the official test set, ensuring the output is identical to the
        original script's output.
    2.  Creates a new validation split from the original training data. It splits
        the original `train.csv` into a new, smaller training set (`train_val`)
        and a validation set (`test_val`). The results are saved in parallel
        `public_val` and `private_val` directories with a mirrored file structure.
    """
    # --- Part 1: Original Data Preparation (UNCHANGED OUTPUT) ---
    # This block ensures the 'public' and 'private' directories are populated
    # exactly as they were in the original script.

    # Ensure original output directories exist
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    # Create test and test without labels
    test = read_csv(raw / "test_private_expanded.csv")
    test_without_labels = test[["id", "comment_text"]]

    # Copy over files
    shutil.copy(raw / "test_private_expanded.csv", private / "test.csv")
    shutil.copy(raw / "train.csv", public / "train.csv")
    test_without_labels.to_csv(public / "test.csv", index=False)

    # Create a sample submission file
    submission_df = test_without_labels.copy()
    submission_df = submission_df.drop(columns=["comment_text"])
    submission_df["prediction"] = 0.0
    submission_df.to_csv(public / "sample_submission.csv", index=False)

    # Checks
    assert test.shape == (
        len(test),
        45,
    ), "test.csv should have 45 columns as per raw data"
    assert test_without_labels.shape == (
        len(test_without_labels),
        2,
    ), "test.csv should have 2 columns: id, comment_text"

    assert submission_df.shape == (
        len(test),
        2,
    ), "sample_submission.csv should have 2 columns: id, prediction"

    # --- Part 2: New Validation Set Creation ---
    # This block creates a new split from the original training data to form
    # a new, smaller training set and a validation set. Outputs are saved
    # to 'public_val' and 'private_val' directories.

    # Define and create the new parallel directories for the validation split
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"
    public_val.mkdir(parents=True, exist_ok=True)
    private_val.mkdir(parents=True, exist_ok=True)

    # Load the full original training data, which will be split
    full_train_df = read_csv(raw / "train.csv")

    # The size of the new validation set ('test_val') should be the same
    # as the size of the original test set to replicate the split ratio.
    test_set_size = len(test)

    # Split the full training data into a new training and validation set.
    # A fixed random_state is used to ensure the split is deterministic.
    train_val, test_val = train_test_split(
        full_train_df, test_size=test_set_size, random_state=42
    )

    # Create the public version of the validation set (without labels)
    test_val_without_labels = test_val[["id", "comment_text"]]

    # Save the new split data, mirroring the original file structure and names.
    # private_val contains the ground truth for the new validation set
    test_val.to_csv(private_val / "test.csv", index=False)

    # public_val contains the new smaller training set and the unlabeled validation set
    train_val.to_csv(public_val / "train.csv", index=False)
    test_val_without_labels.to_csv(public_val / "test.csv", index=False)

    # Create a sample submission file for the new validation set
    submission_df_val = test_val_without_labels.copy()
    submission_df_val = submission_df_val.drop(columns=["comment_text"])
    submission_df_val["prediction"] = 0.0
    submission_df_val.to_csv(public_val / "sample_submission.csv", index=False)

    # Add checks for the new validation split dataframes
    assert test_val.shape == (
        len(test_val),
        full_train_df.shape[1],
    ), f"private_val/test.csv should have {full_train_df.shape[1]} columns"
    assert test_val_without_labels.shape == (
        len(test_val_without_labels),
        2,
    ), "public_val/test.csv should have 2 columns: id, comment_text"
    assert submission_df_val.shape == (
        len(test_val),
        2,
    ), "public_val/sample_submission.csv should have 2 columns: id, prediction"
    assert len(train_val) + len(test_val) == len(
        full_train_df
    ), "Split should conserve all data from original train set"