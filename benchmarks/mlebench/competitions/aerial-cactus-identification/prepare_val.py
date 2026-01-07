import shutil
from pathlib import Path
import pandas as pd

from sklearn.model_selection import train_test_split
from tqdm.auto import tqdm

from mlebench.utils import compress, extract, read_csv


def _process_and_save_split(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    public_dir: Path,
    private_dir: Path,
    raw_image_dir: Path,
    original_df: pd.DataFrame,
):
    """
    Helper function to process a single train/test split.
    It saves all required CSVs, copies and compresses images, and runs assertions.
    """
    public_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the dataframes
    train_df.to_csv(public_dir / "train.csv", index=False)
    test_df.to_csv(private_dir / "test.csv", index=False)

    sample_submission = test_df.copy()
    sample_submission["has_cactus"] = 0.5
    sample_submission.to_csv(public_dir / "sample_submission.csv", index=False)

    # Prepare temporary directories for images
    temp_train_img_dir = public_dir / "train"
    temp_test_img_dir = public_dir / "test"
    temp_train_img_dir.mkdir(parents=True, exist_ok=True)
    temp_test_img_dir.mkdir(parents=True, exist_ok=True)

    # Copy images for the current split
    for image_id in tqdm(train_df["id"], desc=f"Copying train images to {public_dir.name}", total=len(train_df)):
        shutil.copy(raw_image_dir / image_id, temp_train_img_dir / image_id)

    for image_id in tqdm(test_df["id"], desc=f"Copying test images to {public_dir.name}", total=len(test_df)):
        shutil.copy(raw_image_dir / image_id, temp_test_img_dir / image_id)

    # and then recompress
    compress(temp_train_img_dir, public_dir / "train.zip")
    compress(temp_test_img_dir, public_dir / "test.zip")

    # and cleanup temporary image directories
    shutil.rmtree(temp_train_img_dir)
    shutil.rmtree(temp_test_img_dir)

    # checks for the current split
    assert (public_dir / "train.zip").exists(), f"{public_dir.name}/train.zip should exist"
    assert (public_dir / "test.zip").exists(), f"{public_dir.name}/test.zip should exist"

    assert len(train_df) + len(test_df) == len(
        original_df
    ), "The lengths of the splits should add up to the original"
    assert len(train_df) > len(test_df), "The train set should be larger than the test set"
    assert len(test_df) == len(
        sample_submission
    ), "The test set should match the sample submission"

    assert (
        train_df.columns.tolist()
        == test_df.columns.tolist()
        == original_df.columns.tolist()
        == sample_submission.columns.tolist()
    ), "All dataframes should have the same columns, i.e. ['id', 'has_cactus']"

    assert set(train_df["id"]).isdisjoint(test_df["id"]), "Train and test ids should not overlap"
    assert set(test_df["id"]) == set(
        sample_submission["id"]
    ), "Test and sample_submission ids should match"

    assert train_df["id"].nunique() == len(train_df), "There should be no duplicate ids in train"
    assert test_df["id"].nunique() == len(test_df), "There should be no duplicate ids in test"


def prepare(raw: Path, public: Path, private: Path):

    old_train = read_csv(raw / "train.csv")
    
    # need to split the train.zip into train.zip and test.zip; to do so need to extract first
    extract(raw / "train.zip", raw)
    raw_image_dir = raw / "train"

    # --- 1. Original Split: Create main train and test sets ---
    # This block creates the original public/private outputs, which must remain unchanged.
    
    # 4000 / (4000 + 17500) -> test_size is ~0.19
    new_train, new_test = train_test_split(old_train, test_size=0.19, random_state=0)
    
    _process_and_save_split(
        train_df=new_train,
        test_df=new_test,
        public_dir=public,
        private_dir=private,
        raw_image_dir=raw_image_dir,
        original_df=old_train,
    )
    
    # --- 2. New Validation Split: Create a validation set from the main train set ---
    # This block creates the new public_val/private_val outputs.
    
    # Define paths for the new validation split artifacts
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # To make the new validation set (test_val) have the same size as the original
    # test set (new_test), we calculate the required test_size proportion.
    test_size_for_val_split = len(new_test) / len(new_train)
    
    # Split the main training set (new_train) into a smaller training set (train_val)
    # and a validation set (test_val), using the same random_state for consistency.
    train_val, test_val = train_test_split(new_train, test_size=test_size_for_val_split, random_state=0)

    _process_and_save_split(
        train_df=train_val,
        test_df=test_val,
        public_dir=public_val,
        private_dir=private_val,
        raw_image_dir=raw_image_dir,
        original_df=new_train,
    )

    # --- Final Cleanup ---
    # and cleanup the extracted raw image directory, which is no longer needed
    shutil.rmtree(raw_image_dir)
    assert not (raw / "train").exists(), "raw/train/ should not exist"