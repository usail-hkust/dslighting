import shutil
from pathlib import Path

import pandas as pd
import requests
from sklearn.model_selection import train_test_split

from mlebench.utils import get_logger

from .vocabulary import CLASS_NAMES

logger = get_logger(__name__)


def download_file(url, local_filename):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
    return local_filename


def _create_many_hot_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Converts a DataFrame with comma-separated labels into a many-hot encoded DataFrame."""
    new_rows = []
    for _, row in df.iterrows():
        fname = row["fname"]
        labels = row["labels"].split(",")
        labels_one_hot = [1 if class_name in labels else 0 for class_name in CLASS_NAMES]
        new_rows.append([fname] + labels_one_hot)

    new_df = pd.DataFrame(new_rows, columns=["fname"] + CLASS_NAMES)
    return new_df


def prepare(raw: Path, public: Path, private: Path):
    """
    Straightforward: we have access to the post-competition released test labels, so we don't need
    to create our own split here. We just copy over the raw data provided by the competition and
    download the test labels.

    Otherwise, the only work here is to convert the test data into the right format for grading:
    The original form of `test.csv` is a DataFrame with N rows and 2 columns. The first column is
    "fname" and the second column is the labels as comma-separated strings (class names). We
    convert the test labels into a binary many-hot matrix matching the shape of the submission,
    [N rows, M + 1 columns]: The first column is "fname" and the remaining M columns are the
    predictions for each class.

    This script also creates a new validation set by splitting the original train_curated set,
    saving the results in `public_val` and `private_val` directories.
    """
    # =================================================================
    # Original Data Preparation (public/ and private/)
    # =================================================================

    # Copy over everything in the raw directory
    logger.info("Copying raw data to public directory")
    # Don't copy the metadata file if it exists
    items_to_copy = [item for item in raw.iterdir() if "FSDKaggle2019.meta" not in item.name]
    for item in items_to_copy:
        dest = public / item.name
        if dest.exists():
            continue
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy(item, dest)
    assert len(list(public.iterdir())) >= len(
        items_to_copy
    ), "Expected all files in raw to be copied to public"

    # Download the test labels and metadata that were released after the competition
    test_url = "https://zenodo.org/records/3612637/files/FSDKaggle2019.meta.zip?download=1"
    dest_path = raw / "FSDKaggle2019.meta.zip"
    if not dest_path.exists():
        download_file(test_url, dest_path)
        logger.info(f"Downloaded file saved as {dest_path}")
        # # Unzip
        shutil.unpack_archive(dest_path, raw)
        logger.info(f"Unzipped file to {raw / 'FSDKaggle2019.meta'}")

    unzipped_path = raw / "FSDKaggle2019.meta"

    # Read test labels
    test_post_competition = pd.read_csv(unzipped_path / "test_post_competition.csv")
    private_test_df = test_post_competition[test_post_competition["usage"] == "Private"]
    # Create a binary many-hot matrix
    new_test = _create_many_hot_labels(private_test_df)
    new_test.to_csv(private / "test.csv", index=False)

    # Check that test and submission match
    submission = pd.read_csv(public / "sample_submission.csv")
    assert len(submission) == len(
        new_test
    ), f"Expected {len(new_test)} rows in test.csv, but got {len(submission)}"
    assert (
        submission.columns[1:].tolist() == CLASS_NAMES
    ), "Expected class names to match between test.csv and sample_submission.csv"
    assert all(
        submission.columns == new_test.columns
    ), "Expected columns to match between test.csv and sample_submission.csv"
    new_test.sort_values("fname", inplace=True)
    submission.sort_values("fname", inplace=True)
    assert (
        submission["fname"].tolist() == new_test["fname"].tolist()
    ), "Expected 'fname' to match between test.csv and sample_submission.csv"

    # Remove the downloaded metadata
    if dest_path.exists():
        dest_path.unlink()
    if unzipped_path.exists():
        shutil.rmtree(unzipped_path)

    # =================================================================
    # New Validation Set Creation (public_val/ and private_val/)
    # =================================================================
    logger.info("Creating new validation set from train_curated.csv")

    # Define paths and create parallel directories for the validation set
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"
    public_val.mkdir(exist_ok=True)
    private_val.mkdir(exist_ok=True)

    # Load original curated training data and final test set (to match size)
    original_train_df = pd.read_csv(public / "train_curated.csv")
    original_test_df = pd.read_csv(private / "test.csv")

    # Split the curated training data to create a new train/validation set.
    # The new validation set ('test_val') will have the same size as the original test set.
    train_val_df, test_val_df = train_test_split(
        original_train_df, test_size=len(original_test_df), random_state=42, shuffle=True
    )

    # --- Populate public_val directory ---
    logger.info(f"Populating {public_val} with new training and validation data")

    # Save the new, smaller curated training set manifest
    train_val_df.to_csv(public_val / "train_curated.csv", index=False)

    # To mirror the directory structure, copy the noisy data as-is
    shutil.copy(public / "train_noisy.csv", public_val / "train_noisy.csv")
    if (public / "train_noisy").exists():
        if (public_val / "train_noisy").exists():
            shutil.rmtree(public_val / "train_noisy")
        shutil.copytree(public / "train_noisy", public_val / "train_noisy")

    # Create directories for the new audio file splits
    (public_val / "train_curated").mkdir(exist_ok=True)
    (public_val / "test").mkdir(exist_ok=True)

    # Copy audio files for the new, smaller training set
    for fname in train_val_df["fname"]:
        shutil.copy(public / "train_curated" / fname, public_val / "train_curated" / fname)

    # Copy audio files for the new validation set into its 'test' directory
    for fname in test_val_df["fname"]:
        shutil.copy(public / "train_curated" / fname, public_val / "test" / fname)

    # Create a new sample submission file corresponding to the validation set
    val_submission = pd.DataFrame({"fname": test_val_df["fname"].sort_values()})
    for col in CLASS_NAMES:
        val_submission[col] = 0
    val_submission.to_csv(public_val / "sample_submission.csv", index=False)

    # --- Populate private_val directory ---
    logger.info(f"Populating {private_val} with new validation labels")

    # Create and save the ground truth labels for the new validation set
    private_test_val_df = _create_many_hot_labels(test_val_df)
    private_test_val_df.to_csv(private_val / "test.csv", index=False)

    logger.info("Validation set creation complete.")