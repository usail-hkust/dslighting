import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from mlebench.utils import extract, read_csv


def _process_split(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    public_dir: Path,
    private_dir: Path,
    raw_images_dir: Path,
    raw_masks_dir: Path,
    all_depths_df: pd.DataFrame,
) -> None:
    """
    Processes a single data split (e.g., train/test or train_val/test_val),
    saving all required files and performing sanity checks.

    Args:
        train_df: DataFrame for the training set.
        test_df: DataFrame for the test set.
        public_dir: The public output directory for this split.
        private_dir: The private output directory for this split.
        raw_images_dir: Path to the directory containing all source images.
        raw_masks_dir: Path to the directory containing all source masks.
        all_depths_df: DataFrame containing depth information for all samples.
    """
    public_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)

    train_ids = set(train_df["id"])
    test_ids = set(test_df["id"])

    assert train_ids.isdisjoint(test_ids), "`id` is not disjoint between train and test sets"

    train_df.sort_values(by="id").to_csv(public_dir / "train.csv", index=False)
    test_df.sort_values(by="id").to_csv(private_dir / "test.csv", index=False)

    all_source_images = set(raw_images_dir.glob("*.png"))
    train_imgs = set(img for img in all_source_images if img.stem in train_ids)
    test_imgs = set(img for img in all_source_images if img.stem in test_ids)

    assert train_imgs.isdisjoint(test_imgs), "Images are not disjoint between train and test sets"

    (public_dir / "train" / "images").mkdir(parents=True, exist_ok=True)
    (public_dir / "train" / "masks").mkdir(parents=True, exist_ok=True)

    for fpath in train_imgs:
        shutil.copyfile(src=fpath, dst=public_dir / "train" / "images" / fpath.name)
        shutil.copyfile(src=raw_masks_dir / fpath.name, dst=public_dir / "train" / "masks" / fpath.name)

    (public_dir / "test" / "images").mkdir(parents=True, exist_ok=True)

    for fpath in test_imgs:
        shutil.copyfile(src=fpath, dst=public_dir / "test" / "images" / fpath.name)

    sample_submission = test_df.drop(columns=["rle_mask"]).copy()
    sample_submission["rle_mask"] = "1 1"
    sample_submission.sort_values(by="id").to_csv(public_dir / "sample_submission.csv", index=False)

    depths_mask = all_depths_df["id"].isin(train_ids)
    filtered_depths = all_depths_df[depths_mask]
    filtered_depths.sort_values(by="id").to_csv(public_dir / "depths.csv", index=False)

    # Sanity checks
    assert (public_dir / "train.csv").exists(), "`train.csv` doesn't exist!"
    assert (public_dir / "sample_submission.csv").exists(), "`sample_submission.csv` doesn't exist!"
    assert (public_dir / "depths.csv").exists(), "`depths.csv` doesn't exist!"
    assert (public_dir / "train").exists(), "`train` directory doesn't exist!"
    assert (public_dir / "test").exists(), "`test` directory doesn't exist!"
    assert (private_dir / "test.csv").exists(), "`test.csv` doesn't exist!"

    actual_train_imgs = set(img.stem for img in (public_dir / "train" / "images").glob("*.png"))
    actual_train_masks = set(img.stem for img in (public_dir / "train" / "masks").glob("*.png"))

    assert len(actual_train_imgs) == len(train_df), "The number of images in the train set doesn't match!"
    assert len(actual_train_masks) == len(train_df), "The number of masks in the train set doesn't match!"

    for train_id in train_df["id"]:
        assert (public_dir / "train" / "images" / f"{train_id}.png").exists()
        assert (public_dir / "train" / "masks" / f"{train_id}.png").exists()

    actual_test_imgs = set(img.stem for img in (public_dir / "test" / "images").glob("*.png"))

    assert not (public_dir / "test" / "masks").exists(), f"Expected `{public_dir}/test/masks` to not exist, but it does!"
    assert len(actual_test_imgs) == len(test_df), "The number of images in the test set doesn't match!"

    for test_id in test_df["id"]:
        assert (public_dir / "test" / "images" / f"{test_id}.png").exists()
        assert not (public_dir / "test" / "masks" / f"{test_id}.png").exists()

    assert actual_train_imgs.isdisjoint(actual_test_imgs), "Image sets overlap!"

    actual_sample_submission = read_csv(public_dir / "sample_submission.csv")
    actual_test = read_csv(private_dir / "test.csv")

    assert len(actual_sample_submission) == len(actual_test), "Sample submission and test set lengths differ!"
    assert set(actual_sample_submission["id"]) == set(actual_test["id"]), "Sample submission and test set IDs differ!"
    assert len(actual_test_imgs) == len(actual_test), "Test image count and test set length differ!"
    assert set(actual_test["id"]) == actual_test_imgs, "Test set IDs and test images differ!"


def prepare(raw: Path, public: Path, private: Path) -> None:
    extract(raw / "competition_data.zip", raw)

    old_train = read_csv(raw / "competition_data" / "train.csv")
    old_train = old_train.fillna("")
    old_depths = read_csv(raw / "depths.csv")

    # Original ratio is Train set - 4,000 samples; Test set - ~18,000 samples (82% ratio)
    # We use a 0.25 ratio to get number of test samples into thousand OOM
    new_train, new_test = train_test_split(old_train, test_size=0.25, random_state=0)

    assert len(new_train) + len(new_test) == len(
        old_train
    ), "Some samples were lost when creating the new train and test sets!"

    # Create the new validation split from the `new_train` set.
    # To make `test_val` have the same size as `new_test` (25% of original),
    # we need to take 1/3 of `new_train` (since 1/3 * 75% = 25%).
    train_val, test_val = train_test_split(new_train, test_size=(1/3), random_state=0)

    assert len(train_val) + len(test_val) == len(
        new_train
    ), "Some samples were lost when creating the validation train and test sets!"

    # Define paths for raw images and new validation output directories
    raw_images_dir = raw / "competition_data" / "train" / "images"
    raw_masks_dir = raw / "competition_data" / "train" / "masks"
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Process the original split, saving to `public` and `private`
    # This block ensures the original outputs are not modified.
    _process_split(
        train_df=new_train,
        test_df=new_test,
        public_dir=public,
        private_dir=private,
        raw_images_dir=raw_images_dir,
        raw_masks_dir=raw_masks_dir,
        all_depths_df=old_depths,
    )

    # Process the new validation split, saving to `public_val` and `private_val`
    _process_split(
        train_df=train_val,
        test_df=test_val,
        public_dir=public_val,
        private_dir=private_val,
        raw_images_dir=raw_images_dir,
        raw_masks_dir=raw_masks_dir,
        all_depths_df=old_depths,
    )

    # Final checks on data types, which are consistent across all splits.
    assert new_train.applymap(
        lambda x: isinstance(x, str)
    ).values.all(), "Not all elements in the DataFrame are strings!"
    assert new_test.applymap(
        lambda x: isinstance(x, str)
    ).values.all(), "Not all elements in the DataFrame are strings!"