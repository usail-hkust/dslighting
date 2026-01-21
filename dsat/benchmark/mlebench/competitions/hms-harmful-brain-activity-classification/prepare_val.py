import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm.auto import tqdm

from mlebench.utils import read_csv

from .constants import TARGET_COLS


def _process_split(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    public_dir: Path,
    private_dir: Path,
    raw_dir: Path,
):
    """
    Helper function to process a single train/test split and save all required files.
    This ensures that the logic for creating the main dataset and the validation dataset is identical.
    """
    public_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)

    # Save main data CSVs
    train_df.to_csv(public_dir / "train.csv", index=False)
    test_df.to_csv(private_dir / "test.csv", index=False)

    # Save public test CSV (without labels)
    test_without_labels = test_df.copy()[["spectrogram_id", "eeg_id", "patient_id"]]
    test_without_labels.to_csv(public_dir / "test.csv", index=False)

    # Create and save submission files
    gold_submission = test_df.copy()[["eeg_id"] + TARGET_COLS]
    # make the votes into probabilities naively
    # https://www.kaggle.com/competitions/hms-harmful-brain-activity-classification/discussion/468705#2606605
    gold_submission[TARGET_COLS] = gold_submission[TARGET_COLS].div(
        gold_submission[TARGET_COLS].sum(axis=1), axis=0
    )
    gold_submission.to_csv(private_dir / "gold_submission.csv", index=False)

    sample_submission = gold_submission.copy()
    sample_submission[TARGET_COLS] = 1 / len(TARGET_COLS)
    sample_submission.to_csv(public_dir / "sample_submission.csv", index=False)

    # Copy EEG files
    (public_dir / "train_eegs").mkdir(parents=True, exist_ok=True)
    for eeg_id in tqdm(
        train_df["eeg_id"].unique(),
        desc=f"Train EEGs ({public_dir.name})",
        total=len(train_df["eeg_id"].unique()),
    ):
        shutil.copy(
            raw_dir / "train_eegs" / f"{eeg_id}.parquet",
            public_dir / "train_eegs" / f"{eeg_id}.parquet",
        )
    (public_dir / "test_eegs").mkdir(parents=True, exist_ok=True)
    for eeg_id in tqdm(
        test_df["eeg_id"].unique(),
        desc=f"Test EEGs ({public_dir.name})",
        total=len(test_df["eeg_id"].unique()),
    ):
        shutil.copy(
            raw_dir / "train_eegs" / f"{eeg_id}.parquet",
            public_dir / "test_eegs" / f"{eeg_id}.parquet",
        )

    # Copy Spectrogram files
    (public_dir / "train_spectrograms").mkdir(parents=True, exist_ok=True)
    for spectrogram_id in tqdm(
        train_df["spectrogram_id"].unique(),
        desc=f"Train Spectrograms ({public_dir.name})",
        total=len(train_df["spectrogram_id"].unique()),
    ):
        shutil.copy(
            raw_dir / "train_spectrograms" / f"{spectrogram_id}.parquet",
            public_dir / "train_spectrograms" / f"{spectrogram_id}.parquet",
        )
    (public_dir / "test_spectrograms").mkdir(parents=True, exist_ok=True)
    for spectrogram_id in tqdm(
        test_df["spectrogram_id"].unique(),
        desc=f"Test Spectrograms ({public_dir.name})",
        total=len(test_df["spectrogram_id"].unique()),
    ):
        shutil.copy(
            raw_dir / "train_spectrograms" / f"{spectrogram_id}.parquet",
            public_dir / "test_spectrograms" / f"{spectrogram_id}.parquet",
        )

    # Assertions for data integrity
    assert len(list((public_dir / "train_eegs").rglob("*"))) == len(
        train_df["eeg_id"].unique()
    ), "Unexpected number of train EEGs Copied"
    assert len(list((public_dir / "test_eegs").rglob("*"))) == len(
        test_df["eeg_id"].unique()
    ), "Unexpected number of test EEGs Copied"

    assert len(list((public_dir / "train_spectrograms").rglob("*"))) == len(
        train_df["spectrogram_id"].unique()
    ), "Unexpected number of train Spectrograms Copied"
    assert len(list((public_dir / "test_spectrograms").rglob("*"))) == len(
        test_df["spectrogram_id"].unique()
    ), "Unexpected number of test Spectrograms Copied"

    assert set(train_df.spectrogram_id).isdisjoint(
        set(test_df.spectrogram_id)
    ), "Some spectrogram_ids are in both train and test"
    assert set(train_df.eeg_id).isdisjoint(
        set(test_df.eeg_id)
    ), "Some eeg_ids are in both train and test"

    assert (
        train_df.columns.tolist() == test_df.columns.tolist()
    ), "Columns mismatch between public train and private test"
    assert len(train_df.columns) == 15, "Unexpected number of columns in public train"
    assert len(test_df.columns) == 15, "Unexpected number of columns in private test"
    assert len(sample_submission.columns) == 7, "Unexpected number of columns in sample submission"
    assert len(gold_submission.columns) == 7, "Unexpected number of columns in gold submission"
    assert len(test_without_labels.columns) == 3, "Unexpected number of columns in private test"

    assert len(test_without_labels) == len(
        test_df
    ), "Length mismatch between public test and private test"
    assert len(sample_submission) == len(
        test_df
    ), "Length mismatch between sample submission and private test"
    assert len(gold_submission) == len(
        test_df
    ), "Length mismatch between gold submission and private test"


