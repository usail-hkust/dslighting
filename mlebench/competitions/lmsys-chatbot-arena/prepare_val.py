import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from mlebench.utils import extract, read_csv


def _create_split(
    df_in: pd.DataFrame,
    public_path: Path,
    private_path: Path,
    test_size: float,
    random_state: int,
) -> pd.DataFrame:
    """
    Helper function to perform a data split and write files to specified directories.

    Args:
        df_in: The input DataFrame to split.
        public_path: The directory for public-facing files (train set, test features).
        private_path: The directory for private files (test answers).
        test_size: The proportion of the dataset to allocate to the test set.
        random_state: The seed for the random number generator.

    Returns:
        The DataFrame for the newly created training set.
    """
    # Create output directories if they don't exist
    public_path.mkdir(exist_ok=True, parents=True)
    private_path.mkdir(exist_ok=True, parents=True)

    # Create train, test from the input dataframe
    new_train, answers = train_test_split(
        df_in, test_size=test_size, random_state=random_state
    )
    new_test = answers[["id", "prompt", "response_a", "response_b"]].copy()

    sample_submission = answers[["id"]].copy()
    sample_submission["winner_model_a"] = 0.3333333333333333
    sample_submission["winner_model_b"] = 0.3333333333333333
    sample_submission["winner_tie"] = 0.3333333333333333

    # Checks
    assert len(new_train) + len(new_test) == len(
        df_in
    ), f"New train and test should have the same number of rows as the original dataframe"
    assert set(new_train["id"]).isdisjoint(
        set(new_test["id"])
    ), f"New train and test should have no overlapping ids"
    assert new_test.columns.tolist() == [
        "id",
        "prompt",
        "response_a",
        "response_b",
    ], f"New test should have columns id, prompt, response_a, response_b"
    assert sample_submission.columns.tolist() == [
        "id",
        "winner_model_a",
        "winner_model_b",
        "winner_tie",
    ], f"Sample submission should have columns id, winner_model_a, winner_model_b, winner_tie"
    assert (
        new_train.columns.tolist() == df_in.columns.tolist()
    ), f"New train should have the same columns as the original dataframe"

    # Write CSVs
    answers.to_csv(private_path / "answers.csv", index=False)
    new_train.to_csv(public_path / "train.csv", index=False)
    new_test.to_csv(public_path / "test.csv", index=False)
    sample_submission.to_csv(public_path / "sample_submission.csv", index=False)

    return new_train


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the data in raw into public and private datasets with appropriate test/train splits.
    Also creates a secondary validation split (public_val, private_val) for local testing.
    """

    # --- Stage 1: Create the original competition split (train/test) ---
    # This block generates the primary `public` and `private` directories.
    # Its outputs MUST remain identical to the original script's outputs.
    old_train_df = read_csv(raw / "train.csv")
    train_for_val_split = _create_split(
        df_in=old_train_df,
        public_path=public,
        private_path=private,
        test_size=0.1,
        random_state=0,
    )

    # --- Stage 2: Create the new validation split (train_val/test_val) ---
    # This block takes the training set from Stage 1 and splits it again
    # to create a new, smaller training set and a validation set.
    # The outputs are saved to parallel `public_val` and `private_val` directories.
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Calculate the test_size needed to make the new validation set (`test_val`)
    # have the same number of samples as the original test set from Stage 1.
    # Original test size = 0.1 * total. New train size = 0.9 * total.
    # We need a fraction `p` such that p * (0.9 * total) = 0.1 * total.
    # p = 0.1 / 0.9 = 1/9.
    val_test_size = 1 / 9

    _create_split(
        df_in=train_for_val_split,
        public_path=public_val,
        private_path=private_val,
        test_size=val_test_size,
        random_state=0,  # Use same random state for consistency
    )