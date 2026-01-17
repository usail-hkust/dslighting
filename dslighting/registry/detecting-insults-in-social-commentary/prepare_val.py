import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from mlebench.utils import read_csv


def _create_split_files(
    train_df: pd.DataFrame,
    test_df_with_solutions: pd.DataFrame,
    public_dir: Path,
    private_dir: Path,
):
    """
    Helper function to create the standard file structure for a given data split.

    This function encapsulates the logic for generating:
    - public/train.csv
    - public/test.csv (unlabeled)
    - public/sample_submission_null.csv
    - private/test.csv (labeled, ground truth)
    - private/gold_submission.csv
    """
    # Create directories if they don't exist
    public_dir.mkdir(exist_ok=True)
    private_dir.mkdir(exist_ok=True)

    # Save the training data
    train_df.to_csv(public_dir / "train.csv", index=False)

    # Save the full test set with solutions to the private directory
    test_df_with_solutions.to_csv(private_dir / "test.csv", index=False)

    # Create the gold submission from the private test set
    gold_submission = test_df_with_solutions[["Insult", "Date", "Comment"]].copy()
    gold_submission.to_csv(private_dir / "gold_submission.csv", index=False)

    # Create the public test set by dropping the label
    public_test = gold_submission.drop(columns=["Insult"]).copy()
    public_test.to_csv(public_dir / "test.csv", index=False)

    # Create a sample submission with null labels
    sample_submission = gold_submission.copy()
    sample_submission["Insult"] = 0
    sample_submission.to_csv(public_dir / "sample_submission_null.csv", index=False)


def prepare(raw: Path, public: Path, private: Path):
    # Load the original, pre-split data from the raw directory
    original_train_df = read_csv(raw / "train.csv")
    original_test_df = read_csv(raw / "test_with_solutions.csv")

    # --- Part 1: Generate the original public/private split ---
    # This block uses the original data to create the competition's primary
    # train/test split, ensuring the output is identical to the original script.
    _create_split_files(original_train_df, original_test_df, public, private)

    # --- Part 2: Generate the new validation split ---
    # This block creates a new split for local validation. It takes the original
    # training data and splits it again, creating a new, smaller training set
    # and a validation set. The outputs are saved to parallel directories.

    # Define paths for the new validation set directories
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Split the original training data to create a new train and validation set.
    # The size of the validation set is chosen to be the same as the original test set.
    # We stratify on the 'Insult' column to maintain label distribution.
    train_val_df, test_val_df = train_test_split(
        original_train_df,
        test_size=len(original_test_df),
        random_state=42,
        stratify=original_train_df["Insult"],
    )

    # Use the same helper function to create the files for the validation split,
    # ensuring an identical directory structure and naming convention.
    _create_split_files(train_val_df, test_val_df, public_val, private_val)

    # --- Final Checks ---
    # checks for the original split
    public_train = read_csv(public / "train.csv")
    public_test = read_csv(public / "test.csv")
    private_test = read_csv(private / "test.csv")
    sample_submission = read_csv(public / "sample_submission_null.csv")
    gold_submission = read_csv(private / "gold_submission.csv")

    assert public_train.columns.to_list() == [
        "Insult",
        "Date",
        "Comment",
    ], "Train columns should be Insult, Date, Comment"
    assert public_test.columns.to_list() == [
        "Date",
        "Comment",
    ], "Test columns should be Date, Comment"
    assert sample_submission.columns.to_list() == [
        "Insult",
        "Date",
        "Comment",
    ], "Sample submission columns should be Insult, Date, Comment"
    assert gold_submission.columns.to_list() == [
        "Insult",
        "Date",
        "Comment",
    ], "Gold submission columns should be Insult, Date, Comment"
    assert private_test.columns.to_list() == [
        "Insult",
        "Date",
        "Comment",
        "Usage",
    ], "Private test columns should be Insult, Date, Comment, Usage"

    assert set(public_train["Comment"]).isdisjoint(
        set(public_test["Comment"])
    ), "None of the test comments should be in the train comments"
    assert public_test.equals(
        private_test.drop(columns=["Insult", "Usage"])
    ), "Public test should be identical to private test, modulo the Insult and Usage columns"
    assert set(public_test["Comment"]) == set(
        sample_submission["Comment"]
    ), "Public test and sample submission should have the same Comments"
    assert set(public_test["Comment"]) == set(
        gold_submission["Comment"]
    ), "Public test and gold submission should have the same Comments"