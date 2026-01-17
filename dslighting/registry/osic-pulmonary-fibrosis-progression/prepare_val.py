import shutil
from multiprocessing import Pool
from pathlib import Path
from typing import List, Tuple

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from mlebench.utils import read_csv


def copy_dir(args):
    src_dir, dst_dir = args
    shutil.copytree(src=src_dir, dst=dst_dir, dirs_exist_ok=True)


def _create_dataset_split(
    train_groups: List[Tuple[str, pd.DataFrame]],
    test_groups: List[Tuple[str, pd.DataFrame]],
    raw_path: Path,
    public_path: Path,
    private_path: Path,
):
    """
    Helper function to process a single train/test split of patient groups.

    This function takes lists of train and test patient groups, creates the necessary
    DataFrames, saves them to the specified public and private directories, and copies
    the associated patient data folders. This logic is used for both the original
    train/test split and the new train/validation split.
    """
    # Ensure output directories exist
    public_path.mkdir(exist_ok=True)
    private_path.mkdir(exist_ok=True)

    # Recreate DataFrames from the split groups
    new_train = pd.concat([group for _, group in train_groups])
    new_test = pd.concat([group for _, group in test_groups])
    assert set(new_train["Patient"]).isdisjoint(
        set(new_test["Patient"])
    ), "There are Patients who are in both train and test sets."

    # For the public new_test set we will only keep each patients first FVS measurement. The task is to predict FVS measurements for all possible weeks
    new_test_public = new_test.sort_values(by="Weeks").groupby("Patient").first().reset_index()

    # Creating the private answers CSV. We need to fill out dummy FVS measurements for all weeks that don't have data so as to match sample_submission.csv
    # Create a DataFrame with all possible Patient-Week combinations
    all_weeks = pd.DataFrame(
        [
            (patient, week)
            for patient in new_test["Patient"].unique()
            for week in range(new_test["Weeks"].min(), new_test["Weeks"].max() + 1)
        ],
        columns=["Patient", "Weeks"],
    )
    # Merge with the new_test DataFrame to fill in missing weeks with NaN values
    new_test_private = all_weeks.merge(new_test, on=["Patient", "Weeks"], how="left")
    new_test_private["Patient_Week"] = (
        new_test_private["Patient"] + "_" + new_test_private["Weeks"].astype(str)
    )
    new_test_private["Confidence"] = 100
    assert (
        new_test_private.groupby("Patient").size().nunique() == 1
    ), "Not all patients have the same number of rows."

    # Create a sample submission file
    submission_df = new_test_private.copy()
    submission_df = submission_df[["Patient_Week"]]
    submission_df["FVC"] = 2000  # Dummy predictions
    submission_df["Confidence"] = 100  # Dummy confidence

    # Write CSVs
    new_train.to_csv(public_path / "train.csv", index=False)
    new_test_public.to_csv(public_path / "test.csv", index=False)
    new_test_private.to_csv(private_path / "test.csv", index=False)
    submission_df.to_csv(public_path / "sample_submission.csv", index=False)

    # Copy over data files
    (public_path / "train").mkdir(exist_ok=True)
    train_args = [
        (raw_path / "train" / patient, public_path / "train" / patient)
        for patient in new_train["Patient"].unique()
    ]
    with Pool() as pool:
        list(
            tqdm(
                pool.imap(copy_dir, train_args),
                total=len(train_args),
                desc=f"Copying train data to {public_path.name}",
            )
        )

    (public_path / "test").mkdir(exist_ok=True)
    test_args = [
        (raw_path / "train" / patient, public_path / "test" / patient)
        for patient in new_test["Patient"].unique()
    ]
    with Pool() as pool:
        list(
            tqdm(
                pool.imap(copy_dir, test_args),
                total=len(test_args),
                desc=f"Copying test data to {public_path.name}",
            )
        )

    # Final checks
    assert new_train.shape[1] == 7, f"Expected 7 columns in new_train, but got {new_train.shape[1]}"
    assert (
        new_test_private.shape[1] == 9
    ), f"Expected 9 columns in new_test, but got {new_test_private.shape[1]}"
    assert (
        new_test_public.shape[1] == 7
    ), f"Expected 7 columns in new_test_public, but got {new_test_public.shape[1]}"
    assert (
        submission_df.shape[1] == 3
    ), f"Expected 3 columns in submission_df, but got {submission_df.shape[1]}"

    public_train_dirs = set((public_path / "train").iterdir())
    public_test_dirs = set((public_path / "test").iterdir())
    common_dirs = public_train_dirs.intersection(public_test_dirs)
    assert (
        not common_dirs
    ), f"There are directories with the same name in public train and test: {common_dirs}"


def prepare(raw: Path, public: Path, private: Path):
    # Read raw data and group by patient to ensure patient-level splits
    old_train = read_csv(raw / "train.csv")
    grouped_by_patient = list(old_train.groupby("Patient"))

    # ---- 1. Create the original train/test split ----
    # This split creates the main competition data in `public` and `private`
    train_groups, test_groups = train_test_split(
        grouped_by_patient, test_size=0.1, random_state=0
    )
    _create_dataset_split(
        train_groups=train_groups,
        test_groups=test_groups,
        raw_path=raw,
        public_path=public,
        private_path=private,
    )

    # ---- 2. Create the new train/validation split ----
    # This second split uses the `train_groups` from the first split to create
    # a smaller training set and a validation set. The outputs are saved in
    # parallel directories (`public_val`, `private_val`) to avoid altering
    # the original competition files.

    # Define new paths for the validation split
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Split the training data again to create a validation set.
    # We use the *same logic and random_state* as the original split.
    train_val_groups, test_val_groups = train_test_split(
        train_groups, test_size=0.1, random_state=0
    )
    _create_dataset_split(
        train_groups=train_val_groups,
        test_groups=test_val_groups,
        raw_path=raw,
        public_path=public_val,
        private_path=private_val,
    )