import shutil
from pathlib import Path
import pandas as pd

from sklearn.model_selection import train_test_split

from mlebench.utils import read_csv


def _process_and_save_split(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    source_images_path: Path,
    public_path: Path,
    private_path: Path,
):
    """
    A helper function to process a single split. It handles directory creation,
    file copying, integrity checks, and writing output CSVs.
    """
    # Create output directories
    public_path.mkdir(exist_ok=True, parents=True)
    private_path.mkdir(exist_ok=True, parents=True)
    (public_path / "test_images").mkdir(exist_ok=True)
    (public_path / "train_images").mkdir(exist_ok=True)

    test_df_without_labels = test_df.drop(columns=["diagnosis"])

    # Copy data for the current split
    for file_id in train_df["id_code"]:
        shutil.copyfile(
            src=source_images_path / f"{file_id}.png",
            dst=public_path / "train_images" / f"{file_id}.png",
        )

    for file_id in test_df_without_labels["id_code"]:
        shutil.copyfile(
            src=source_images_path / f"{file_id}.png",
            dst=public_path / "test_images" / f"{file_id}.png",
        )

    # Check integrity of the files copied for the current split
    assert set(train_df["id_code"]).isdisjoint(
        set(test_df["id_code"])
    ), "Train and test sets should have no shared ids"

    assert len(test_df_without_labels) == len(
        test_df
    ), "Public and Private tests should have equal length"

    assert len(list(public_path.glob("train_images/*.png"))) == len(
        train_df
    ), "Public train images should have the same number of images as the length of train set"

    assert len(list(public_path.glob("test_images/*.png"))) == len(
        test_df_without_labels
    ), "Public test images should have the same number of images as the length of test set"

    train_image_files = set(public_path.glob("train_images/*.png"))
    test_image_files = set(public_path.glob("test_images/*.png"))
    common_files = train_image_files.intersection(test_image_files)
    assert not common_files, f"Images found in both train_images and test_images: {common_files}"

    for file_id in test_df["id_code"]:
        assert (
            public_path / "test_images" / f"{file_id}.png"
        ).exists(), f"Image file for {file_id} not found in test_images"

    for file_id in train_df["id_code"]:
        assert (
            public_path / "train_images" / f"{file_id}.png"
        ).exists(), f"Image file for {file_id} not found in train_images"

    # Create a sample submission file
    submission_df = test_df.copy()
    submission_df["diagnosis"] = 0

    # Write CSVs for the current split
    train_df.to_csv(public_path / "train.csv", index=False)
    test_df.to_csv(private_path / "test.csv", index=False)
    test_df_without_labels.to_csv(public_path / "test.csv", index=False)
    submission_df.to_csv(public_path / "sample_submission.csv", index=False)


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the data in raw into public and private datasets with appropriate test/train splits.
    It also creates a secondary validation split in public_val/private_val directories.
    """

    # --- Stage 1: Create the original train/test split ---
    # This section remains functionally identical to the original script
    # to ensure the contents of `public` and `private` are unchanged.
    old_train = read_csv(raw / "train.csv")
    new_train, new_test = train_test_split(old_train, test_size=0.1, random_state=0)

    # Process and save the original split using the helper function
    _process_and_save_split(
        train_df=new_train,
        test_df=new_test,
        source_images_path=raw / "train_images",
        public_path=public,
        private_path=private,
    )

    # --- Stage 2: Create the new train/validation split ---
    # This split takes the training set from Stage 1 (`new_train`) and splits it again.
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # The test size is 1/9 of the `new_train` data, which is equivalent to 10% of the
    # original total data. This makes the new validation set (`test_val`) have the
    # same size as the original test set (`new_test`).
    train_val, test_val = train_test_split(new_train, test_size=1 / 9, random_state=0)

    # Process and save the new validation split into the _val directories
    _process_and_save_split(
        train_df=train_val,
        test_df=test_val,
        source_images_path=raw / "train_images",
        public_path=public_val,
        private_path=private_val,
    )