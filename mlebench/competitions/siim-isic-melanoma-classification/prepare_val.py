import shutil
from pathlib import Path
from typing import Set, List

import pandas as pd
from tqdm.auto import tqdm

from mlebench.competitions.utils import get_ids_from_tf_records
from mlebench.utils import get_logger

logger = get_logger(__name__)


def _get_ids_from_tfrec_set(raw_path: Path, tfrec_set: Set[str]) -> List[str]:
    """Helper function to parse image IDs from a given set of TFRecord files."""
    ids = []
    for tfrec_name in tqdm(tfrec_set, desc="Splitting IDs from TFRecords"):
        ids.extend(get_ids_from_tf_records(raw_path / "tfrecords" / tfrec_name))
    return ids


def _create_dataset_files(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    source_tfrec_files: List[Path],
    test_tfrec_set: Set[str],
    raw_path: Path,
    public_path: Path,
    private_path: Path,
):
    """
    Core function to generate all files for a given train/test split.
    This includes CSVs, image files (JPG, DCM), and TFRecords.
    """
    # Create destination directories
    public_path.mkdir(parents=True, exist_ok=True)
    private_path.mkdir(parents=True, exist_ok=True)

    # Prepare dataframes for saving
    test_df_without_labels = test_df.copy()[
        ["image_name", "patient_id", "sex", "age_approx", "anatom_site_general_challenge"]
    ]
    test_df_with_labels = test_df[["image_name", "target"]]
    sample_submission = test_df_with_labels.copy()
    sample_submission["target"] = 0

    # Save the CSVs
    train_df.to_csv(public_path / "train.csv", index=False)
    test_df_without_labels.to_csv(public_path / "test.csv", index=False)
    sample_submission.to_csv(public_path / "sample_submission.csv", index=False)
    test_df_with_labels.to_csv(private_path / "test.csv", index=False)

    # Copy image files (DICOMs and JPEGs)
    (public_path / "train").mkdir(parents=True, exist_ok=True)
    (public_path / "jpeg" / "train").mkdir(parents=True, exist_ok=True)
    for image_name in tqdm(train_df["image_name"], desc=f"Train Images -> {public_path.name}", total=len(train_df)):
        shutil.copy(raw_path / "train" / f"{image_name}.dcm", public_path / "train" / f"{image_name}.dcm")
        shutil.copy(raw_path / "jpeg" / "train" / f"{image_name}.jpg", public_path / "jpeg" / "train" / f"{image_name}.jpg")

    (public_path / "test").mkdir(parents=True, exist_ok=True)
    (public_path / "jpeg" / "test").mkdir(parents=True, exist_ok=True)
    for image_name in tqdm(test_df["image_name"], desc=f"Test Images -> {public_path.name}", total=len(test_df)):
        shutil.copy(raw_path / "train" / f"{image_name}.dcm", public_path / "test" / f"{image_name}.dcm")
        shutil.copy(raw_path / "jpeg" / "train" / f"{image_name}.jpg", public_path / "jpeg" / "test" / f"{image_name}.jpg")

    # Copy and rename TFRecords
    train_count = 0
    test_count = 0
    tfrecords_dest_path = public_path / "tfrecords"
    tfrecords_dest_path.mkdir(parents=True, exist_ok=True)
    for file in tqdm(source_tfrec_files, desc=f"Copying TFRecords -> {public_path.name}"):
        record_count = file.stem.split("-")[1]
        if file.name in test_tfrec_set:
            shutil.copy(file, tfrecords_dest_path / f"test{test_count:02d}-{record_count}.tfrec")
            test_count += 1
        else:
            shutil.copy(file, tfrecords_dest_path / f"train{train_count:02d}-{record_count}.tfrec")
            train_count += 1

    # Assertions to ensure data integrity
    logger.info(f"Running asserts for {public_path.name} split...")
    assert len(list(public_path.glob("train/*.dcm"))) == len(train_df), "Train DICOM count mismatch"
    assert len(list(public_path.glob("test/*.dcm"))) == len(test_df), "Test DICOM count mismatch"
    assert len(list(public_path.glob("jpeg/train/*.jpg"))) == len(train_df), "Train JPEG count mismatch"
    assert len(list(public_path.glob("jpeg/test/*.jpg"))) == len(test_df), "Test JPEG count mismatch"
    assert not set(train_df["image_name"]).intersection(test_df["image_name"]), "Train/Test overlap"
    assert len(sample_submission) == len(test_df), "Sample submission length mismatch"
    assert (
        sample_submission["image_name"].sort_values().reset_index(drop=True)
        .equals(test_df["image_name"].sort_values().reset_index(drop=True))
    ), "Sample submission IDs mismatch"


def prepare(raw: Path, public: Path, private: Path):
    # Common setup
    DEV = False
    cutoff_index = 10000 if DEV else None
    all_data_df = pd.read_csv(raw / "train.csv")[:cutoff_index]
    all_raw_tfrec_files = sorted((raw / "tfrecords").glob("train*.tfrec"))

    # --- 1. Original Competition Split (train -> train/test) ---
    logger.info("--- Creating original public/private split ---")

    # The original split used 2 arbitrary TFRecord files as the test set
    original_test_tfrec_set = {"train00-2071.tfrec", "train06-2071.tfrec"}
    original_test_ids = _get_ids_from_tfrec_set(raw, original_test_tfrec_set)

    # Split the main dataframe
    all_data_df["split"] = "train"
    all_data_df.loc[all_data_df["image_name"].isin(original_test_ids), "split"] = "test"
    
    # These are the final dataframes for the original competition
    final_train_df = all_data_df[all_data_df["split"] == "train"].drop(columns=["split"])
    final_test_df = all_data_df[all_data_df["split"] == "test"].drop(columns=["split"])

    # Create all files for the original split
    _create_dataset_files(
        train_df=final_train_df,
        test_df=final_test_df,
        source_tfrec_files=all_raw_tfrec_files,
        test_tfrec_set=original_test_tfrec_set,
        raw_path=raw,
        public_path=public,
        private_path=private,
    )

    # --- 2. New Validation Split (train -> train_val/test_val) ---
    logger.info("--- Creating new public_val/private_val split ---")

    # Define new directories for the validation set
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # The source for this new split is the *training* data from the *first* split.
    # We replicate the split logic by taking 2 TFRecord files for the validation-test set.
    val_source_tfrec_files = [f for f in all_raw_tfrec_files if f.name not in original_test_tfrec_set]
    val_test_tfrec_set = {"train01-2071.tfrec", "train02-2071.tfrec"}
    val_test_ids = _get_ids_from_tfrec_set(raw, val_test_tfrec_set)

    # Split the *training dataframe* from the first split to create the new sets
    final_train_df["split"] = "train_val"
    final_train_df.loc[final_train_df["image_name"].isin(val_test_ids), "split"] = "test_val"
    
    train_val_df = final_train_df[final_train_df["split"] == "train_val"].drop(columns=["split"])
    test_val_df = final_train_df[final_train_df["split"] == "test_val"].drop(columns=["split"])

    # Create all files for the new validation split
    _create_dataset_files(
        train_df=train_val_df,
        test_df=test_val_df,
        source_tfrec_files=val_source_tfrec_files,
        test_tfrec_set=val_test_tfrec_set,
        raw_path=raw,
        public_path=public_val,
        private_path=private_val,
    )

    logger.info("--- Data preparation complete for all splits. ---")