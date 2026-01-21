from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from mlebench.utils import read_csv


def _create_split_files(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    public_dir: Path,
    private_dir: Path,
):
    """A helper function to save train/test splits and artifacts."""
    # Create random example submission
    example_submission = test_df[["PassengerId", "Transported"]].copy()
    example_submission["Transported"] = False
    example_submission.to_csv(public_dir / "sample_submission.csv", index=False)

    # Create private files
    test_df.to_csv(private_dir / "test.csv", index=False)

    # Create public files visible to agents
    train_df.to_csv(public_dir / "train.csv", index=False)
    test_df.drop("Transported", axis="columns").to_csv(
        public_dir / "test.csv", index=False
    )


def prepare(raw: Path, public: Path, private: Path):
    # Define and create all output directories to ensure they exist
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"
    public_val.mkdir(parents=True, exist_ok=True)
    private_val.mkdir(parents=True, exist_ok=True)

    # --- Original Split: Create main train and test sets ---
    # Create train and test splits from train set
    old_train = read_csv(raw / "train.csv")
    new_train, new_test = train_test_split(old_train, test_size=0.1, random_state=0)

    # Generate the files for the original public/private directories
    # This ensures the original outputs are unchanged
    _create_split_files(new_train, new_test, public, private)

    # --- Validation Split: Create a new train and validation set ---
    # The new validation set should be approx. the same size as the original test set.
    # We calculate the required test_size for splitting the new_train set.
    test_size_for_val = len(new_test) / len(new_train)

    # Split the training data again to create a new, smaller training set and a validation set
    train_val, test_val = train_test_split(
        new_train, test_size=test_size_for_val, random_state=0
    )

    # Generate the files for the new validation directories, using the exact same
    # structure and filenames as the original split.
    _create_split_files(train_val, test_val, public_val, private_val)