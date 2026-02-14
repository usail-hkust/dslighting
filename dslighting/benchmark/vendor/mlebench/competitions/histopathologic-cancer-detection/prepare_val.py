import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm


def _create_split(
    df_to_split: pd.DataFrame,
    image_source_dir: Path,
    test_split_size: float,
    public_dest: Path,
    private_dest: Path,
    random_state: int,
) -> pd.DataFrame:
    """
    Splits a dataframe of labels, copies corresponding images, and saves the results.

    Args:
        df_to_split: DataFrame containing image IDs and labels to be split.
        image_source_dir: Path to the directory containing the source images.
        test_split_size: The proportion of the dataset to allocate to the test split.
        public_dest: The destination directory for public-facing files (train set, test images, sample submission).
        private_dest: The destination directory for private files (test set answers).
        random_state: The seed used by the random number generator for the split.

    Returns:
        The training portion of the split as a pandas DataFrame.
    """
    # Create destination directories
    public_dest.mkdir(exist_ok=True, parents=True)
    private_dest.mkdir(exist_ok=True, parents=True)
    (public_dest / "train").mkdir(exist_ok=True)
    (public_dest / "test").mkdir(exist_ok=True)

    # Perform the split
    train_ids, test_ids = train_test_split(
        df_to_split["id"], test_size=test_split_size, random_state=random_state
    )
    train_df = df_to_split[df_to_split["id"].isin(train_ids)]
    test_df = df_to_split[df_to_split["id"].isin(test_ids)]

    assert set(train_df["id"]).isdisjoint(
        set(test_df["id"])
    ), "Train should not contain id's of test images"
    assert len(train_ids) + len(test_ids) == len(
        df_to_split
    ), "The combined length of train_ids and test_ids should equal the length of the source df"

    # Copy over image files
    for file_id in tqdm(train_ids, desc=f"Copying train images to {public_dest}"):
        shutil.copyfile(
            src=image_source_dir / f"{file_id}.tif",
            dst=public_dest / "train" / f"{file_id}.tif",
        )
    for file_id in tqdm(test_ids, desc=f"Copying test images to {public_dest}"):
        shutil.copyfile(
            src=image_source_dir / f"{file_id}.tif",
            dst=public_dest / "test" / f"{file_id}.tif",
        )

    # Create and save label/submission files
    sample_submission = test_df.copy()
    sample_submission["label"] = 0

    train_df.to_csv(public_dest / "train_labels.csv", index=False)
    test_df.to_csv(private_dest / "answers.csv", index=False)
    sample_submission.to_csv(public_dest / "sample_submission.csv", index=False)

    # Check integrity of files copied
    assert len(list(public_dest.glob("train/*.tif"))) == len(
        train_ids
    ), "Number of train images should be equal to the number of unique id's in the train set"
    assert len(list(public_dest.glob("test/*.tif"))) == len(
        test_ids
    ), "Number of test images should be equal to the number of unique id's in the test set"

    return train_df


def prepare(raw: Path, public: Path, private: Path):
    """
    Prepares the data for the competition by performing two splits.
    1. A main split of the raw data into a primary train/test set for the competition.
       Outputs are saved to `public/` and `private/`.
    2. A secondary split of the primary train set into a smaller train/validation set for user convenience.
       Outputs are saved to `public_val/` and `private_val/`, mirroring the main structure.
    """
    # Common setup
    all_train_labels = pd.read_csv(raw / "train_labels.csv")
    image_source_dir = raw / "train"
    RANDOM_STATE = 0

    # --- 1. Main Split: Create the primary train/test sets ---
    # This logic is identical to the original script to ensure outputs do not change.
    num_test_from_pool = len(list((raw / "test").glob("*.tif")))
    test_ratio_main = num_test_from_pool / (len(all_train_labels) + num_test_from_pool)

    # The returned `primary_train_df` is the larger portion of the first split.
    primary_train_df = _create_split(
        df_to_split=all_train_labels,
        image_source_dir=image_source_dir,
        test_split_size=test_ratio_main,
        public_dest=public,
        private_dest=private,
        random_state=RANDOM_STATE,
    )

    # --- 2. Validation Split: Create a secondary train/validation set ---
    # Define new output paths for the validation split
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # To get the same number of test samples as the main split, we must adjust the test_size
    # for this second split, which operates on a smaller dataset (the primary_train_df).
    if (1 - test_ratio_main) <= 0:
        # Avoid division by zero in the unlikely case the main split uses all data for test
        test_ratio_val = 0
    else:
        test_ratio_val = test_ratio_main / (1 - test_ratio_main)

    # Perform the second split on the primary training data
    _create_split(
        df_to_split=primary_train_df,
        image_source_dir=image_source_dir,
        test_split_size=test_ratio_val,
        public_dest=public_val,
        private_dest=private_val,
        random_state=RANDOM_STATE,
    )