import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from mlebench.utils import read_csv


def _get_consensus_annotation(answers, inspect_duplicates=False):
    """
    In the original train, there can be multiple annotations of the same image_id, class_id pair. (Different radiologists draw the bounding boxes differently for the same finding)

    In the original test, there is only one annotation per image_id, class_id pair. The original test set is labeled by consensus of 5 radiologists. (Source: https://www.kaggle.com/competitions/vinbigdata-chest-xray-abnormalities-detection/discussion/207969#1134645)

    We simulate consensus by taking the first annotation for each image_id, class_id pair.
    """

    if inspect_duplicates:
        duplicates = answers[answers.duplicated(subset=["image_id", "class_id"], keep=False)]
        duplicates = duplicates.sort_values(by=["image_id", "class_id"])
        duplicates.to_csv("duplicates.csv", index=False)

    answers = answers.groupby(by=["image_id", "class_id"]).first().reset_index()
    return answers


def _create_split_files(
    train_df: pd.DataFrame,
    answers_df: pd.DataFrame,
    train_image_ids: list,
    test_image_ids: list,
    public_path: Path,
    private_path: Path,
    raw_images_path: Path,
    dev: bool = False,
):
    """
    Helper function to process and save a single train/test split to the specified paths.
    This encapsulates the logic for creating submissions, writing CSVs, and copying image files.
    """
    public_path.mkdir(parents=True, exist_ok=True)
    private_path.mkdir(parents=True, exist_ok=True)

    # Create sample submission for the test set
    sample_submission = pd.DataFrame(
        {
            "image_id": test_image_ids,
            "PredictionString": "14 1 0 0 1 1",  # As per the original sample submission
        }
    )

    # Reformat answers
    answers = _get_consensus_annotation(answers_df)
    # Filling in missing values for when there is no finding (class_id = 14)
    answers = answers.fillna(0)
    answers.loc[answers["class_id"] == 14, ["x_max", "y_max"]] = 1.0

    # Create gold submission
    gold = answers[["image_id", "class_id", "x_min", "y_min", "x_max", "y_max"]].copy()
    # Create individual prediction strings
    gold.loc[:, "PredictionString"] = gold.apply(
        lambda row: f"{row['class_id']} 1.0 {row['x_min']} {row['y_min']} {row['x_max']} {row['y_max']}",
        axis=1,  # 1.0 is the confidence score
    )
    # Group by image_id and concatenate prediction strings
    gold = gold.groupby("image_id")["PredictionString"].agg(" ".join).reset_index()
    gold = gold.reset_index(drop=True)

    # Checks for this split
    assert len(set(train_df["image_id"])) == len(
        train_image_ids
    ), f"Number of unique image_ids in train_df does not match the provided list for {public_path.name}"
    assert len(set(answers["image_id"])) == len(
        test_image_ids
    ), f"Number of unique image_ids in answers does not match the provided list for {public_path.name}"
    assert set(train_df["image_id"]).isdisjoint(
        set(answers["image_id"])
    ), f"image_id is not disjoint between train and test sets for {public_path.name}"
    assert len(sample_submission) == len(
        set(answers["image_id"])
    ), f"Length of sample submission is incorrect for {public_path.name}"
    assert len(gold) == len(
        set(answers["image_id"])
    ), f"Length of gold submission is incorrect for {public_path.name}"

    # Write CSVs
    train_df.to_csv(public_path / "train.csv", index=False)
    sample_submission.to_csv(public_path / "sample_submission.csv", index=False)
    answers.to_csv(private_path / "answers.csv", index=False)
    gold.to_csv(private_path / "gold_submission.csv", index=False)

    # Copy over files
    (public_path / "test").mkdir(exist_ok=True)
    (public_path / "train").mkdir(exist_ok=True)

    if dev:
        train_image_ids = train_image_ids[:10]
        test_image_ids = test_image_ids[:10]

    for file_id in tqdm(train_image_ids, desc=f"Copying {public_path.name} train files"):
        shutil.copyfile(
            src=raw_images_path / "train" / f"{file_id}.dicom",
            dst=public_path / "train" / f"{file_id}.dicom",
        )

    for file_id in tqdm(test_image_ids, desc=f"Copying {public_path.name} test files"):
        shutil.copyfile(
            src=raw_images_path / "train" / f"{file_id}.dicom",
            dst=public_path / "test" / f"{file_id}.dicom",
        )

    # Check files
    assert len(list(public_path.glob("train/*.dicom"))) == len(
        train_image_ids
    ), f"Incorrect number of train files copied for {public_path.name}"
    assert len(list(public_path.glob("test/*.dicom"))) == len(
        test_image_ids
    ), f"Incorrect number of test files copied for {public_path.name}"


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the data in raw into public and private datasets with appropriate test/train splits.
    Also creates a parallel validation split (public_val, private_val).
    """

    dev = False

    # Create train, test from train split
    old_train = read_csv(raw / "train.csv")
    unique_image_ids = old_train["image_id"].unique()

    # --- 1. Original Train/Test Split ---
    # Original train has 15k images, original test has 3k images
    # Our new train will have 13.5k images, our new test will have 1.5k images
    expected_train_size = 13500
    expected_test_size = 1500
    train_image_ids, test_image_ids = train_test_split(
        unique_image_ids, test_size=0.1, random_state=0
    )

    new_train = old_train[old_train["image_id"].isin(train_image_ids)]
    answers = old_train[old_train["image_id"].isin(test_image_ids)]

    # Checks
    assert (
        len(set(new_train["image_id"])) == expected_train_size
    ), f"Expected {expected_train_size} train image_ids, got {len(set(new_train['image_id']))}"
    assert (
        len(set(answers["image_id"])) == expected_test_size
    ), f"Expected {expected_test_size} test image_ids, got {len(set(answers['image_id']))}"
    assert set(new_train["image_id"]).isdisjoint(
        set(answers["image_id"])
    ), f"image_id is not disjoint between train and test sets"
    assert len(new_train) + len(answers) == len(
        old_train
    ), f"Length of new train and answers should add up to the length of old train, got {len(new_train) + len(answers)} vs {len(old_train)}"

    # Create all files for the original public/private split
    _create_split_files(
        train_df=new_train,
        answers_df=answers,
        train_image_ids=train_image_ids,
        test_image_ids=test_image_ids,
        public_path=public,
        private_path=private,
        raw_images_path=raw,
        dev=dev,
    )

    # --- 2. New Validation Split (from the `new_train` set) ---
    print("\nCreating validation split...")

    # Define paths for the new validation set
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # The new validation set should have the same size as the original test set
    train_for_val_split_ids = new_train["image_id"].unique()
    val_test_size = expected_test_size / len(train_for_val_split_ids)

    # Split `new_train` again to create a smaller train set and a validation set
    # We use the same random_state for consistency in splitting methodology
    train_val_image_ids, test_val_image_ids = train_test_split(
        train_for_val_split_ids, test_size=val_test_size, random_state=0
    )

    train_val = new_train[new_train["image_id"].isin(train_val_image_ids)]
    answers_val = new_train[new_train["image_id"].isin(test_val_image_ids)]

    # Create all files for the new validation split
    _create_split_files(
        train_df=train_val,
        answers_df=answers_val,
        train_image_ids=train_val_image_ids,
        test_image_ids=test_val_image_ids,
        public_path=public_val,
        private_path=private_val,
        raw_images_path=raw,
        dev=dev,
    )
    print("Validation split created successfully.")