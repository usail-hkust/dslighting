import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from mlebench.utils import read_csv


def copy(src: Path, dst: Path):
    """A wrapper for `shutil.copy` which creates destination directories when they don't exist."""

    assert src.exists(), f"{src} does not exist"
    # Allow overwriting for simplicity in rerunning the script
    if dst.exists():
        if dst.is_dir():
            shutil.rmtree(dst)
        else:
            dst.unlink()
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dst)


def _process_and_save_split(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    public_path: Path,
    private_path: Path,
    raw_path: Path,
    old_sample_submission: pd.DataFrame,
):
    """
    Helper function to process a single train/test split and save the results.
    This encapsulates the logic for creating CSVs, copying images, and running checks.
    """
    sample_submission = test_df[["image_id", "label"]].copy()
    sample_submission["label"] = ""

    # Ensure output directories exist
    public_path.mkdir(exist_ok=True)
    private_path.mkdir(exist_ok=True)

    train_df.to_csv(public_path / "train.csv", index=False)
    sample_submission.to_csv(public_path / "sample_submission.csv", index=False)
    test_df.to_csv(private_path / "test.csv", index=False)

    for row in train_df.itertuples():
        copy(
            raw_path / "train_images" / row.label / row.image_id,
            public_path / "train_images" / row.label / row.image_id,
        )

    for row in test_df.itertuples():
        copy(
            raw_path / "train_images" / row.label / row.image_id,
            public_path / "test_images" / row.image_id,
        )

    # Sanity checks (generalized for any split)
    train_image_ids = set(train_df.image_id)
    test_image_ids = set(test_df.image_id)

    assert train_image_ids.isdisjoint(test_image_ids), f"Train and test sets overlap in {public_path}!"

    assert set(train_df.columns) == set(
        test_df.columns
    ), f"Expected the new train and test sets to have the same columns, but they didn't! Got {set(train_df.columns)} != {set(test_df.columns)} in {public_path}."

    assert set(sample_submission.columns) == set(
        old_sample_submission.columns
    ), f"Expected the new sample submission to have the same columns as the original sample submission, but it didn't! Got {set(sample_submission.columns)} != {set(old_sample_submission.columns)} in {public_path}."

    assert len(list(public_path.glob("train_images/*/*.jpg"))) == len(
        train_df
    ), f"Expected the number of images in the `{public_path / 'train_images'}` directory to match the number of rows in the `{public_path / 'train.csv'}` file, but it didn't! Got {len(list(public_path.glob('train_images/*/*.jpg')))} != {len(train_df)}."

    assert len(list(public_path.glob("test_images/*.jpg"))) == len(
        test_df
    ), f"Expected the number of images in the `{public_path / 'test_images'}` directory to match the number of rows in the `{private_path / 'test.csv'}` file, but it didn't! Got {len(list(public_path.glob('test_images/*.jpg')))} != {len(test_df)}."


def prepare(raw: Path, public: Path, private: Path):
    old_train = read_csv(raw / "train.csv")
    old_sample_submission = read_csv(raw / "sample_submission.csv")

    # The original dataset has 10,407 train images and 3,469 test images.
    # This implies a 75%/25% train/test split.
    new_train, new_test = train_test_split(old_train, train_size=0.75, random_state=0)

    # Process and save the original split to `public` and `private` directories
    _process_and_save_split(
        train_df=new_train,
        test_df=new_test,
        public_path=public,
        private_path=private,
        raw_path=raw,
        old_sample_submission=old_sample_submission,
    )

    # Sanity check specific to the first split
    assert len(new_train) + len(new_test) == len(
        old_train
    ), f"Expected the combined size of the new train and test sets to be the same size as the original train set, but it wasn't! Got {len(new_train) + len(new_test)} != {len(old_train)}."

    # --- New Validation Set Creation ---
    # Define paths for the new validation split
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Perform a second split on the `new_train` set created above.
    # Use the exact same splitting parameters to replicate the logic.
    train_val, test_val = train_test_split(new_train, train_size=0.75, random_state=0)

    # Process and save the new validation split to `public_val` and `private_val`
    _process_and_save_split(
        train_df=train_val,
        test_df=test_val,
        public_path=public_val,
        private_path=private_val,
        raw_path=raw,
        old_sample_submission=old_sample_submission,
    )