import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from mlebench.utils import read_csv

from .classes import CLASSES


def _create_split_files(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    all_annotations_df: pd.DataFrame,
    public_dir: Path,
    private_dir: Path,
    raw_image_dir: Path,
):
    """
    Helper function to populate public and private directories for a given data split.

    This function handles directory creation, image copying, and CSV file generation,
    ensuring a consistent output structure.
    """
    # Ensure output directories exist
    public_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)
    (public_dir / "train").mkdir(exist_ok=True)
    (public_dir / "test").mkdir(exist_ok=True)

    # Filter annotations to only include those for the current training set
    train_uids = train_df["StudyInstanceUID"]
    is_in_train = all_annotations_df["StudyInstanceUID"].isin(train_uids)
    split_train_annotations = all_annotations_df[is_in_train]

    # Copy image files for the current train and test sets
    for file_id in train_df["StudyInstanceUID"]:
        shutil.copyfile(
            src=raw_image_dir / f"{file_id}.jpg",
            dst=public_dir / "train" / f"{file_id}.jpg",
        )

    for file_id in test_df["StudyInstanceUID"]:
        shutil.copyfile(
            src=raw_image_dir / f"{file_id}.jpg",
            dst=public_dir / "test" / f"{file_id}.jpg",
        )

    # Assert that the correct number of images were copied
    assert len(list(public_dir.glob("train/*.jpg"))) == len(
        train_df
    ), f"Expected {len(train_df)} files in {public_dir}/train, got {len(list(public_dir.glob('train/*.jpg')))}"
    assert len(list(public_dir.glob("test/*.jpg"))) == len(
        test_df
    ), f"Expected {len(test_df)} files in {public_dir}/test, got {len(list(public_dir.glob('test/*.jpg')))}"

    # Create a sample submission file for the current test set
    submission_df = test_df[["StudyInstanceUID"] + CLASSES].copy()
    submission_df[CLASSES] = 0

    # Save all required CSV files with the required standard filenames
    train_df.to_csv(public_dir / "train.csv", index=False)
    split_train_annotations.to_csv(public_dir / "train_annotations.csv", index=False)
    submission_df.to_csv(public_dir / "sample_submission.csv", index=False)
    test_df.to_csv(private_dir / "test.csv", index=False)


def prepare(raw: Path, public: Path, private: Path):
    # Load raw data once
    old_train = read_csv(raw / "train.csv")
    old_train_annotations = read_csv(raw / "train_annotations.csv")
    raw_image_dir = raw / "train"

    # --- 1. Original Split: Create main train and test sets ---
    # This split creates the primary train/test sets for the competition.
    # The outputs in `public` and `private` must remain identical to the original script.
    new_train, new_test = train_test_split(old_train, test_size=0.1, random_state=0)

    # Use the helper to create the original public/private directory contents
    _create_split_files(
        train_df=new_train,
        test_df=new_test,
        all_annotations_df=old_train_annotations,
        public_dir=public,
        private_dir=private,
        raw_image_dir=raw_image_dir,
    )

    # --- 2. New Validation Split: Create a validation set from the main train set ---
    # Define paths for the new validation split directories.
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Split the main training set (`new_train`) again to create a smaller
    # training set and a validation set.
    # The validation set (`test_val`) size should be ~10% of the *original* data.
    # new_train size = 0.9 * total. test_val_size = (0.1 * total) / (0.9 * total) = 1/9.
    test_val_size = 1 / 9
    train_val, test_val = train_test_split(
        new_train, test_size=test_val_size, random_state=0
    )

    # Use the same helper to create the new validation directories (`public_val`, `private_val`)
    # The helper ensures filenames and structure are identical to the original outputs.
    _create_split_files(
        train_df=train_val,
        test_df=test_val,
        all_annotations_df=old_train_annotations,
        public_dir=public_val,
        private_dir=private_val,
        raw_image_dir=raw_image_dir,
    )