def prepare(raw: Path, public: Path, private: Path):
    old_train = read_csv(raw / "train.csv")

    # === Main Data Split (Train/Test) ===
    # This split produces the primary competition data.

    # split based on `spectrogram_id`
    # this is coarser than `eeg_id` which is coarser than `label_id`, so we avoid data leakage
    train_spectrograms, test_specrograms = train_test_split(
        old_train["spectrogram_id"].unique(), test_size=0.1, random_state=0
    )

    new_train = old_train[old_train["spectrogram_id"].isin(train_spectrograms)]
    new_test = old_train[old_train["spectrogram_id"].isin(test_specrograms)]

    # Process and save the main split to the `public` and `private` directories
    _process_split(new_train, new_test, public, private, raw)

    # Copy shared assets only to the main public directory
    shutil.copytree(raw / "example_figures", public / "example_figures")

    # Assertions for the main split (post-processing)
    assert len(new_train) + len(new_test) == len(
        old_train
    ), "Expected train + test length to be equal to original train length"

    # === Validation Data Split ===
    # This second split takes the main training set (`new_train`) and splits it
    # again to create a new, smaller training set and a validation set.
    # The outputs are saved to parallel `public_val` and `private_val` directories.

    # Define paths for the validation split output
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # The original test set was 10% of the total data. The main training set is 90%.
    # To get a validation set of the same size (10% of total), we need to take
    # 1/9th of the main training set (1/9 * 90% = 10%).
    val_test_size = 1 / 9

    train_val_spectrograms, test_val_specrograms = train_test_split(
        new_train["spectrogram_id"].unique(), test_size=val_test_size, random_state=0
    )

    train_val_df = new_train[new_train["spectrogram_id"].isin(train_val_spectrograms)]
    test_val_df = new_train[new_train["spectrogram_id"].isin(test_val_specrograms)]

    # Process and save the validation split using the same logic as the main split
    _process_split(train_val_df, test_val_df, public_val, private_val, raw)

    # Copy shared assets to the validation public directory to mirror the main one
    shutil.copytree(raw / "example_figures", public_val / "example_figures")

    # Assertions for the validation split (post-processing)
    assert len(train_val_df) + len(test_val_df) == len(
        new_train
    ), "Expected train_val + test_val length to be equal to new_train length"