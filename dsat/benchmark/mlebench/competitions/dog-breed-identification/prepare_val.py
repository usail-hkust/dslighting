import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from mlebench.competitions.utils import df_to_one_hot
from mlebench.utils import read_csv

from .dogs import DOGS_LIST


def to_one_hot(df: pd.DataFrame) -> pd.DataFrame:
    return df_to_one_hot(df, id_column="id", target_column="breed", classes=DOGS_LIST)


def _save_split(
    raw_data_path: Path,
    public_dir: Path,
    private_dir: Path,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
):
    """Saves a given train/test split to the specified public and private directories."""
    # Ensure target directories exist
    public_dir.mkdir(exist_ok=True)
    private_dir.mkdir(exist_ok=True)

    # one hot the private test because we will one-hot the submission, as per kaggle.com
    test_labels_private = to_one_hot(test_df.copy())

    # Copy over files
    train_df.to_csv(public_dir / "labels.csv", index=False)
    test_labels_private.to_csv(private_dir / "test.csv", index=False)

    (public_dir / "train").mkdir(exist_ok=True)
    for file_id in train_df["id"]:
        shutil.copyfile(
            src=raw_data_path / "train" / f"{file_id}.jpg",
            dst=public_dir / "train" / f"{file_id}.jpg",
        )

    (public_dir / "test").mkdir(exist_ok=True)
    for file_id in test_df["id"]:
        shutil.copyfile(
            src=raw_data_path / "train" / f"{file_id}.jpg",
            dst=public_dir / "test" / f"{file_id}.jpg",
        )

    # Check integrity of the files copied
    assert len(list(public_dir.glob("train/*.jpg"))) == len(train_df)
    assert len(list(public_dir.glob("test/*.jpg"))) == len(test_df)

    # Create a sample submission file
    submission_df = test_labels_private.copy()
    for col in submission_df.columns[1:]:
        submission_df[col] = submission_df[col].astype("float64")
    submission_df.iloc[:, 1:] = 1 / 120
    submission_df.to_csv(public_dir / "sample_submission.csv", index=False)

    assert submission_df.shape == (len(test_df), 121)  # 1 id column + 120 breeds


def prepare(raw: Path, public: Path, private: Path):
    # Read the full raw dataset labels
    all_labels = read_csv(raw / "labels.csv")

    # --- 1. Original Split: Create main train and test sets ---
    # This split and its outputs must remain identical to the original script.
    train_df, test_df = train_test_split(all_labels, test_size=0.1, random_state=0)

    # Save the original split to the 'public' and 'private' directories
    _save_split(
        raw_data_path=raw,
        public_dir=public,
        private_dir=private,
        train_df=train_df,
        test_df=test_df,
    )

    # --- 2. New Split: Create a validation set from the main train set ---
    # Define paths for the new validation directories, parallel to the original ones.
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # To ensure the new validation set ('test_val_df') is the same size as the
    # original test set, we calculate the required test_size for the second split.
    test_size_for_val_split = len(test_df) / len(train_df)

    # Split the main training data (train_df) into a smaller training set
    # and a validation set, using the same random_state for reproducibility.
    train_val_df, test_val_df = train_test_split(
        train_df, test_size=test_size_for_val_split, random_state=0
    )

    # Save the new validation split to the 'public_val' and 'private_val' directories
    # using the same helper function to ensure identical structure and filenames.
    _save_split(
        raw_data_path=raw,
        public_dir=public_val,
        private_dir=private_val,
        train_df=train_val_df,
        test_df=test_val_df,
    )