import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm.auto import tqdm

from mlebench.utils import get_logger

logger = get_logger(__name__)


def _create_split_files(
    original_meta_df: pd.DataFrame,
    train_batch_ids: list,
    test_batch_ids: list,
    public_dir: Path,
    private_dir: Path,
    raw_dir: Path,
):
    """
    Helper function to process a split (e.g., train/test or train_val/test_val),
    save the necessary files, and run checks.
    """
    logger.info(f"Processing split for destination: {public_dir.name}")
    public_dir.mkdir(exist_ok=True, parents=True)
    private_dir.mkdir(exist_ok=True, parents=True)

    new_train = (
        original_meta_df[original_meta_df["batch_id"].isin(train_batch_ids)]
        .reset_index(drop=True)
        .copy()
    )
    new_test = (
        original_meta_df[original_meta_df["batch_id"].isin(test_batch_ids)]
        .reset_index(drop=True)
        .copy()
    )

    logger.info("Creating label-less test and sample submission")
    new_test_without_labels = new_test.drop(columns=["azimuth", "zenith"])

    # format private test to only contain event_id and labels
    new_test = new_test[["event_id", "azimuth", "zenith"]]

    # copy the format as the private test and fill dummy values like kaggle.com
    sample_submission = new_test.copy()
    sample_submission["azimuth"] = 1
    sample_submission["zenith"] = 1

    logger.info("Saving metadata files")
    new_train.to_parquet(public_dir / "train_meta.parquet", index=False, engine="fastparquet")
    new_test_without_labels.to_parquet(
        public_dir / "test_meta.parquet", index=False, engine="fastparquet"
    )
    sample_submission.to_csv(public_dir / "sample_submission.csv", index=False)
    new_test.to_csv(private_dir / "test.csv", index=False)

    logger.info("Copying sensor geometry and batch data files")
    # sensor_geometry can be copied as is
    shutil.copy(raw_dir / "sensor_geometry.csv", public_dir / "sensor_geometry.csv")

    # copy the raw train files to train and test folders respectively
    train_ids_set = set(train_batch_ids)
    train_dest = public_dir / "train"
    train_dest.mkdir(exist_ok=True, parents=True)
    test_ids_set = set(test_batch_ids)
    test_dest = public_dir / "test"
    test_dest.mkdir(exist_ok=True, parents=True)

    for batch_file in tqdm(
        sorted((raw_dir / "train").glob("*.parquet")), desc=f"Copying batches to {public_dir.name}"
    ):
        batch_id = int(batch_file.stem.split("_")[-1])
        if batch_id in train_ids_set:
            shutil.copy(batch_file, train_dest / batch_file.name)
        elif batch_id in test_ids_set:
            shutil.copy(batch_file, test_dest / batch_file.name)

    logger.info("Running checks")
    assert len(list(public_dir.glob("train/*.parquet"))) == len(
        train_batch_ids
    ), "Not all train batches copied"
    assert len(list(public_dir.glob("test/*.parquet"))) == len(
        test_batch_ids
    ), "Not all test batches copied"
    assert len(train_batch_ids) + len(test_batch_ids) == len(
        set(train_batch_ids) | set(test_batch_ids)
    ), "Something went wrong with splitting the batches"

    # Drop the 'split' column for accurate checks, as it's not in the final data
    original_meta_subset = original_meta_df[
        original_meta_df["batch_id"].isin(train_batch_ids + test_batch_ids)
    ]
    if "split" in original_meta_subset.columns:
        original_meta_subset = original_meta_subset.drop(columns=["split"])

    assert len(new_train) + len(new_test) == len(
        original_meta_subset
    ), "Expected train + test to equal the original data"
    assert len(sample_submission) == len(
        new_test
    ), "Length mismatch between private test and sample submission"

    assert sample_submission.columns.equals(
        new_test.columns
    ), "Column mismatch between sample_submission and private test"
    assert new_train.columns.equals(
        original_meta_subset.columns
    ), f"Unexpected columns in train, expected {original_meta_subset.columns}, got {new_train.columns}"
    assert new_test_without_labels.columns.equals(
        original_meta_subset.drop(columns=["azimuth", "zenith"]).columns
    ), f"Unexpected columns in test"

    assert (
        len(set(new_train["event_id"]).intersection(set(new_test["event_id"]))) == 0
    ), "Event ids overlap between train and test"
    assert set(new_test["event_id"]) == set(
        sample_submission["event_id"]
    ), "Event ids mismatch between test and sample submission"


def prepare(raw: Path, public: Path, private: Path):
    DEV = False

    if DEV:
        batch_cutoff = 66  # 66 instead of 660 when in dev mode
    else:
        batch_cutoff = None

    logger.info("Loading raw metadata")
    old_train = pd.read_parquet(raw / "train_meta.parquet")
    batch_ids = old_train["batch_id"].unique()[:batch_cutoff]

    # Clean the dataframe for processing.
    # The original script adds a 'split' column which we don't need in the helper.
    old_train_clean = old_train[old_train["batch_id"].isin(batch_ids)].drop(
        columns=["split"], errors="ignore"
    )

    # --- 1. Original Split: Raw Data -> Train / Test ---
    logger.info("Splitting batches into original train and test sets")
    train_batch_ids, test_batch_ids = train_test_split(
        batch_ids, test_size=0.1, random_state=0
    )

    # Process and save the original split to 'public' and 'private'
    _create_split_files(
        original_meta_df=old_train_clean,
        train_batch_ids=list(train_batch_ids),
        test_batch_ids=list(test_batch_ids),
        public_dir=public,
        private_dir=private,
        raw_dir=raw,
    )

    # --- 2. New Validation Split: Original Train -> New Train / Validation Test ---
    logger.info("Creating new parallel directories for validation split")
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # The new validation set should be the same size as the original test set.
    # Calculate the required test_size for the second split.
    # test_size = (size of desired val set) / (size of set being split)
    #           = len(test_batch_ids) / len(train_batch_ids)
    test_val_size_ratio = len(test_batch_ids) / len(train_batch_ids)

    logger.info(f"Splitting original train set to create validation set")
    train_val_batch_ids, test_val_batch_ids = train_test_split(
        train_batch_ids, test_size=test_val_size_ratio, random_state=0
    )

    # Process and save the new validation split to 'public_val' and 'private_val'
    _create_split_files(
        original_meta_df=old_train_clean,
        train_batch_ids=list(train_val_batch_ids),
        test_batch_ids=list(test_val_batch_ids),
        public_dir=public_val,
        private_dir=private_val,
        raw_dir=raw,
    )

    logger.info("All data preparation tasks are complete.")