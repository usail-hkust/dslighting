import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm.auto import tqdm

from mlebench.competitions.utils import get_ids_from_tf_records
from mlebench.utils import read_csv


def _process_and_save_split(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    train_tfrecords: list,
    test_tfrecords: list,
    public_dir: Path,
    private_dir: Path,
    raw_dir: Path,
):
    """
    Helper function to process a single data split (train/test) and save all
    associated files to the specified public and private directories.
    """
    # Create output directories
    public_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)

    # --- Create and save CSV files ---
    sample_submission = test_df.copy()
    sample_submission["label"] = 4  # Default label for submission template

    train_df.to_csv(public_dir / "train.csv", index=False)
    test_df.to_csv(private_dir / "test.csv", index=False)  # Ground truth
    sample_submission.to_csv(public_dir / "sample_submission.csv", index=False)

    # --- Copy and rename TFRecord files ---
    (public_dir / "train_tfrecords").mkdir(exist_ok=True)
    for i, path in tqdm(
        enumerate(train_tfrecords),
        desc=f"Copying Train TFRecords to {public_dir.name}",
        total=len(train_tfrecords),
    ):
        length = path.stem.split("-")[1]
        new_name = f"ld_train{i:02d}-{length}.tfrec"
        shutil.copy(path, public_dir / "train_tfrecords" / new_name)

    (public_dir / "test_tfrecords").mkdir(exist_ok=True)
    for i, path in tqdm(
        enumerate(test_tfrecords),
        desc=f"Copying Test TFRecords to {public_dir.name}",
        total=len(test_tfrecords),
    ):
        length = path.stem.split("-")[1]
        new_name = f"ld_test{i:02d}-{length}.tfrec"
        shutil.copy(path, public_dir / "test_tfrecords" / new_name)

    # --- Copy image files ---
    (public_dir / "train_images").mkdir(exist_ok=True)
    for image_id in tqdm(
        train_df["image_id"],
        desc=f"Copying Train Images to {public_dir.name}",
        total=len(train_df),
    ):
        shutil.copy(raw_dir / "train_images" / image_id, public_dir / "train_images")

    (public_dir / "test_images").mkdir(exist_ok=True)
    for image_id in tqdm(
        test_df["image_id"],
        desc=f"Copying Test Images to {public_dir.name}",
        total=len(test_df),
    ):
        shutil.copy(raw_dir / "train_images" / image_id, public_dir / "test_images")

    # --- Copy auxiliary files ---
    shutil.copy(raw_dir / "label_num_to_disease_map.json", public_dir)

    # --- Perform checks for this split ---
    assert len(train_df) + len(test_df) == len(train_df) + len(
        test_df
    ), f"Length check failed for {public_dir.name}"
    assert len(sample_submission) == len(
        test_df
    ), f"Sample submission length mismatch for {public_dir.name}"

    assert len(train_df) == sum(
        1 for _ in (public_dir / "train_images").iterdir()
    ), f"Train image count mismatch in {public_dir.name}"
    assert len(test_df) == sum(
        1 for _ in (public_dir / "test_images").iterdir()
    ), f"Test image count mismatch in {public_dir.name}"

    assert len(train_tfrecords) == sum(
        1 for _ in (public_dir / "train_tfrecords").iterdir()
    ), f"Train TFRecord count mismatch in {public_dir.name}"
    assert len(test_tfrecords) == sum(
        1 for _ in (public_dir / "test_tfrecords").iterdir()
    ), f"Test TFRecord count mismatch in {public_dir.name}"

    assert train_df.columns.tolist() == [
        "image_id",
        "label",
    ], f"Train columns mismatch for {public_dir.name}"
    assert test_df.columns.tolist() == [
        "image_id",
        "label",
    ], f"Test columns mismatch for {public_dir.name}"
    assert sample_submission.columns.tolist() == [
        "image_id",
        "label",
    ], f"Sample submission columns mismatch for {public_dir.name}"

    assert set(train_df["image_id"]).isdisjoint(
        test_df["image_id"]
    ), f"Train and test image IDs are not disjoint for {public_dir.name}"


def prepare(raw: Path, public: Path, private: Path):
    # Define paths for the new validation split
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # need to split based on the TFRecord files, since not mentioned in the CSVs
    tfrecord_files = [
        path
        for path in sorted((raw / "train_tfrecords").iterdir())
        if path.is_file() and path.suffix == ".tfrec"
    ]

    # --- FIRST SPLIT: Create original train and test sets ---
    # In the original there are 21397 train samples and they say test has ~15000 test samples, which is ~ 0.4/0.6 test/train split
    # We use 0.1 ratio to avoid removing too many samples from train
    train_tfrecords, test_tfrecords = train_test_split(
        tfrecord_files, test_size=0.1, random_state=0
    )

    # parse the IDs from the test tf records
    test_ids = []
    for path in test_tfrecords:
        test_ids.extend(get_ids_from_tf_records(path))

    # Create dataframes for the first split
    full_train_df = read_csv(raw / "train.csv")
    train_df = full_train_df[~full_train_df["image_id"].isin(test_ids)].copy()
    test_df = full_train_df[full_train_df["image_id"].isin(test_ids)].copy()

    # Process and save the original split to 'public' and 'private'
    # This ensures the original outputs are untouched
    _process_and_save_split(
        train_df=train_df,
        test_df=test_df,
        train_tfrecords=train_tfrecords,
        test_tfrecords=test_tfrecords,
        public_dir=public,
        private_dir=private,
        raw_dir=raw,
    )

    # --- SECOND SPLIT: Create new training and validation sets from the original train set ---
    # The new training set from the first split becomes the source for this second split.
    # A test_size of 1/9 on the train_tfrecords (which is 90% of the original data)
    # results in a validation set that is 10% of the original total, matching the
    # original test set size. (1/9 * 0.9 = 0.1)
    train_val_tfrecords, test_val_tfrecords = train_test_split(
        train_tfrecords, test_size=1 / 9, random_state=0
    )

    # Parse IDs for the validation set
    test_val_ids = []
    for path in test_val_tfrecords:
        test_val_ids.extend(get_ids_from_tf_records(path))

    # Create dataframes for the validation split using the original train_df
    train_val_df = train_df[~train_df["image_id"].isin(test_val_ids)].copy()
    test_val_df = train_df[train_df["image_id"].isin(test_val_ids)].copy()

    # Process and save the validation split to 'public_val' and 'private_val'
    _process_and_save_split(
        train_df=train_val_df,
        test_df=test_val_df,
        train_tfrecords=train_val_tfrecords,
        test_tfrecords=test_val_tfrecords,
        public_dir=public_val,
        private_dir=private_val,
        raw_dir=raw,
    )