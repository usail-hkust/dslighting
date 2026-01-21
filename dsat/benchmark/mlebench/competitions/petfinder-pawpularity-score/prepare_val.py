import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm.auto import tqdm

from mlebench.utils import read_csv


def _process_split(
    source_df: pd.DataFrame,
    public_dir: Path,
    private_dir: Path,
    raw_images_dir: Path,
    test_size: float,
    random_state: int,
):
    """
    Processes a single data split, creating train/test sets and associated files.

    This helper function encapsulates the logic for:
    1. Splitting a dataframe into train and test sets.
    2. Creating public and private directories.
    3. Saving train.csv, test.csv (public), test.csv (private), and sample_submission.csv.
    4. Copying the corresponding images.
    5. Running assertions to verify the split.

    Args:
        source_df (pd.DataFrame): The dataframe to be split.
        public_dir (Path): The public output directory.
        private_dir (Path): The private output directory.
        raw_images_dir (Path): The directory containing the source raw images.
        test_size (float): The proportion of the dataset to allocate to the test split.
        random_state (int): The random state for reproducibility.

    Returns:
        pd.DataFrame: The train portion of the split dataframe.
    """
    # Create output directories
    public_dir.mkdir(exist_ok=True, parents=True)
    private_dir.mkdir(exist_ok=True, parents=True)

    # Perform the split
    train_df, test_df = train_test_split(
        source_df, test_size=test_size, random_state=random_state
    )

    test_df_without_labels = test_df.drop(columns=["Pawpularity"])

    # Create a sample submission file
    np_rng = np.random.default_rng(random_state)
    sample_submission = test_df[["Id", "Pawpularity"]].copy()
    sample_submission["Pawpularity"] = np_rng.uniform(1, 100, len(sample_submission)).round(2)

    # Save CSV files
    train_df.to_csv(public_dir / "train.csv", index=False)
    test_df.to_csv(private_dir / "test.csv", index=False)
    test_df_without_labels.to_csv(public_dir / "test.csv", index=False)
    sample_submission.to_csv(public_dir / "sample_submission.csv", index=False)

    # Copy train images
    (public_dir / "train").mkdir(exist_ok=True)
    for img_id in tqdm(
        train_df["Id"], desc=f"Copying train images to {public_dir.name}", total=len(train_df)
    ):
        shutil.copy(raw_images_dir / f"{img_id}.jpg", public_dir / "train" / f"{img_id}.jpg")

    # Copy test images
    (public_dir / "test").mkdir(exist_ok=True)
    for img_id in tqdm(
        test_df_without_labels["Id"],
        desc=f"Copying test images to {public_dir.name}",
        total=len(test_df_without_labels),
    ):
        shutil.copy(raw_images_dir / f"{img_id}.jpg", public_dir / "test" / f"{img_id}.jpg")

    # checks
    assert len(train_df) + len(test_df) == len(
        source_df
    ), "Train and test length should sum to the source df length"
    assert len(sample_submission) == len(
        test_df
    ), "Sample submission should have the same length as the test set"
    assert (
        train_df.columns.tolist() == source_df.columns.tolist()
    ), "Train columns should match source columns"
    assert (
        test_df_without_labels.columns.tolist() == train_df.columns.tolist()[:-1]
    ), "Public test columns should match train columns, minus the target column"
    assert (
        test_df.columns.tolist() == train_df.columns.tolist()
    ), "Private test columns should match train columns"
    assert sample_submission.columns.tolist() == [
        "Id",
        "Pawpularity",
    ], "Sample submission columns should be Id, Pawpularity"
    assert set(train_df["Id"]).isdisjoint(
        set(test_df["Id"])
    ), "Train and test ids should not overlap"
    assert len(list((public_dir / "train").glob("*.jpg"))) == len(
        train_df
    ), "Train images should match the train set"
    assert len(list((public_dir / "test").glob("*.jpg"))) == len(
        test_df
    ), "Test images should match the test set"

    return train_df


def prepare(raw: Path, public: Path, private: Path):

    old_train = read_csv(raw / "train.csv")
    raw_images_dir = raw / "train"

    # --- First Split: Create the original train/test sets ---
    # This split creates the main `public` and `private` directories.
    # Its outputs must remain identical to the original script.
    # Original ratio: 6800/(9912 + 6800) = ~ 0.41 test_size
    # We use 0.1 ratio to avoid taking out too many samples from train
    original_test_size = 0.1
    train_from_first_split = _process_split(
        source_df=old_train,
        public_dir=public,
        private_dir=private,
        raw_images_dir=raw_images_dir,
        test_size=original_test_size,
        random_state=0,
    )

    # --- Second Split: Create the new validation sets from the first split's train set ---
    # Define new paths for the validation set outputs.
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Calculate the test size for the second split to make the new test_val set
    # have approximately the same size as the original test set.
    # size(test_val) = size(test_original)
    # test_size_val * size(train_from_first_split) = original_test_size * size(old_train)
    # test_size_val * (1 - original_test_size) * size(old_train) = original_test_size * size(old_train)
    # test_size_val = original_test_size / (1 - original_test_size)
    val_test_size = original_test_size / (1 - original_test_size)

    # This split creates `public_val` and `private_val` directories.
    # The random_state is kept the same for consistency.
    _process_split(
        source_df=train_from_first_split,
        public_dir=public_val,
        private_dir=private_val,
        raw_images_dir=raw_images_dir,
        test_size=val_test_size,
        random_state=0,
    )