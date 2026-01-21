from pathlib import Path
import pandas as pd

from sklearn.model_selection import train_test_split

from mlebench.utils import read_csv


def _save_split_files(train_df: pd.DataFrame, test_df: pd.DataFrame, public_dir: Path, private_dir: Path):
    """
    Saves the train/test splits to the specified public and private directories,
    ensuring a consistent file structure and content format.

    - Creates a sample submission file in public_dir.
    - Saves the full test set (with labels) to private_dir.
    - Saves the train set to public_dir.
    - Saves the test set (without labels) to public_dir.
    """
    # Ensure output directories exist
    public_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)

    # Create sample submission from a copy of the full test set
    sample_submission = test_df.copy()
    sample_submission["EC1"] = 0.5
    sample_submission["EC2"] = 0.5
    sample_submission.drop(
        sample_submission.columns.difference(["id", "EC1", "EC2"]), axis=1, inplace=True
    )
    sample_submission.to_csv(public_dir / "sample_submission.csv", index=False)

    # Create private files (full test set with labels)
    test_df.to_csv(private_dir / "test.csv", index=False)

    # Create public files visible to agents
    train_df.to_csv(public_dir / "train.csv", index=False)

    # Create public test set (without labels) from a new copy
    public_test_df = test_df.copy()
    public_test_df.drop(["EC1", "EC2", "EC3", "EC4", "EC5", "EC6"], axis=1, inplace=True)
    public_test_df.to_csv(public_dir / "test.csv", index=False)


def prepare(raw: Path, public: Path, private: Path):
    # Read the raw data
    old_train = read_csv(raw / "train.csv")

    # --- Step 1: Create the original train/test split ---
    # This split is used for the main competition leaderboard. Its outputs
    # in `public/` and `private/` must remain identical to the original script.
    original_test_size = 0.1
    new_train, new_test = train_test_split(
        old_train, test_size=original_test_size, random_state=0
    )

    # Save the files for the original split, ensuring original outputs are unchanged
    _save_split_files(new_train, new_test, public, private)

    # --- Step 2: Create the new validation split ---
    # This second split is derived from the *training data* of the first split.
    # It creates a smaller training set and a validation set for users,
    # saved to parallel `public_val/` and `private_val/` directories.

    # Define paths for the new validation split outputs
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # To keep the new validation set size (`test_val`) the same as the original
    # test set size (`new_test`), we adjust the split ratio.
    # test_val_size = original_test_size / (1 - original_test_size)
    val_split_test_size = original_test_size / (1.0 - original_test_size)

    # Create the new training and validation sets from the first-pass training data
    train_val, test_val = train_test_split(
        new_train, test_size=val_split_test_size, random_state=0
    )

    # Save the files for the new validation split using the same helper.
    # This guarantees the file/directory structure is mirrored.
    _save_split_files(train_val, test_val, public_val, private_val)

    # Original checks (adapted slightly for clarity after refactoring)
    public_test_df = read_csv(public / "test.csv")
    public_train_df = read_csv(public / "train.csv")
    assert public_test_df.shape[1] == 32, "Public test set should have 32 columns"
    assert public_train_df.shape[1] == 38, "Public train set should have 38 columns"
    assert len(public_train_df) + len(public_test_df) == len(
        old_train
    ), "Length of new_train and new_test should equal length of old_train"