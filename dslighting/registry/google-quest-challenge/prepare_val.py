from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from mlebench.utils import read_csv

from .classes import CLASSES


def _create_split_and_write_files(
    source_df: pd.DataFrame,
    public_dir: Path,
    private_dir: Path,
    test_size: float,
    random_state: int,
):
    """
    Splits a dataframe into train and test sets, and writes them to public and private directories.

    This function encapsulates the core data preparation logic:
    1. Splits the data.
    2. Handles a special case for 'question_type_spelling' to ensure variability.
    3. Creates public-facing test set (without labels) and a sample submission.
    4. Creates private-facing test set (with labels).
    5. Writes all files to the specified directories.
    6. Performs assertions to validate the output.
    """
    # Create output directories if they don't exist
    public_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)

    # Create train and test splits from the source dataframe
    train_df, test_df = train_test_split(
        source_df, test_size=test_size, random_state=random_state
    )

    # question_type_spelling is almost always 0; if entirely 0 in test set, swap one row
    if test_df["question_type_spelling"].nunique() == 1:
        # need to do this swapping because spearmanr needs variation in the data to work
        suitable_train_row_index = train_df[train_df["question_type_spelling"] != 0].index[0]
        suitable_test_row_index = test_df.index[0]
        temp = test_df.loc[suitable_test_row_index].copy()
        test_df.loc[suitable_test_row_index] = train_df.loc[suitable_train_row_index].copy()
        train_df.loc[suitable_train_row_index] = temp

    test_df_without_labels = test_df.drop(CLASSES, axis=1, inplace=False)

    # Create sample submission; private test will match this format
    cols_to_keep = ["qa_id"] + CLASSES
    test_labels = test_df[cols_to_keep]
    sample_submission = test_labels.copy()
    # spearmanr needs variation in the data to work; make each column increasing from 0 to 1
    n, M = len(sample_submission), len(CLASSES)
    sample_submission[CLASSES] = np.tile(np.linspace(0, 1, n)[:, None], (1, M))

    # Create private files
    test_labels.to_csv(private_dir / "test.csv", index=False)

    # Create public files visible to agents
    train_df.to_csv(public_dir / "train.csv", index=False)
    test_df_without_labels.to_csv(public_dir / "test.csv", index=False)
    sample_submission.to_csv(public_dir / "sample_submission.csv", index=False)

    # Checks
    assert test_df_without_labels.shape[1] == 11, "Public test set should have 11 columns"
    assert train_df.shape[1] == 41, "Public train set should have 41 columns"
    # each private test set target column should not be constant
    for column in CLASSES:
        assert (
            test_labels[column].nunique() > 1
        ), f"Column {column} should not be constant in the private test set"
    assert len(train_df) + len(test_df) == len(
        source_df
    ), "Length of new_train and new_test should equal length of source_df"
    assert (
        sample_submission.columns.to_list() == test_labels.columns.to_list()
    ), "Sample submission columns should match test set"
    assert len(sample_submission) == len(test_labels), "Sample submission length should match test set"

    return train_df, test_df


def prepare(raw: Path, public: Path, private: Path):

    # Load the raw data from the competition
    source_data = read_csv(raw / "train.csv")

    # ---- 1. Create the Original Main Split (train/test) ----
    # This first call generates the primary train and test sets.
    # The output files are saved to the `public` and `private` directories,
    # remaining identical to the original script's output.
    main_train, main_test = _create_split_and_write_files(
        source_df=source_data,
        public_dir=public,
        private_dir=private,
        test_size=0.1,
        random_state=0,
    )

    # ---- 2. Create the New Validation Split (train_val/test_val) ----
    # This second call takes the `main_train` set from the first split and
    # splits it again to create a new, smaller training set and a validation set.
    # The outputs are saved to new, parallel `public_val` and `private_val` dirs.
    public_val_dir = public.parent / "public_val"
    private_val_dir = private.parent / "private_val"

    # To make the new validation set (`test_val`) have the same number of samples
    # as the original test set (`main_test`), we calculate the required `test_size`
    # relative to the size of the `main_train` dataframe.
    validation_test_size = len(main_test) / len(main_train)

    _create_split_and_write_files(
        source_df=main_train,
        public_dir=public_val_dir,
        private_dir=private_val_dir,
        test_size=validation_test_size,
        random_state=0,  # Use the same random state for consistency
    )