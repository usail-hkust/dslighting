import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from mlebench.utils import read_csv


def _perform_split(
    df: pd.DataFrame, target_test_size: float, random_seed: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Performs the custom splitting logic on a given dataframe.

    This logic ensures that for IDs with 2 or more images, one is guaranteed
    to be in the train set and one in the test set. The remaining data is
    split randomly.

    Args:
        df: The input dataframe with "Image" and "Id" columns.
        target_test_size: The approximate fraction of data to allocate to the test set.
        random_seed: The random seed for reproducibility.

    Returns:
        A tuple containing the train dataframe and the test dataframe.
    """
    # Make a copy to avoid modifying the original dataframe
    data_to_split = df.copy()
    data_to_split["split"] = "undecided"

    # seeded random generator for numpy
    np_rng = np.random.default_rng(random_seed)

    # ensure each id occurs in train and test set at least once
    # when there's only one image for an id, goes randomly to train or test
    whale_ids = data_to_split["Id"].unique()
    for whale_id in whale_ids:
        whale_images = data_to_split[data_to_split["Id"] == whale_id]
        if len(whale_images) >= 2:
            # randomly assign one of these to train and one to test
            selected = whale_images.sample(2, random_state=random_seed)
            data_to_split.loc[selected.index[0], "split"] = "train"
            data_to_split.loc[selected.index[1], "split"] = "test"
        else:
            # randomly assign this one image to train or test
            data_to_split.loc[whale_images.index[0], "split"] = np_rng.choice(
                ["train", "test"],
                replace=False,
                p=[1 - target_test_size, target_test_size],
            )

    # split the remaining data
    remaining_data = data_to_split[data_to_split["split"] == "undecided"]
    if not remaining_data.empty:
        train, test = train_test_split(
            remaining_data, test_size=target_test_size, random_state=random_seed
        )
        data_to_split.loc[train.index, "split"] = "train"
        data_to_split.loc[test.index, "split"] = "test"

    # finally, can split out into separate dataframes
    train_df = data_to_split[data_to_split["split"] == "train"].drop(
        columns=["split"]
    )
    test_df = data_to_split[data_to_split["split"] == "test"].drop(columns=["split"])

    return train_df.copy(), test_df.copy()


def _write_output_files(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    public_dir: Path,
    private_dir: Path,
    raw_dir: Path,
):
    """
    Writes all required output files for a given train/test split.
    This includes CSVs, images, and a sample submission file.
    """
    public_dir.mkdir(exist_ok=True)
    private_dir.mkdir(exist_ok=True)

    # Make a copy of the test dataframe to create the final answers
    answers = test_df.copy()

    # If a whale Id is only in the test set, it should be labeled as new_whale instead
    ids_in_test_but_not_train = set(answers["Id"]) - set(train_df["Id"])
    answers.loc[answers["Id"].isin(ids_in_test_but_not_train), "Id"] = "new_whale"

    # Create sample submission
    sample_submission = answers.copy()
    sample_submission["Id"] = "new_whale w_1287fbc w_98baff9 w_7554f44 w_1eafe46"

    # Checks
    assert len(answers) == len(
        sample_submission
    ), "Answers and sample submission should have the same length"
    assert train_df.shape[1] == 2, "Train should have exactly 2 columns"
    assert sample_submission.shape[1] == 2, "Sample submission should have exactly 2 columns"
    assert answers.shape[1] == 2, "Answers should have exactly 2 columns"
    assert (
        "new_whale" in answers["Id"].values
    ), "Answers should contain at least some values with 'new_whale' in the 'Id' column"
    assert len(train_df) + len(answers) == len(train_df) + len(
        test_df
    ), "The combined length of train_df and answers should equal their original combined length"

    # Write CSVs
    answers.to_csv(private_dir / "test.csv", index=False)
    train_df.to_csv(public_dir / "train.csv", index=False)
    sample_submission.to_csv(public_dir / "sample_submission.csv", index=False)

    # Copy over files
    (public_dir / "test").mkdir(exist_ok=True)
    (public_dir / "train").mkdir(exist_ok=True)

    for file_id in tqdm(train_df["Image"], desc=f"Copying train images to {public_dir}"):
        shutil.copyfile(
            src=raw_dir / "train" / f"{file_id}",
            dst=public_dir / "train" / f"{file_id}",
        )

    for file_id in tqdm(answers["Image"], desc=f"Copying test images to {public_dir}"):
        shutil.copyfile(
            src=raw_dir / "train" / f"{file_id}",
            dst=public_dir / "test" / f"{file_id}",
        )

    # File checks
    train_files = list(public_dir.glob("train/*.jpg"))
    test_files = list(public_dir.glob("test/*.jpg"))
    assert len(train_files) == len(
        train_df
    ), f"Train dir {public_dir / 'train'} should have the same number of images as the length of its train set"
    assert len(test_files) == len(
        answers
    ), f"Test dir {public_dir / 'test'} should have the same number of images as the length of its test set"
    assert not set(train_files) & set(test_files), "Train and test files should be distinct"


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the data in raw into public and private datasets with appropriate test/train splits.
    Additionally, it creates a second parallel split (train_val, test_val) for validation purposes.
    """
    old_train = read_csv(raw / "train.csv")
    target_test_size = 0.1
    random_seed = 0

    # --- Step 1: Create the original train/test split ---
    # This split generates the main competition data.
    new_train, answers = _perform_split(
        df=old_train, target_test_size=target_test_size, random_seed=random_seed
    )

    # Write the original output files. This part is unchanged in its output.
    _write_output_files(
        train_df=new_train,
        test_df=answers,
        public_dir=public,
        private_dir=private,
        raw_dir=raw,
    )

    # --- Step 2: Create the new validation split ---
    # This takes the `new_train` set from the first split and splits it again
    # to create a validation set (`test_val`) of a similar size to the original `answers`.
    # The new, smaller training set is `train_val`.

    # Define paths for the new validation directories
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # To get a validation test set of size ~0.1*N from a training set of size ~0.9*N,
    # the new test_size must be 0.1/0.9.
    val_target_test_size = target_test_size / (1 - target_test_size)

    # Perform the second split on the `new_train` data using the same logic and seed.
    train_val, test_val = _perform_split(
        df=new_train,
        target_test_size=val_target_test_size,
        random_seed=random_seed,
    )

    # Write the validation output files to the new directories.
    _write_output_files(
        train_df=train_val,
        test_df=test_val,
        public_dir=public_val,
        private_dir=private_val,
        raw_dir=raw,
    )