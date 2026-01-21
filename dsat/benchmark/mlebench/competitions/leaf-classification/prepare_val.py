import shutil
from pathlib import Path

from pandas import DataFrame
from sklearn.model_selection import train_test_split

from mlebench.competitions.utils import df_to_one_hot
from mlebench.utils import extract, read_csv

from .classes import CLASSES


def _create_split_and_save(
    source_df: DataFrame,
    image_source_dir: Path,
    public_dir: Path,
    private_dir: Path,
    test_size: float,
    random_state: int,
) -> DataFrame:
    """Helper function to perform a split, copy images, and save all artifacts."""
    # Create train, test from the source dataframe
    new_train, new_test = train_test_split(
        source_df, test_size=test_size, random_state=random_state
    )
    new_test_without_labels = new_test.drop(columns=["species"])

    # match the format of the sample submission
    new_test = new_test[["id", "species"]]
    new_test = df_to_one_hot(new_test, "id", "species", classes=CLASSES)

    # Create destination directories
    (public_dir / "images").mkdir(parents=True, exist_ok=True)
    (private_dir / "images").mkdir(parents=True, exist_ok=True)

    # Copy images for the new training set
    for file_id in new_train["id"]:
        shutil.copyfile(
            src=image_source_dir / f"{file_id}.jpg",
            dst=public_dir / "images" / f"{file_id}.jpg",
        )

    # Copy images for the new test set
    for file_id in new_test_without_labels["id"]:
        shutil.copyfile(
            src=image_source_dir / f"{file_id}.jpg",
            dst=public_dir / "images" / f"{file_id}.jpg",
        )

    # Check integrity of the files copied
    assert len(new_test_without_labels) == len(
        new_test
    ), "Public and Private tests should have equal length"
    assert len(list(public_dir.glob("images/*.jpg"))) == len(new_train) + len(
        new_test_without_labels
    ), "Public images should have the same number of images as the sum of train and test"

    # Create a sample submission file
    submission_df = new_test.copy()
    submission_df[CLASSES] = 1 / len(CLASSES)

    # Save all dataframes to their respective files
    new_train.to_csv(public_dir / "train.csv", index=False)
    new_test.to_csv(private_dir / "test.csv", index=False)
    new_test_without_labels.to_csv(public_dir / "test.csv", index=False)
    submission_df.to_csv(public_dir / "sample_submission.csv", index=False)

    return new_train


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the data in raw into public and private datasets with appropriate test/train splits.
    Also creates a secondary validation split in public_val/private_val directories.
    """
    # extract only what we need
    extract(raw / "train.csv.zip", raw)
    extract(raw / "images.zip", raw)

    # Load the full raw training data
    full_train_df = read_csv(raw / "train.csv")
    image_source_dir = raw / "images"

    # --- Stage 1: Create the original train/test split ---
    # This block generates the primary competition data in `public/` and `private/`.
    # The outputs of this stage must remain unchanged from the original script.
    train_df_after_first_split = _create_split_and_save(
        source_df=full_train_df,
        image_source_dir=image_source_dir,
        public_dir=public,
        private_dir=private,
        test_size=0.1,
        random_state=0,
    )

    # --- Stage 2: Create the new train/validation split ---
    # This block takes the training set from Stage 1 and splits it again
    # to create a new, smaller training set and a validation set.
    # The outputs are saved to new `public_val/` and `private_val/` directories.

    # Define paths for the new validation split
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Calculate test_size to make the new validation set have the same number
    # of samples as the original test set (0.1 / (1-0.1) = 0.1 / 0.9)
    validation_test_size = 0.1 / 0.9

    _create_split_and_save(
        source_df=train_df_after_first_split,
        image_source_dir=image_source_dir,
        public_dir=public_val,
        private_dir=private_val,
        test_size=validation_test_size,
        random_state=0,  # Use the same random state for consistency
    )