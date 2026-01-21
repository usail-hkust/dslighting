from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from mlebench.utils import read_csv


def _split_and_save(
    df: pd.DataFrame,
    test_size: float,
    public_path: Path,
    private_path: Path,
    random_state: int,
):
    """
    Helper function to perform a data split, save files, and run assertions.

    Args:
        df (pd.DataFrame): The dataframe to split.
        test_size (float): The proportion of the dataset to allocate to the test split.
        public_path (Path): The directory for public-facing files (train set, unlabeled test set).
        private_path (Path): The directory for private-facing files (labeled test set).
        random_state (int): The seed for the random number generator.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: The resulting train and test dataframes.
    """
    # Ensure output directories exist
    public_path.mkdir(parents=True, exist_ok=True)
    private_path.mkdir(parents=True, exist_ok=True)

    # Perform the split
    train_df, test_df = train_test_split(
        df, test_size=test_size, random_state=random_state
    )
    test_df_without_labels = test_df.drop(columns=["Cover_Type"])

    # Save the split data using standard filenames
    train_df.to_csv(public_path / "train.csv", index=False)
    test_df.to_csv(private_path / "test.csv", index=False)
    test_df_without_labels.to_csv(public_path / "test.csv", index=False)

    # Create a sample submission file
    submission_df = pd.DataFrame(
        {"Id": test_df["Id"].values, "Cover_Type": 2}
    )
    submission_df.to_csv(public_path / "sample_submission.csv", index=False)

    # Assertions
    assert len(train_df) + len(test_df) == len(
        df
    ), "train and test splits lengths do not add up to original data."
    assert set(train_df["Id"]).isdisjoint(
        set(test_df["Id"])
    ), f"there are Ids in both train and test sets: {set(train_df['Id']).intersection(set(test_df['Id']))}"
    assert len(test_df_without_labels) == len(
        test_df
    ), "public and Private tests should have equal length"

    return train_df, test_df


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the data in raw into public and private datasets with appropriate test/train splits.
    Also creates a secondary validation split in public_val/private_val directories.
    """
    # Create train, test from train split
    old_train = read_csv(raw / "train.csv")

    # --- First Split: Create the original train and test sets ---
    # This call produces the original outputs, which must remain unchanged.
    new_train, new_test = _split_and_save(
        df=old_train,
        test_size=0.1,
        public_path=public,
        private_path=private,
        random_state=0,
    )

    # --- Second Split: Create a new train and validation set ---
    # Define paths for the new validation set outputs
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Calculate the test size for the second split to make the new validation
    # set (`test_val`) have the same number of samples as the original test set.
    test_val_size = len(new_test) / len(new_train)

    # This call takes the `new_train` data and splits it again, saving the
    # results to the new `_val` directories with identical structure and filenames.
    _split_and_save(
        df=new_train,
        test_size=test_val_size,
        public_path=public_val,
        private_path=private_val,
        random_state=0,  # Use the same random state for consistency
    )