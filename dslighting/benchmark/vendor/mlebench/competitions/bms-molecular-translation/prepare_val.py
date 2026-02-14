import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm


def make_image_subpath(image_id: str) -> Path:
    """
    Creates a triple-nested directory structure from the first 3 characters of the image_id.
    """
    subpath = Path(image_id[0]) / image_id[1] / image_id[2] / f"{image_id}.png"
    return subpath


def _create_split_files(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    raw_images_path: Path,
    public_path: Path,
    private_path: Path,
):
    """
    Helper function to generate the directory structure and files for a given split.
    This function populates the public and private directories with train/test data,
    images, and a sample submission file.
    """
    # Create output directories
    public_path.mkdir(exist_ok=True)
    private_path.mkdir(exist_ok=True)

    # Save dataframes
    train_df.to_csv(public_path / "train_labels.csv", index=False)
    test_df.to_csv(private_path / "test.csv", index=False)

    # Copy train files
    desc_prefix = public_path.name
    for _, row in tqdm(train_df.iterrows(), total=len(train_df), desc=f"Copying {desc_prefix} train images"):
        image_id = row["image_id"]
        src = raw_images_path / make_image_subpath(image_id)
        dst = public_path / "train" / make_image_subpath(image_id)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src=src, dst=dst)

    # Copy test files
    for _, row in tqdm(test_df.iterrows(), total=len(test_df), desc=f"Copying {desc_prefix} test images"):
        image_id = row["image_id"]
        src = raw_images_path / make_image_subpath(image_id)
        dst = public_path / "test" / make_image_subpath(image_id)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src=src, dst=dst)

    # Create sample submission
    sample_submission = test_df.copy()
    sample_submission["InChI"] = "InChI=1S/H2O/h1H2"
    sample_submission.to_csv(public_path / "sample_submission.csv", index=False)

    # Checks
    assert len(list((public_path / "train").glob("**/*.png"))) == len(
        train_df
    ), f"Expected {len(train_df)} train images in {public_path}/train, but got {len(list((public_path / 'train').glob('**/*.png')))}"
    assert len(list((public_path / "test").glob("**/*.png"))) == len(
        test_df
    ), f"Expected {len(test_df)} test images in {public_path}/test, but got {len(list((public_path / 'test').glob('**/*.png')))}"

    assert "image_id" in sample_submission.columns, "Sample submission must have 'image_id' column"
    assert "InChI" in sample_submission.columns, "Sample submission must have 'InChI' column"
    assert len(sample_submission) == len(
        test_df
    ), f"Expected {len(test_df)} images in sample submission, but got {len(sample_submission)}"


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the data in raw into public and private datasets with appropriate test/train splits.
    Also creates a secondary validation split in parallel public_val and private_val directories.
    """
    # Load train data
    old_train = pd.read_csv(raw / "train_labels.csv")

    # ---- 1. Create the original train/test split ----
    # This split is for the main competition test set.
    new_train, new_test = train_test_split(old_train, test_size=0.2, random_state=0)

    # Generate the files for the original public and private directories
    _create_split_files(
        train_df=new_train,
        test_df=new_test,
        raw_images_path=raw / "train",
        public_path=public,
        private_path=private,
    )

    # ---- 2. Create the new validation split ----
    # This second split is performed on the `new_train` set created above.
    # We want the new `test_val` to be the same size as the original `new_test`.
    # Original test size = 0.2 * total. Original train size = 0.8 * total.
    # New test size relative to train set = 0.2 / 0.8 = 0.25
    train_val, test_val = train_test_split(new_train, test_size=0.25, random_state=0)

    # Define the new parallel directories for the validation set
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Generate the files for the new validation directories
    _create_split_files(
        train_df=train_val,
        test_df=test_val,
        raw_images_path=raw / "train",
        public_path=public_val,
        private_path=private_val,
    )

    # ---- 3. Copy shared files and run final checks ----

    # Copy other files into both public and public_val directories
    shutil.copyfile(src=raw / "extra_approved_InChIs.csv", dst=public / "extra_approved_InChIs.csv")
    shutil.copyfile(src=raw / "extra_approved_InChIs.csv", dst=public_val / "extra_approved_InChIs.csv")

    # Original split checks
    assert len(new_train) + len(new_test) == len(
        old_train
    ), f"Expected {len(old_train)} total images in new_train ({len(new_train)}) and new_test ({len(new_test)})"

    # New validation split checks
    assert len(train_val) + len(test_val) == len(
        new_train
    ), f"Expected {len(new_train)} total images in train_val ({len(train_val)}) and test_val ({len(test_val)})"
    # Ensure the size of the validation test set is approx. the same as the original test set
    assert abs(len(test_val) - len(new_test)) <= 1, "Validation test set size should match original test set size"