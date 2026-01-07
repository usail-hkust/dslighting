import json
import random
import shutil
from pathlib import Path
from typing import Dict, List

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from mlebench.utils import get_logger

logger = get_logger(__name__)


def _split_data_by_category(
    data_by_category: Dict[int, List[dict]],
) -> (Dict[int, List[dict]], Dict[int, List[dict]]):
    """
    Splits data within each category into train and test sets.

    This function replicates the original script's splitting logic to ensure
    consistency.
    """
    train_split_by_category = {}
    test_split_by_category = {}

    for category_id, annotations_images in data_by_category.items():
        test_size = 0.2
        n_samples = len(annotations_images)
        if n_samples == 1:
            train_annotations_images = annotations_images
            test_annotations_images = []
        elif n_samples < 5:
            test_size = max(1, int(n_samples * test_size))
            train_annotations_images = annotations_images[:-test_size]
            test_annotations_images = annotations_images[-test_size:]
        else:
            train_annotations_images, test_annotations_images = train_test_split(
                annotations_images, test_size=test_size, random_state=0
            )
        train_split_by_category[category_id] = train_annotations_images
        test_split_by_category[category_id] = test_annotations_images
    return train_split_by_category, test_split_by_category


def _process_and_save_split(
    train_data_by_cat: Dict[int, List[dict]],
    test_data_by_cat: Dict[int, List[dict]],
    base_metadata: dict,
    public_dir: Path,
    private_dir: Path,
    raw_data_path: Path,
    dev_mode: bool,
    dev_count: int,
):
    """
    Processes and saves a single train/test split to the specified directories.

    This function handles:
    - Creating training set metadata and copying images.
    - Creating test set metadata and copying/renaming images.
    - Creating private ground-truth answers.
    - Creating a public sample submission file.
    """
    # Create required directories
    public_dir.mkdir(exist_ok=True, parents=True)
    private_dir.mkdir(exist_ok=True, parents=True)
    (public_dir / "train/images").mkdir(exist_ok=True, parents=True)
    (public_dir / "test/images").mkdir(exist_ok=True, parents=True)

    # Process train set
    new_train_metadata = base_metadata.copy()
    new_train_metadata.update({"annotations": [], "images": []})
    train_sample_count = sum(len(v) for v in train_data_by_cat.values())

    with tqdm(
        desc=f"Creating train set for {public_dir.name}",
        total=train_sample_count,
    ) as pbar:
        for category_id, annotations_images in train_data_by_cat.items():
            category_subdir = f"{category_id // 100:03d}/{category_id % 100:02d}"
            (public_dir / "train/images" / category_subdir).mkdir(exist_ok=True, parents=True)
            for idx, annotation_image in enumerate(annotations_images):
                new_train_metadata["annotations"].append(annotation_image["annotation"].copy())
                new_train_metadata["images"].append(annotation_image["image"].copy())

                if not dev_mode or idx < dev_count:
                    src_path = raw_data_path / "train" / annotation_image["image"]["file_name"]
                    dst_path = public_dir / "train" / annotation_image["image"]["file_name"]
                    shutil.copyfile(src=src_path, dst=dst_path)
                pbar.update(1)

    with open(public_dir / "train/metadata.json", "w") as f:
        json.dump(new_train_metadata, f, indent=4, sort_keys=True)

    # Process test set
    new_test_metadata = base_metadata.copy()
    for key_to_del in ["categories", "institutions"]:
        if key_to_del in new_test_metadata:
            del new_test_metadata[key_to_del]
    new_test_metadata.update({"annotations": [], "images": []})

    test_annotations_images = [
        item for sublist in test_data_by_cat.values() for item in sublist
    ]
    random.Random(0).shuffle(test_annotations_images)

    for idx, annotation_image in tqdm(
        enumerate(test_annotations_images),
        desc=f"Creating test set for {public_dir.name}",
        total=len(test_annotations_images),
    ):
        new_image_id = str(idx)
        new_file_name = f"images/{idx // 1000:03d}/{idx}.jpg"

        new_annotation = annotation_image["annotation"].copy()
        new_annotation["image_id"] = new_image_id
        new_test_metadata["annotations"].append(new_annotation)

        new_image = annotation_image["image"].copy()
        new_image["id"] = new_image_id
        new_image["file_name"] = new_file_name
        new_test_metadata["images"].append(new_image)

        if not dev_mode or idx < dev_count:
            src_path = raw_data_path / "train" / annotation_image["image"]["file_name"]
            dst_path = public_dir / "test" / new_file_name
            dst_path.parent.mkdir(exist_ok=True, parents=True)
            shutil.copyfile(src=src_path, dst=dst_path)

    # Save public test metadata (without answers)
    public_new_test = new_test_metadata.copy()
    del public_new_test["annotations"]
    with open(public_dir / "test/metadata.json", "w") as f:
        json.dump(public_new_test, f, indent=4, sort_keys=True)

    # Save private test answers
    answers_rows = [
        {"Id": img["id"], "Predicted": ann["category_id"]}
        for img, ann in zip(new_test_metadata["images"], new_test_metadata["annotations"])
    ]
    pd.DataFrame(answers_rows).to_csv(private_dir / "answers.csv", index=False)

    # Save public sample submission
    sample_rows = [{"Id": img["id"], "Predicted": 0} for img in new_test_metadata["images"]]
    pd.DataFrame(sample_rows).to_csv(public_dir / "sample_submission.csv", index=False)


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the raw data into public and private datasets with appropriate test/train splits.

    This script now performs two splits:
    1.  raw -> train + test (saved to `public`/`private`)
    2.  train -> train_val + test_val (saved to `public_val`/`private_val`)

    The second split uses the exact same logic as the first, creating a smaller
    dataset for validation that mirrors the structure of the main one.
    """
    dev_mode = False
    dev_count = 2

    # --- Start: New code for managing validation paths ---
    # Define and create the new parallel directories for the validation set
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"
    public_val.mkdir(exist_ok=True)
    private_val.mkdir(exist_ok=True)
    # --- End: New code for managing validation paths ---

    json_path = raw / "train/metadata.json"
    with open(json_path, "r", encoding="utf-8") as f:
        old_train_metadata = json.load(f)

    annotations_images_by_category = {}
    for annotation, image in list(
        zip(old_train_metadata["annotations"], old_train_metadata["images"])
    ):
        category_id = annotation["category_id"]
        if category_id not in annotations_images_by_category:
            annotations_images_by_category[category_id] = []
        annotations_images_by_category[category_id].append(
            {"annotation": annotation, "image": image}
        )

    # --- SPLIT 1: Create the original train and test sets ---
    logger.info("Starting initial split: raw -> train + test")
    train_annotations_images_by_category, test_annotations_images_by_category = (
        _split_data_by_category(annotations_images_by_category)
    )

    _process_and_save_split(
        train_data_by_cat=train_annotations_images_by_category,
        test_data_by_cat=test_annotations_images_by_category,
        base_metadata=old_train_metadata,
        public_dir=public,
        private_dir=private,
        raw_data_path=raw,
        dev_mode=dev_mode,
        dev_count=dev_count,
    )
    logger.info(f"Original train/test sets saved to {public.name} and {private.name}")

    # --- SPLIT 2: Create the new validation sets from the training set of SPLIT 1 ---
    logger.info("Starting second split: train -> train_val + test_val")
    # The input to this split is the *training data* from the first split
    train_val_by_category, test_val_by_category = _split_data_by_category(
        train_annotations_images_by_category
    )

    _process_and_save_split(
        train_data_by_cat=train_val_by_category,
        test_data_by_cat=test_val_by_category,
        base_metadata=old_train_metadata,  # Use original for all top-level keys
        public_dir=public_val,
        private_dir=private_val,
        raw_data_path=raw,
        dev_mode=dev_mode,
        dev_count=dev_count,
    )
    logger.info(f"Validation sets saved to {public_val.name} and {private_val.name}")