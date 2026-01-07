import shutil
from pathlib import Path

import pandas as pd
import py7zr
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from mlebench.utils import extract, read_csv


def _process_split(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    raw_images_dir: Path,
    public_dir: Path,
    private_dir: Path,
):
    """
    Helper function to process a single data split (train/test).

    This function handles:
    - Creating a sample submission.
    - Writing all necessary CSV files to public and private directories.
    - Copying image files to temporary train/test subdirectories.
    - Zipping the final artifacts.
    - Cleaning up temporary files.
    """
    # Create output directories if they don't exist
    public_dir.mkdir(exist_ok=True, parents=True)
    private_dir.mkdir(exist_ok=True, parents=True)

    # Sample submission
    sample_submission = test_df.copy()
    sample_submission["invasive"] = 0.5

    # Write CSVs
    test_df.to_csv(private_dir / "answers.csv", index=False)
    train_df.to_csv(public_dir / "train_labels.csv", index=False)
    sample_submission.to_csv(private_dir / "sample_submission.csv", index=False)
    sample_submission.to_csv(public_dir / "sample_submission.csv", index=False)

    # Create temporary directories for image copying
    public_train_images_dir = public_dir / "train"
    public_test_images_dir = public_dir / "test"
    public_train_images_dir.mkdir(exist_ok=True)
    public_test_images_dir.mkdir(exist_ok=True)

    # Copy files
    for file_id in tqdm(train_df["name"], desc=f"Copying Train Images to {public_dir.name}"):
        shutil.copyfile(
            src=raw_images_dir / f"{file_id}.jpg",
            dst=public_train_images_dir / f"{file_id}.jpg",
        )

    for file_id in tqdm(test_df["name"], desc=f"Copying Test Images to {public_dir.name}"):
        shutil.copyfile(
            src=raw_images_dir / f"{file_id}.jpg",
            dst=public_test_images_dir / f"{file_id}.jpg",
        )

    # Checks
    assert len(list(public_train_images_dir.glob("*.jpg"))) == len(
        train_df
    ), f"{public_dir.name}/train should have the same number of files as its corresponding train df"
    assert len(list(public_test_images_dir.glob("*.jpg"))) == len(
        test_df
    ), f"{public_dir.name}/test should have the same number of files as its corresponding test df"

    # Zip
    shutil.make_archive(
        str(public_dir / "sample_submission.csv"),
        "zip",
        root_dir=public_dir,
        base_dir="sample_submission.csv",
    )
    shutil.make_archive(
        str(public_dir / "train_labels.csv"),
        "zip",
        root_dir=public_dir,
        base_dir="train_labels.csv",
    )
    with py7zr.SevenZipFile(public_dir / "train.7z", "w") as z:
        z.write(public_train_images_dir, arcname="train")
    with py7zr.SevenZipFile(public_dir / "test.7z", "w") as z:
        z.write(public_test_images_dir, arcname="test")

    # Delete temporary files and directories
    shutil.rmtree(public_train_images_dir)
    shutil.rmtree(public_test_images_dir)
    (public_dir / "sample_submission.csv").unlink()
    (public_dir / "train_labels.csv").unlink()


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the data in raw into public and private datasets with appropriate test/train splits.
    Additionally, creates a second, parallel validation split (public_val/private_val).
    """
    # Define paths for the new validation set
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # extract only what we need
    extract(raw / "train.7z", raw)
    extract(raw / "train_labels.csv.zip", raw)

    # ---- FIRST SPLIT (Original Train/Test) ----
    # Create train, test from train split
    # Original ratio is 1531/(1531+2295) = 0.4
    test_ratio = 0.2
    old_train = read_csv(raw / "train_labels.csv")
    new_train, answers = train_test_split(old_train, test_size=test_ratio, random_state=0)

    # Checks
    assert new_train["name"].is_unique, "new_train should have unique names"
    assert answers["name"].is_unique, "answers should have unique names"
    assert set(new_train["name"]).isdisjoint(
        set(answers["name"])
    ), "new_train and answers should be disjoint"
    assert len(new_train) + len(answers) == len(
        old_train
    ), "new_train and answers together should have the same number of rows as old_train"
    assert (
        new_train.columns.tolist() == old_train.columns.tolist()
    ), "new_train should have the same columns as old_train"
    assert (
        answers.columns.tolist() == old_train.columns.tolist()
    ), "answers should have the same columns as old_train"

    # Process and save the original public/private split
    # This ensures the original outputs are not modified
    _process_split(
        train_df=new_train,
        test_df=answers,
        raw_images_dir=raw / "train",
        public_dir=public,
        private_dir=private,
    )

    # ---- SECOND SPLIT (New Train/Validation) ----
    # Split the `new_train` set again to create a validation set.
    # The new test set (`test_val`) will have the same size as the original test set (`answers`).
    val_test_ratio = len(answers) / len(new_train)
    train_val, test_val = train_test_split(
        new_train, test_size=val_test_ratio, random_state=0
    )

    # Checks for the validation split
    assert set(train_val["name"]).isdisjoint(
        set(test_val["name"])
    ), "train_val and test_val should be disjoint"
    assert len(train_val) + len(test_val) == len(
        new_train
    ), "train_val and test_val together should have the same number of rows as new_train"

    # Process and save the new validation split into parallel directories
    _process_split(
        train_df=train_val,
        test_df=test_val,
        raw_images_dir=raw / "train",
        public_dir=public_val,
        private_dir=private_val,
    )