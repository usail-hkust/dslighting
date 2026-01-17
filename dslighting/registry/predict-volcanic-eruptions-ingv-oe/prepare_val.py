import shutil
from pathlib import Path
from typing import Tuple

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from mlebench.utils import read_csv


def _create_split(
    source_df: pd.DataFrame,
    public_path: Path,
    private_path: Path,
    raw_files_dir: Path,
    test_size: float,
    random_state: int,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Splits a dataframe into train and test sets, and creates the corresponding
    directory structure with data files and labels.

    Args:
        source_df: The dataframe to split.
        public_path: The path to the public output directory.
        private_path: The path to the private output directory (for test labels).
        raw_files_dir: The path to the directory containing the raw data files.
        test_size: The proportion of the dataset to allocate to the test split.
        random_state: The seed for the random number generator.

    Returns:
        A tuple containing the new training dataframe and the answers dataframe.
    """
    # Ensure output directories exist
    public_path.mkdir(parents=True, exist_ok=True)
    private_path.mkdir(parents=True, exist_ok=True)

    # Create train, test from the source dataframe
    new_train, answers = train_test_split(
        source_df, test_size=test_size, random_state=random_state
    )

    # Create sample submission
    submission_df = answers.copy()
    submission_df["time_to_eruption"] = 0

    # Checks
    assert len(answers) == len(submission_df), "Answers and submission should have the same length"
    assert not any(
        new_train["segment_id"].isin(answers["segment_id"])
    ), "No segment_id should be in both train and answers"
    assert list(new_train.columns) == [
        "segment_id",
        "time_to_eruption",
    ], "new_train should have columns 'segment_id' and 'time_to_eruption'"
    assert list(submission_df.columns) == [
        "segment_id",
        "time_to_eruption",
    ], "submission_df should have columns 'segment_id' and 'time_to_eruption'"
    assert list(answers.columns) == [
        "segment_id",
        "time_to_eruption",
    ], "answers should have columns 'segment_id' and 'time_to_eruption'"
    assert len(new_train) + len(answers) == len(
        source_df
    ), "The sum of the length of new_train and answers should be equal to the length of source_df"

    # Write CSVs
    answers.to_csv(private_path / "test.csv", index=False)
    new_train.to_csv(public_path / "train.csv", index=False)
    submission_df.to_csv(public_path / "sample_submission.csv", index=False)

    # Copy over files
    (public_path / "test").mkdir(exist_ok=True)
    (public_path / "train").mkdir(exist_ok=True)

    for file_id in tqdm(new_train["segment_id"], desc=f"Copying train files to {public_path.name}"):
        shutil.copyfile(
            src=raw_files_dir / f"{file_id}.csv",
            dst=public_path / "train" / f"{file_id}.csv",
        )

    for file_id in tqdm(answers["segment_id"], desc=f"Copying test files to {public_path.name}"):
        shutil.copyfile(
            src=raw_files_dir / f"{file_id}.csv",
            dst=public_path / "test" / f"{file_id}.csv",
        )

    # Checks on files
    assert len(list(public_path.glob("train/*.csv"))) == len(
        new_train
    ), f"Public train in {public_path.name} should have the same number of files as its train split"
    assert len(list(public_path.glob("test/*.csv"))) == len(
        answers
    ), f"Public test in {public_path.name} should have the same number of files as its answer key"

    return new_train, answers


def prepare(raw: Path, public: Path, private: Path):
    """
    Prepares the dataset by creating two splits:
    1. A standard train/test split for the main competition.
    2. A subsequent train/validation split for model development, created from
       the training set of the first split.
    """
    RANDOM_STATE = 0
    TEST_SIZE_ORIGINAL = 0.1

    # Load the full raw training data manifest
    original_train_df = read_csv(raw / "train.csv")
    raw_files_dir = raw / "train"

    # --- 1. Create the original train/test split for `public` and `private` ---
    # This call produces the primary competition data. Its outputs must remain
    # identical to those of the original script.
    competition_train_df, competition_test_answers = _create_split(
        source_df=original_train_df,
        public_path=public,
        private_path=private,
        raw_files_dir=raw_files_dir,
        test_size=TEST_SIZE_ORIGINAL,
        random_state=RANDOM_STATE,
    )

    # --- 2. Create the new train/validation split for `public_val` and `private_val` ---
    # This call creates a new split from the training data generated above.
    # The new directories will mirror the structure of the originals.
    public_val_path = public.parent / "public_val"
    private_val_path = private.parent / "private_val"

    # Calculate the test size for the second split to ensure the number of samples
    # in the new validation set is the same as in the original test set.
    validation_test_size = len(competition_test_answers) / len(competition_train_df)

    # Create the new split using the same logic and random state.
    # The source data is `competition_train_df`, the training set from the first split.
    _create_split(
        source_df=competition_train_df,
        public_path=public_val_path,
        private_path=private_val_path,
        raw_files_dir=raw_files_dir,
        test_size=validation_test_size,
        random_state=RANDOM_STATE,
    )