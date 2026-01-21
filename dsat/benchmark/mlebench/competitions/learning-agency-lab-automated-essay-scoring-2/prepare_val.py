from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from mlebench.utils import read_csv


def _create_split(
    input_df: pd.DataFrame, test_size: float, random_state: int
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Helper function to perform a single data split and generate associated files."""
    # Create train, test from the input dataframe
    train_df, answers_df = train_test_split(
        input_df, test_size=test_size, random_state=random_state
    )
    test_df = answers_df.drop(columns=["score"])

    sample_submission_df = answers_df[["essay_id"]].copy()
    sample_submission_df["score"] = np.random.RandomState(42).randint(
        1, 7, size=len(sample_submission_df)
    )

    # Checks
    assert set(train_df["essay_id"]).isdisjoint(
        set(test_df["essay_id"])
    ), "Essay IDs in train and test sets are not disjoint"
    assert len(train_df) + len(test_df) == len(
        input_df
    ), f"Train and test sets do not sum to original train set"
    assert len(test_df) == len(
        sample_submission_df
    ), f"Test and sample submission sets do not have the same length"
    assert (
        train_df.columns.tolist() == input_df.columns.tolist()
    ), f"Train set columns do not match original train set, got {train_df.columns.tolist()}"
    assert test_df.columns.tolist() == [
        "essay_id",
        "full_text",
    ], f"Test set columns do not match expected columns, got {test_df.columns.tolist()}"
    assert sample_submission_df.columns.tolist() == [
        "essay_id",
        "score",
    ], f"Sample submission set columns do not match expected columns, got {sample_submission_df.columns.tolist()}"

    return train_df, test_df, answers_df, sample_submission_df


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the data in raw into public and private datasets with appropriate test/train splits.
    Also creates a second, parallel split for validation purposes.
    """

    # Read the original raw data
    old_train = read_csv(raw / "train.csv")

    # --- Stage 1: Create the original train/test split for the main competition ---
    # This block produces the exact same output as the original script.

    # Original train has 17307 rows. Original hidden test has approx 8k rows. We just take 10% of the original train as the test set.
    main_train, main_test, main_answers, main_sample_submission = _create_split(
        input_df=old_train, test_size=0.1, random_state=0
    )

    # Write original CSVs to public/ and private/
    main_answers.to_csv(private / "answers.csv", index=False)
    main_train.to_csv(public / "train.csv", index=False)
    main_test.to_csv(public / "test.csv", index=False)
    main_sample_submission.to_csv(public / "sample_submission.csv", index=False)

    # --- Stage 2: Create a new validation split from the main training data ---
    # This block creates a new set of directories and files for validation.

    # Define and create the new parallel directories for the validation set
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"
    public_val.mkdir(parents=True, exist_ok=True)
    private_val.mkdir(parents=True, exist_ok=True)

    # Calculate the test size for the second split to make the validation test set
    # have the same number of samples as the original test set.
    val_test_size = len(main_test) / len(main_train)

    # Create the new split using the main training data as input
    val_train, val_test, val_answers, val_sample_submission = _create_split(
        input_df=main_train, test_size=val_test_size, random_state=0
    )

    # Write validation CSVs to public_val/ and private_val/ using identical filenames
    val_answers.to_csv(private_val / "answers.csv", index=False)
    val_train.to_csv(public_val / "train.csv", index=False)
    val_test.to_csv(public_val / "test.csv", index=False)
    val_sample_submission.to_csv(public_val / "sample_submission.csv", index=False)