import json
import shutil
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from mlebench.competitions.utils import df_to_one_hot
from mlebench.utils import read_csv


def _perform_split(
    images_to_split: pd.DataFrame, test_size: float, random_state: int
) -> Tuple[np.ndarray, np.ndarray]:
    """Performs a location-based split on the given images DataFrame."""
    image_locations = images_to_split["location"].unique()
    train_locations, test_locations = train_test_split(
        image_locations, test_size=test_size, random_state=random_state
    )

    # The original script's logic for fine-tuning the split size
    temp_train_images = images_to_split[images_to_split["location"].isin(train_locations)]
    temp_test_images = images_to_split[images_to_split["location"].isin(test_locations)]

    while len(temp_test_images) / len(images_to_split) < test_size and len(train_locations) > 1:
        location_to_move = train_locations[-1]
        train_locations = train_locations[:-1]
        test_locations = np.append(test_locations, location_to_move)
        temp_train_images = images_to_split[images_to_split["location"].isin(train_locations)]
        temp_test_images = images_to_split[images_to_split["location"].isin(test_locations)]

    while len(temp_test_images) / len(images_to_split) > test_size and len(test_locations) > 1:
        location_to_move = test_locations[-1]
        test_locations = test_locations[:-1]
        train_locations = np.append(train_locations, location_to_move)
        temp_train_images = images_to_split[images_to_split["location"].isin(train_locations)]
        temp_test_images = images_to_split[images_to_split["location"].isin(test_locations)]

    return train_locations, test_locations


