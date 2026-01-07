import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from mlebench.utils import extract, get_logger, read_csv

logger = get_logger(__name__)


def _create_split(
    input_df: pd.DataFrame,
    test_size: float,
    random_state: int,
    raw_images_path: Path,
    public_path: Path,
    private_path: Path,
    dev_mode: bool = False,
) -> pd.DataFrame:
    """
    Helper function to perform a data split, create necessary files, and organize directories.

    Args:
        input_df: The dataframe to be split.
        test_size: The proportion of the dataset to allocate to the test split.
        random_state: The seed used by the random number generator.
        raw_images_path: Path to the directory containing all source images.
        public_path: The target public directory.
        private_path: The target private directory.
        dev_mode: If True, uses a small sample for faster processing.

    Returns:
        The training portion of the split dataframe.
    """
    # Create train, test from the input dataframe
    locations = input_df["location"].unique()
    train_locations, test_locations = train_test_split(
        locations, test_size=test_size, random_state=random_state
    )

    input_df["split"] = input_df["location"].apply(
        lambda loc: "test" if loc in test_locations else "train"
    )

    train_df = input_df[input_df["split"] == "train"].drop(columns=["split"])
    answers_df = input_df[input_df["split"] == "test"].drop(columns=["split"])

    logger.debug("Train locations: %s", train_locations)
    logger.debug("Test locations: %s", test_locations)
    logger.debug(
        "Test size for this split: %s",
        len(answers_df) / (len(train_df) + len(answers_df)),
    )

    input_df.drop(columns=["split"], inplace=True)  # Drop helper column

    test_df = answers_df.copy().drop(columns=["category_id"])
    gold_submission_df = answers_df.copy()[["id", "category_id"]]
    gold_submission_df.rename(
        columns={"id": "Id", "category_id": "Category"}, inplace=True
    )

    # Make sample submission
    submission_df = test_df.copy()[["id"]]
    submission_df["category_id"] = 0
    submission_df.rename(columns={"id": "Id", "category_id": "Category"}, inplace=True)

    # Checks
    assert set(train_df["id"]).isdisjoint(
        set(test_df["id"])
    ), "train_df and test_df are not disjoint"
    assert len(train_df) + len(test_df) == len(
        input_df
    ), "Length of train_df and test_df should be equal to the length of the input dataframe"
    assert len(answers_df) == len(
        test_df
    ), "Length of answers_df should be equal to the length of test_df"
    assert len(submission_df) == len(
        answers_df
    ), "Length of answers_df should be equal to the length of the sample submission"
    assert (
        input_df.columns.tolist() == train_df.columns.tolist()
    ), f"train_df should have the same columns as the input dataframe: input_df: {input_df.columns.tolist()} != train_df: {train_df.columns.tolist()}"
    assert set(train_df["location"]).isdisjoint(
        set(test_df["location"])
    ), "train_df and test_df should not share any locations"

    # Create directories
    public_path.mkdir(exist_ok=True, parents=True)
    private_path.mkdir(exist_ok=True, parents=True)

    # Write CSVs
    answers_df.to_csv(private_path / "test.csv", index=False)
    gold_submission_df.to_csv(private_path / "answers.csv", index=False)
    train_df.to_csv(public_path / "train.csv", index=False)
    test_df.to_csv(public_path / "test.csv", index=False)
    submission_df.to_csv(public_path / "sample_submission.csv", index=True)

    # Prepare for file copy
    public_train_images = public_path / "train_images"
    public_test_images = public_path / "test_images"
    public_train_images.mkdir(exist_ok=True)
    public_test_images.mkdir(exist_ok=True)

    loop_train_df = train_df.sample(n=100) if dev_mode else train_df
    loop_test_df = test_df.sample(n=100) if dev_mode else test_df

    for file_id in tqdm(loop_train_df["id"], desc=f"Copying train images to {public_path.name}"):
        shutil.copyfile(
            src=raw_images_path / f"{file_id}.jpg",
            dst=public_train_images / f"{file_id}.jpg",
        )

    for file_id in tqdm(loop_test_df["id"], desc=f"Copying test images to {public_path.name}"):
        shutil.copyfile(
            src=raw_images_path / f"{file_id}.jpg",
            dst=public_test_images / f"{file_id}.jpg",
        )

    # Check integrity of the files copied
    assert len(list(public_test_images.glob("*.jpg"))) == len(
        loop_test_df["id"].unique()
    ), f"Public test images in {public_path.name} should have the same number of images as the unique ids in the test set"
    assert len(list(public_train_images.glob("*.jpg"))) == len(
        loop_train_df["id"].unique()
    ), f"Public train images in {public_path.name} should have the same number of images as the unique ids in the train set"

    # Zip up image directories and delete non-zipped files
    shutil.make_archive(
        public_path / "train_images", "zip", public_train_images
    )
    shutil.make_archive(public_path / "test_images", "zip", public_test_images)
    shutil.rmtree(public_train_images)
    shutil.rmtree(public_test_images)

    return train_df


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the data in raw into public and private datasets with appropriate test/train splits.
    Also creates a secondary validation split in public_val/private_val directories.
    """
    dev_mode = False
    test_size = 0.1
    random_state = 8  # We target a 44% test set size, we have empirically trialed seeds and landed on 8 to achieve this

    # --- Setup and Initial Data Extraction ---
    old_train = read_csv(raw / "train.csv")
    raw_images_path = raw / "train_images"
    raw_images_path.mkdir(exist_ok=True)
    logger.info("Extracting raw images...")
    extract(raw / "train_images.zip", raw_images_path)
    assert len(list(raw_images_path.glob("*.jpg"))) == len(
        old_train["id"].unique()
    ), f"Raw train images should have the same number of images as the unique ids in the old train set, but got {len(list(raw_images_path.glob('*.jpg')))} files and {len(old_train['id'].unique())} ids"

    # --- First Split (Original Public/Private) ---
    # This creates the main competition data. The outputs in `public` and `private`
    # will be identical to the original script's output.
    logger.info("Creating original train/test split for competition...")
    train_from_first_split = _create_split(
        input_df=old_train,
        test_size=test_size,
        random_state=random_state,
        raw_images_path=raw_images_path,
        public_path=public,
        private_path=private,
        dev_mode=dev_mode,
    )

    # --- Second Split (New Validation Set) ---
    # This takes the training data from the first split and splits it again
    # to create a new, smaller training set and a validation set.
    # The output structure in `public_val` and `private_val` mirrors the original.
    logger.info("Creating validation train/test split for local development...")
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"
    _create_split(
        input_df=train_from_first_split,
        test_size=test_size,
        random_state=random_state,  # Use same params to replicate splitting logic
        raw_images_path=raw_images_path,
        public_path=public_val,
        private_path=private_val,
        dev_mode=dev_mode,
    )

    # Clean up the extracted raw images directory
    logger.info("Cleaning up extracted raw images...")
    shutil.rmtree(raw_images_path)
    logger.info("Data preparation complete.")