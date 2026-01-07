import shutil
from pathlib import Path
from typing import Dict

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm.auto import tqdm

from mlebench.utils import extract, read_csv


def _process_and_save_split(
    source_df: pd.DataFrame,
    public_path: Path,
    private_path: Path,
    raw_images_path: Path,
    test_size: float,
    random_state: int,
) -> pd.DataFrame:
    """
    Helper function to perform a data split, save CSVs, and copy image files.

    Args:
        source_df: The DataFrame to split.
        public_path: The public output directory.
        private_path: The private output directory.
        raw_images_path: The path to the source images.
        test_size: The proportion of the dataset to allocate to the test split.
        random_state: The random state for reproducibility.

    Returns:
        The training portion of the split DataFrame.
    """
    # Create output directories
    public_path.mkdir(exist_ok=True, parents=True)
    private_path.mkdir(exist_ok=True, parents=True)

    # Create train, test from the source dataframe
    new_train, answers = train_test_split(
        source_df, test_size=test_size, random_state=random_state
    )

    # Create a sample submission file
    submission_df = answers.copy()
    submission_df["labels"] = "healthy"

    # Checks
    assert len(answers) == len(submission_df), "Answers and submission should have the same length"
    assert not set(new_train["image"]).intersection(
        set(answers["image"])
    ), "new_train and answers should not share any image"
    assert (
        "image" in new_train.columns and "labels" in new_train.columns
    ), "Train DataFrame must have 'image' and 'labels' columns"
    assert (
        "image" in submission_df.columns and "labels" in submission_df.columns
    ), "Sample submission DataFrame must have 'image' and 'labels' columns"
    assert len(new_train) + len(answers) == len(
        source_df
    ), "The combined length of new_train and answers should equal the length of the source dataframe"

    # Write CSVs using the required standard filenames
    answers.to_csv(private_path / "answers.csv", index=False)
    new_train.to_csv(public_path / "train.csv", index=False)
    submission_df.to_csv(public_path / "sample_submission.csv", index=False)

    # Copy files
    (public_path / "test_images").mkdir(exist_ok=True)
    (public_path / "train_images").mkdir(exist_ok=True)

    for file_id in tqdm(new_train["image"], desc=f"Copying Train Images to {public_path.name}"):
        shutil.copyfile(
            src=raw_images_path / f"{file_id}",
            dst=public_path / "train_images" / f"{file_id}",
        )

    for file_id in tqdm(answers["image"], desc=f"Copying Test Images to {public_path.name}"):
        shutil.copyfile(
            src=raw_images_path / f"{file_id}",
            dst=public_path / "test_images" / f"{file_id}",
        )

    # Checks
    assert len(list(public_path.glob("train_images/*.jpg"))) == len(
        new_train
    ), f"Public train images in {public_path.name} should have the same number of images as the train DataFrame"
    assert len(list(public_path.glob("test_images/*.jpg"))) == len(
        answers
    ), f"Public test images in {public_path.name} should have the same number of images as the answers DataFrame"

    return new_train


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the data in raw into public/private datasets for the main competition,
    and creates a parallel validation split in public_val/private_val directories.
    """
    # Define paths for the new validation split
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    old_train = read_csv(raw / "train.csv")
    raw_images_path = raw / "train_images"

    # 1. Create the original train/test split for the competition.
    # This creates the `public` and `private` directories. The outputs here
    # will be identical to the original script's outputs.
    # The returned `competition_train_df` is the 80% training set from this first split.
    competition_train_df = _process_and_save_split(
        source_df=old_train,
        public_path=public,
        private_path=private,
        raw_images_path=raw_images_path,
        test_size=0.2,
        random_state=0,
    )

    # 2. Create the new validation split from the competition's training data.
    # We split the `competition_train_df` (80% of original data) again.
    # To get a validation set of the same size as the original test set (20% of total),
    # we take 25% from this new pool of data (0.25 * 0.8 = 0.2).
    _process_and_save_split(
        source_df=competition_train_df,
        public_path=public_val,
        private_path=private_val,
        raw_images_path=raw_images_path,
        test_size=0.25,
        random_state=0,
    )