def _write_dataset_files(
    public_path: Path,
    private_path: Path,
    train_images: pd.DataFrame,
    test_images: pd.DataFrame,
    train_annotations: pd.DataFrame,
    test_annotations: pd.DataFrame,
    categories_df: pd.DataFrame,
    info_json: Dict,
    test_info_json: Dict,
    raw_path: Path,
    dev_mode: bool,
):
    """Writes all the necessary files for a given train/test split to the specified paths."""
    # Create output directories
    public_path.mkdir(exist_ok=True)
    private_path.mkdir(exist_ok=True)

    # Answers
    answer_annotations = test_annotations[["image_id", "category_id"]].copy()
    answer_annotations.rename(columns={"image_id": "Id", "category_id": "Category"}, inplace=True)

    # Create a sample submission file
    sample_submission = answer_annotations.copy()
    np.random.seed(0)
    sample_submission["Category"] = np.random.randint(
        0, 676, size=len(sample_submission)
    )  # Uniform between 0 and 675

    # Reform JSON files
    new_train_json = {
        "annotations": train_annotations.to_dict(orient="records"),
        "images": train_images.to_dict(orient="records"),
        "categories": categories_df.to_dict(orient="records"),
        "info": info_json,
    }

    new_test_json = {
        "images": test_images.to_dict(orient="records"),
        "categories": pd.DataFrame(test_info_json["categories"]).to_dict(orient="records"),
        "info": test_info_json["info"],
    }

    # Write files
    answer_annotations.to_csv(private_path / "answers.csv", index=False)
    sample_submission.to_csv(public_path / "sample_submission.csv", index=False)
    with open(public_path / "iwildcam2020_train_annotations.json", "w") as f:
        json.dump(new_train_json, f)
    with open(public_path / "iwildcam2020_test_information.json", "w") as f:
        json.dump(new_test_json, f)

    # Copy over megadetector results
    shutil.copyfile(
        raw_path / "iwildcam2020_megadetector_results.json",
        public_path / "iwildcam2020_megadetector_results.json",
    )

    train_ids_to_copy = train_images["id"].unique()
    test_ids_to_copy = test_images["id"].unique()

    # Reduce the number of images copied over to 100 for dev mode
    if dev_mode:
        train_ids_to_copy = train_ids_to_copy[:100]
        test_ids_to_copy = test_ids_to_copy[:100]

    # Copy over image files
    (public_path / "train").mkdir(exist_ok=True)
    (public_path / "test").mkdir(exist_ok=True)

    print(f"Copying images to {public_path}...")
    for file_id in tqdm(train_ids_to_copy, desc="Copying train images", unit="file"):
        shutil.copyfile(
            src=raw_path / "train" / f"{file_id}.jpg",
            dst=public_path / "train" / f"{file_id}.jpg",
        )

    for file_id in tqdm(test_ids_to_copy, desc="Copying test images", unit="file"):
        shutil.copyfile(
            src=raw_path / "train" / f"{file_id}.jpg",
            dst=public_path / "test" / f"{file_id}.jpg",
        )

    # Check integrity of the files copied
    assert len(list(public_path.glob("train/*.jpg"))) == len(
        train_ids_to_copy
    ), "Number of train images should be equal to the number of unique image_id in the train set"
    assert len(list(public_path.glob("test/*.jpg"))) == len(
        test_ids_to_copy
    ), "Number of test images should be equal to the number of unique image_id in the test set"


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the data in raw into public and private datasets with appropriate test/train splits.
    Also creates a second, parallel validation split (public_val, private_val).
    """

    dev_mode = False

    # Define paths for the new validation split
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Load raw data once
    with open(raw / "iwildcam2020_train_annotations.json", "r") as file:
        old_train_json = json.load(file)
    old_train_annotations = pd.DataFrame(old_train_json["annotations"])
    old_train_images = pd.DataFrame(old_train_json["images"])
    old_train_categories = pd.DataFrame(old_train_json["categories"])

    with open(raw / "iwildcam2020_test_information.json", "r") as file:
        old_test_json = json.load(file)

    # ==================================================================
    # 1. Create the original Train / Test split
    # ==================================================================
    print("--- Creating original Train/Test split ---")
    test_size_orig = 0.22  # 62894/(217959+62894) = 0.22
    locations_train, locations_test = _perform_split(
        images_to_split=old_train_images, test_size=test_size_orig, random_state=0
    )

    # Filter original data to create the first train/test sets
    train_images = old_train_images[old_train_images["location"].isin(locations_train)]
    test_images = old_train_images[old_train_images["location"].isin(locations_test)]
    train_ids = train_images["id"].unique()
    test_ids = test_images["id"].unique()
    train_annotations = old_train_annotations[old_train_annotations["image_id"].isin(train_ids)]
    test_annotations = old_train_annotations[old_train_annotations["image_id"].isin(test_ids)]

    # Checks
    assert set(train_annotations["image_id"]).isdisjoint(
        set(test_images["id"])
    ), "Train should not contain annotations of test images"
    assert len(train_ids) + len(test_ids) == len(
        old_train_images["id"]
    ), "The combined length of new_train_ids and new_test_ids should equal the length of old_train_images"
    assert set(train_images["location"]).isdisjoint(
        set(test_images["location"])
    ), "Train and test images should not share locations"

    # Write files for the original public/private split
    _write_dataset_files(
        public_path=public,
        private_path=private,
        train_images=train_images,
        test_images=test_images,
        train_annotations=train_annotations,
        test_annotations=test_annotations,
        categories_df=old_train_categories,
        info_json=old_train_json["info"],
        test_info_json=old_test_json,
        raw_path=raw,
        dev_mode=dev_mode,
    )

    # ==================================================================
    # 2. Create the new Train / Validation split from the first training set
    # ==================================================================
    print("\n--- Creating new Train/Validation split ---")
    # The new split is performed on the `train_images` from the *first* split.
    # We calculate the test_size to make the new validation set have the same
    # number of images as the original test set.
    test_size_val = len(test_images) / len(train_images)

    locations_train_val, locations_test_val = _perform_split(
        images_to_split=train_images, test_size=test_size_val, random_state=0
    )

    # Filter the first training set to create the second (train_val/test_val) sets
    train_val_images = train_images[train_images["location"].isin(locations_train_val)]
    test_val_images = train_images[train_images["location"].isin(locations_test_val)]
    train_val_ids = train_val_images["id"].unique()
    test_val_ids = test_val_images["id"].unique()
    train_val_annotations = train_annotations[train_annotations["image_id"].isin(train_val_ids)]
    test_val_annotations = train_annotations[train_annotations["image_id"].isin(test_val_ids)]

    # Checks
    assert set(train_val_images["location"]).isdisjoint(
        set(test_val_images["location"])
    ), "Validation train and test images should not share locations"
    assert len(train_val_ids) + len(test_val_ids) == len(
        train_ids
    ), "The combined length of train_val and test_val should equal the length of the original train set"

    # Write files for the new public_val/private_val split
    _write_dataset_files(
        public_path=public_val,
        private_path=private_val,
        train_images=train_val_images,
        test_images=test_val_images,
        train_annotations=train_val_annotations,
        test_annotations=test_val_annotations,
        categories_df=old_train_categories,
        info_json=old_train_json["info"],
        test_info_json=old_test_json,
        raw_path=raw,
        dev_mode=dev_mode,
    )

    print("\nData preparation complete.")