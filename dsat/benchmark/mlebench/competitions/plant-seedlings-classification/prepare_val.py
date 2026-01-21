import os
import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from mlebench.utils import extract, read_csv


def create_dataframe_from_directory(directory: str) -> pd.DataFrame:
    """
    Creates a DataFrame from a directory of images.

    Args:
        directory (str): The path to the directory containing subdirectories of images.

    Returns:
        pd.DataFrame: A DataFrame with two columns: 'image' and 'label'. The 'image' column contains the file paths to the images, and the 'label' column contains the corresponding labels (subdirectory names).
    """
    data = []
    for label in sorted(os.listdir(directory)):  # Sort labels for determinism
        label_path = os.path.join(directory, label)
        if os.path.isdir(label_path):
            for file_name in sorted(os.listdir(label_path)):  # Sort files for determinism
                if file_name.endswith(".png"):
                    file_path = os.path.join(label_path, file_name)
                    data.append({"file": os.path.basename(file_path), "species": label})
    return pd.DataFrame(data)


def _process_split(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    public_path: Path,
    private_path: Path,
    source_images_dir: Path,
):
    """
    Helper function to process a train/test split and write all necessary files and folders.
    This function creates the public and private directories, generates CSVs, and copies image files.
    """
    # Ensure destination directories exist
    public_path.mkdir(exist_ok=True)
    private_path.mkdir(exist_ok=True)

    # Create a sample submission file
    submission_df = test_df.copy()
    submission_df["species"] = "Sugar beet"

    # Checks
    assert len(test_df) == len(submission_df), "Answers and submission should have the same length"
    assert not set(train_df["file"]).intersection(
        set(test_df["file"])
    ), "new_train and answers should not share any image"
    assert (
        "file" in train_df.columns and "species" in train_df.columns
    ), "Train DataFrame must have 'file' and 'species' columns"
    assert (
        "file" in submission_df.columns and "species" in submission_df.columns
    ), "Sample submission DataFrame must have 'file' and 'species' columns"

    # Write CSVs
    test_df.to_csv(private_path / "answers.csv", index=False)
    submission_df.to_csv(public_path / "sample_submission.csv", index=False)

    # Prepare image directories
    public_test_images_path = public_path / "test"
    public_train_images_path = public_path / "train"
    public_test_images_path.mkdir(exist_ok=True)
    public_train_images_path.mkdir(exist_ok=True)

    # Create nested folder structure for train
    for species in train_df["species"].unique():
        (public_train_images_path / species).mkdir(parents=True, exist_ok=True)

    # Use public path name for progress bar description
    desc_prefix = public_path.name.capitalize()

    for _, row in tqdm(
        train_df.iterrows(), desc=f"Copying {desc_prefix} Train Images", total=len(train_df)
    ):
        src_path = source_images_dir / row["species"] / row["file"]
        dst_path = public_train_images_path / row["species"] / row["file"]
        shutil.copyfile(src=src_path, dst=dst_path)

    for _, row in tqdm(
        test_df.iterrows(), desc=f"Copying {desc_prefix} Test Images", total=len(test_df)
    ):
        src_path = source_images_dir / row["species"] / row["file"]
        dst_path = public_test_images_path / row["file"]
        shutil.copyfile(src=src_path, dst=dst_path)

    # Final checks on copied files
    assert len(list(public_train_images_path.glob("**/*.png"))) == len(
        train_df
    ), f"Public train images should have the same number of images as the train DataFrame: number of files {len(list(public_train_images_path.glob('**/*.png')))} != len(train_df)={len(train_df)}"
    assert len(list(public_test_images_path.glob("*.png"))) == len(
        test_df
    ), f"Public test images should have the same number of images as the answers DataFrame: number of files {len(list(public_test_images_path.glob('*.png')))} != len(test_df)={len(test_df)}"


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the data in raw into public and private datasets with appropriate test/train splits.
    It then creates a secondary validation split (public_val, private_val) from the main training data.
    """
    # Directory containing the original images
    train_dir = raw / "train"
    old_train = create_dataframe_from_directory(train_dir)
    test_ratio = 0.14  # 794/(4750+794) = 0.14

    # --- 1. Original Split: Create main train and test sets ---
    train_df, test_df = train_test_split(old_train, test_size=test_ratio, random_state=0)

    # Check for original split integrity
    assert len(train_df) + len(test_df) == len(
        old_train
    ), "The combined length of new_train and answers should equal the length of old_train"

    # Process and save the original split to public/ and private/
    # This generates the original, unmodified competition output.
    _process_split(
        train_df=train_df,
        test_df=test_df,
        public_path=public,
        private_path=private,
        source_images_dir=train_dir,
    )

    # --- 2. New Validation Split: Split the main train_df again ---
    # Define paths for the new validation dataset, parallel to the original ones.
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Calculate the new test ratio to make the validation set (test_val_df)
    # approximately the same size as the original test set (test_df).
    new_test_ratio = len(test_df) / len(train_df)

    # Split the training data to create a new, smaller training set and a validation set.
    # We use the same random_state for reproducibility and consistency with the first split.
    train_val_df, test_val_df = train_test_split(train_df, test_size=new_test_ratio, random_state=0)

    # Check for new split integrity
    assert (
        len(train_val_df) + len(test_val_df) == len(train_df)
    ), "The combined length of train_val_df and test_val_df should equal the length of train_df"

    # Process and save the new validation split to public_val/ and private_val/
    # Using the same helper ensures an identical file and directory structure.
    _process_split(
        train_df=train_val_df,
        test_df=test_val_df,
        public_path=public_val,
        private_path=private_val,
        source_images_dir=train_dir,
    )