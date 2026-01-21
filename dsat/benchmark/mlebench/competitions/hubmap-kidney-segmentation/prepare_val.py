import shutil
from pathlib import Path
import pandas as pd

from sklearn.model_selection import train_test_split
from tqdm.auto import tqdm

from mlebench.utils import read_csv


def _create_split_files(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    full_dataset_info: pd.DataFrame,
    raw_path: Path,
    public_path: Path,
    private_path: Path,
):
    """
    Helper function to generate all required files for a given train/test split.

    This function encapsulates the logic of creating CSVs, sample submissions,
    and copying image files to ensure that the process is identical for both
    the main split (public/private) and the validation split (public_val/private_val).
    """
    # Create output directories
    public_path.mkdir(parents=True, exist_ok=True)
    private_path.mkdir(parents=True, exist_ok=True)
    (public_path / "train").mkdir(parents=True, exist_ok=True)
    (public_path / "test").mkdir(parents=True, exist_ok=True)

    # Process and save data files
    dataset_info = full_dataset_info.drop(columns=["id"], inplace=False)
    dataset_info.to_csv(public_path / "HuBMAP-20-dataset_information.csv", index=False)

    train_df.to_csv(public_path / "train.csv", index=False)

    # Put height and width in test_df, for grading
    private_test_df = test_df.merge(full_dataset_info[["id", "width_pixels", "height_pixels"]], on="id")
    private_test_df.to_csv(private_path / "test.csv", index=False)

    sample_submission = private_test_df[["id"]].copy()
    sample_submission["predicted"] = ""
    sample_submission.to_csv(public_path / "sample_submission.csv", index=False)
    # for some reason sample_submission.csv is also in test/
    shutil.copy(public_path / "sample_submission.csv", public_path / "test" / "sample_submission.csv")

    # basically the same as private_test_df but with a different column name
    gold_submission = sample_submission.copy()
    gold_submission["predicted"] = private_test_df["encoding"]
    gold_submission.to_csv(private_path / "gold_submission.csv", index=False)

    # Copy image files
    for image_id in tqdm(train_df["id"], desc=f"Copying train images to {public_path.name}"):
        shutil.copy(raw_path / "train" / f"{image_id}.tiff", public_path / "train" / f"{image_id}.tiff")
        shutil.copy(raw_path / "train" / f"{image_id}.json", public_path / "train" / f"{image_id}.json")
        shutil.copy(
            raw_path / "train" / f"{image_id}-anatomical-structure.json",
            public_path / "train" / f"{image_id}-anatomical-structure.json",
        )

    for image_id in tqdm(private_test_df["id"], desc=f"Copying test images to {public_path.name}"):
        shutil.copy(raw_path / "train" / f"{image_id}.tiff", public_path / "test" / f"{image_id}.tiff")
        shutil.copy(raw_path / "train" / f"{image_id}.json", public_path / "test" / f"{image_id}.json")
        shutil.copy(
            raw_path / "train" / f"{image_id}-anatomical-structure.json",
            public_path / "test" / f"{image_id}-anatomical-structure.json",
        )

    # Checks
    assert train_df.columns.to_list() == [
        "id",
        "encoding",
    ], f"Public train set in {public_path.name} should have 2 columns, called 'id' and 'encoding'"
    assert private_test_df.columns.to_list() == [
        "id",
        "encoding",
        "width_pixels",
        "height_pixels",
    ], f"Private test set in {private_path.name} should have 4 columns"

    assert len(sample_submission) == len(private_test_df), "Sample submission length should match test set"
    assert sample_submission.columns.to_list() == [
        "id",
        "predicted",
    ], "Sample submissions should have two columns, 'id' and 'predicted'"

    assert len(gold_submission) == len(private_test_df), "Gold submission length should match test set"
    assert gold_submission.columns.to_list() == [
        "id",
        "predicted",
    ], "Gold submissions should have two columns, 'id' and 'predicted'"

    assert gold_submission["predicted"].equals(
        private_test_df["encoding"]
    ), "Gold submission should match private test set"

    assert set(train_df["id"]).isdisjoint(
        set(private_test_df["id"])
    ), "Train and test ids should not overlap"

    assert len(list((public_path / "train").glob("*.tiff"))) == len(
        train_df
    ), f"Missing train tiff files in {public_path.name}"
    assert len(list((public_path / "train").glob("*-anatomical-structure.json"))) == len(
        train_df
    ), f"Missing train structure json files in {public_path.name}"
    assert (
        len(list((public_path / "train").glob("*.json"))) == len(train_df) * 2
    ), f"Missing train json files in {public_path.name}"

    assert len(list((public_path / "test").glob("*.tiff"))) == len(private_test_df), f"Missing test tiff files in {public_path.name}"
    assert len(list((public_path / "test").glob("*-anatomical-structure.json"))) == len(
        private_test_df
    ), f"Missing test structure json files in {public_path.name}"


def prepare(raw: Path, public: Path, private: Path):

    old_train = read_csv(raw / "train.csv")
    old_dataset_info = read_csv(raw / "HuBMAP-20-dataset_information.csv")

    # --- First Split: Create the main train and test sets ---
    # This split is identical to the original script to ensure public/private are not changed.
    new_train, new_test = train_test_split(old_train, train_size=12, test_size=3, random_state=0)
    
    # Process dataset_info once. This info is based on the full original train set
    # and will be used for both the main and validation splits.
    old_dataset_info["id"] = old_dataset_info["image_file"].str.replace(".tiff", "")
    dataset_info = old_dataset_info[old_dataset_info["id"].isin(old_train["id"])]
    
    # Create the original public and private directories and their contents.
    # The results of this call will be IDENTICAL to the original script's output.
    _create_split_files(new_train, new_test, dataset_info, raw, public, private)
    
    # --- Second Split: Create a validation set from the main train set ---
    # This creates a new, smaller training set and a validation set.
    # The outputs are saved to parallel 'public_val' and 'private_val' directories.
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Split new_train (12 samples) into train_val (9) and test_val (3).
    # This replicates the test set size (3) and random_state (0) from the first split.
    train_val, test_val = train_test_split(new_train, train_size=9, test_size=3, random_state=0)

    # Create the new validation directories and their contents.
    # The file structure and names inside these directories will mirror the original ones.
    _create_split_files(train_val, test_val, dataset_info, raw, public_val, private_val)

    # Final check from original script
    assert len(new_train) + len(new_test) == len(
        old_train
    ), "Length of new_train and new_test should equal length of old_train"