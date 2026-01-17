import shutil
from pathlib import Path

from sklearn.model_selection import train_test_split
from tqdm.auto import tqdm

from mlebench.utils import read_csv


def _create_split(
    df_to_split,
    raw_images_base_path: Path,
    public_path: Path,
    private_path: Path,
    test_size: float,
    random_state: int,
):
    """
    Helper function to perform a data split, create corresponding files, and copy images.

    Args:
        df_to_split: The DataFrame to be split into train and test sets.
        raw_images_base_path: Path to the directory containing the original images.
        public_path: The public output directory for this split.
        private_path: The private output directory for this split.
        test_size: The proportion of the dataset to allocate to the test split.
        random_state: The seed used by the random number generator.
    """
    # Create output directories
    public_path.mkdir(exist_ok=True, parents=True)
    private_path.mkdir(exist_ok=True, parents=True)

    # Perform the split
    new_train, new_test = train_test_split(
        df_to_split, test_size=test_size, random_state=random_state
    )
    sample_submission = new_test.copy()[["image", "hotel_id"]]
    sample_submission["hotel_id"] = "36363 53586 18807 64314 60181"

    # Save public files
    new_train.to_csv(public_path / "train.csv", index=False)
    sample_submission.to_csv(public_path / "sample_submission.csv", index=False)

    # Copy images from raw to prepared/public accordingly
    (public_path / "train_images").mkdir(exist_ok=True, parents=True)
    for image, chain in tqdm(
        zip(new_train["image"], new_train["chain"]),
        total=len(new_train),
        desc=f"Train images for {public_path.name}",
    ):
        chain = str(chain)
        (public_path / "train_images" / chain).mkdir(exist_ok=True, parents=True)
        shutil.copy(
            raw_images_base_path / chain / image,
            public_path / "train_images" / chain / image,
        )

    (public_path / "test_images").mkdir(exist_ok=True, parents=True)
    for image, chain in tqdm(
        zip(new_test["image"], new_test["chain"]),
        total=len(new_test),
        desc=f"Test images for {public_path.name}",
    ):
        chain = str(chain)
        # Note: Test images are copied to a flat directory structure
        shutil.copy(raw_images_base_path / chain / image, public_path / "test_images" / image)

    # Save private files
    new_test.to_csv(private_path / "test.csv", index=False)

    # Checks
    assert len(new_train) + len(new_test) == len(
        df_to_split
    ), "Length of new_train and new_test should equal length of input dataframe"
    assert sample_submission.columns.to_list() == [
        "image",
        "hotel_id",
    ], "Sample submission columns should only be `image` and `hotel_id`"
    assert len(sample_submission) == len(new_test), "Sample submission length should match test set"
    for image, chain in zip(new_train["image"], new_train["chain"]):
        chain = str(chain)
        assert (
            public_path / "train_images" / chain / image
        ).exists(), f"Image {image} not found in train_images folder"
    for image in new_test["image"]:
        assert (
            public_path / "test_images" / image
        ).exists(), f"Image {image} not found in test_images folder"
    assert not set(new_train["image"]).intersection(
        set(new_test["image"])
    ), "Train and test ids overlap"

    return new_train, new_test


def prepare(raw: Path, public: Path, private: Path):
    old_train = read_csv(raw / "train.csv")
    # drop image ce27d36c9147cc19.jpg: it appears twice and may occur across train and test when split
    old_train = old_train[old_train["image"] != "ce27d36c9147cc19.jpg"]

    # --- First Split (Original Public/Private) ---
    # This split produces the main benchmark data. The outputs in `public` and `private`
    # will be identical to the original script's output.
    original_train_df, _ = _create_split(
        df_to_split=old_train,
        raw_images_base_path=raw / "train_images",
        public_path=public,
        private_path=private,
        test_size=0.1,
        random_state=0,
    )

    # --- Second Split (New Validation Set) ---
    # This split takes the training data from the first split (`original_train_df`) and
    # splits it again to create a new, smaller training set and a validation set.
    # The results are saved in parallel `public_val` and `private_val` directories.
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # The test size is 1/9 because we want the new validation set to be roughly the
    # same size as the original test set (10% of the total data).
    # original_train_df is 90% of the total, so 1/9 of it is 10% of the total.
    test_size_for_val_split = 1 / 9

    _create_split(
        df_to_split=original_train_df,
        raw_images_base_path=raw / "train_images",
        public_path=public_val,
        private_path=private_val,
        test_size=test_size_for_val_split,
        random_state=0,  # Use same random state for consistency and determinism
    )