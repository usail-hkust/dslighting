import json
import random
import shutil
import tarfile
from pathlib import Path
from typing import Dict, List

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from mlebench.utils import get_logger

logger = get_logger(__name__)


def add_to_tar(src: Path, out: Path):

    assert src.exists(), f"Source directory `{src}` does not exist."
    assert src.is_dir(), f"Expected a directory, but got `{src}`."

    tqdm_desc = f"Taring {src.name} to {out.name}"
    file_paths = [path for path in src.rglob("*") if path.is_file()]
    total_files = len(file_paths)

    with tarfile.open(out, "w") as tar:
        for file_path in tqdm(file_paths, desc=tqdm_desc, unit="file", total=total_files):
            tar.add(file_path, arcname=file_path.relative_to(src))


def _split_by_category(
    data_by_category: Dict, test_size: float, random_state: int
) -> tuple[Dict, Dict]:
    """Splits data for each category into train and test sets using the original script's logic."""
    train_split_by_category = {}
    test_split_by_category = {}

    for category_id, annotation_image_metadata in tqdm(
        data_by_category.items(),
        desc=f"Assigning train/test splits (test_size={test_size:.3f})",
    ):
        n_samples = len(annotation_image_metadata)
        if n_samples == 1:
            # If only one sample, put it in train
            train_annotations_images = annotation_image_metadata
            test_annotations_images = []
        elif n_samples < 5:  # Minimum 5 samples to ensure at least 1 in test
            num_test_samples = max(1, int(n_samples * test_size))
            train_annotations_images = annotation_image_metadata[:-num_test_samples]
            test_annotations_images = annotation_image_metadata[-num_test_samples:]
        else:
            train_annotations_images, test_annotations_images = train_test_split(
                annotation_image_metadata, test_size=test_size, random_state=random_state
            )

        train_split_by_category[category_id] = train_annotations_images
        test_split_by_category[category_id] = test_annotations_images

    return train_split_by_category, test_split_by_category


def _generate_split_files(
    train_annotation_image_metadata_by_category: Dict,
    test_annotation_image_metadata_by_category: Dict,
    old_train_metadata: Dict,
    raw_path: Path,
    public_path: Path,
    private_path: Path,
    dev_mode: bool,
    image_count: int,
):
    """
    Processes a given train/test split and saves all corresponding files
    (metadata, images, private answers, etc.) to the specified output directories.
    """
    public_path.mkdir(parents=True, exist_ok=True)
    private_path.mkdir(parents=True, exist_ok=True)

    # Create new train2019.json
    new_train_metadata = (
        old_train_metadata.copy()
    )  # Keep 'info', 'categories', 'licenses' unchanged
    new_train_metadata.update(
        {
            "annotations": [],
            "images": [],
        }
    )
    for category_id, annotation_image_metadata in tqdm(
        train_annotation_image_metadata_by_category.items(),
        desc=f"[{public_path.name}] Creating new train2019.json",
        total=len(train_annotation_image_metadata_by_category),
    ):
        for annotation_image in annotation_image_metadata:
            new_annotation = annotation_image["annotation"].copy()
            new_train_metadata["annotations"].append(new_annotation)
            new_image = annotation_image["image"].copy()
            new_train_metadata["images"].append(new_image)

    with open(public_path / "train2019.json", "w") as f:
        json.dump(new_train_metadata, f, indent=4, sort_keys=True)

    # Copy over val2019.json
    shutil.copy(raw_path / "val2019.json", public_path / "val2019.json")

    # Create new test2019.json
    new_to_old_file_name = {}
    new_test_metadata = old_train_metadata.copy()
    del new_test_metadata["categories"]
    new_test_metadata.update(
        {
            "annotations": [],
            "images": [],
        }
    )
    # Flatten and shuffle test set so that we don't have all the same categories in a row
    test_annotations_images = [
        item
        for sublist in test_annotation_image_metadata_by_category.values()
        for item in sublist
    ]
    random.Random(0).shuffle(test_annotations_images)
    for idx, annotation_image in tqdm(
        enumerate(test_annotations_images),
        desc=f"[{public_path.name}] Creating new test2019.json",
        total=len(test_annotations_images),
    ):
        new_annotation = annotation_image["annotation"].copy()
        new_test_metadata["annotations"].append(new_annotation)

        new_image = annotation_image["image"].copy()
        old_file_name = new_image["file_name"]
        # go from e.g. "train_val2019/Plants/400/d1322d13ccd856eb4236c8b888546c79.jpg" to "test2019/d1322d13ccd856eb4236c8b888546c79.jpg"
        new_file_name = "test2019/" + old_file_name.split("/")[-1]
        # keep track of things so we know what to copy later
        new_to_old_file_name[new_file_name] = old_file_name
        new_image["file_name"] = new_file_name
        new_test_metadata["images"].append(new_image)

    with open(public_path / "test2019.json", "w") as f:
        # The public test data, of course, doesn't have annotations
        public_new_test = new_test_metadata.copy()
        del public_new_test["annotations"]
        assert public_new_test.keys() == {
            "images",
            "info",
            "licenses",
        }, f"Public test metadata keys should be 'images', 'info', 'licenses', but found {public_new_test.keys()}"
        json.dump(public_new_test, f, indent=4, sort_keys=True)

    (public_path / "train_val2019").mkdir(parents=True, exist_ok=True)
    (public_path / "test2019").mkdir(parents=True, exist_ok=True)

    # Save private test answers
    answers_rows = []
    for image_info, annotation_info in zip(
        new_test_metadata["images"], new_test_metadata["annotations"]
    ):
        assert (
            image_info["id"] == annotation_info["image_id"]
        ), f"Mismatching image_id in image and annotation: {image_info['id']} vs {annotation_info['image_id']}"
        answers_rows.append(
            {
                "id": image_info["id"],
                "predicted": annotation_info["category_id"],
            }
        )
    answers_df = pd.DataFrame(answers_rows)
    answers_df.to_csv(private_path / "answers.csv", index=False)

    # Create new sample submission based on answers_df
    sample_df = answers_df.copy()
    sample_df["predicted"] = [random.Random(42).randint(0, 1009) for _ in range(len(sample_df))]
    sample_df.to_csv(public_path / "kaggle_sample_submission.csv", index=False)

    # Copy train images
    for annotation_image_metadata in tqdm(
        train_annotation_image_metadata_by_category.values(),
        desc=f"[{public_path.name}] Copying train images",
    ):
        for idx, annotation_image in enumerate(annotation_image_metadata):
            if dev_mode and idx >= image_count:
                break
            old_path = raw_path / annotation_image["image"]["file_name"]
            new_path = public_path / annotation_image["image"]["file_name"]
            new_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(old_path, new_path)

    # Copy test images
    for image_info in tqdm(
        new_test_metadata["images"], desc=f"[{public_path.name}] Copying test images"
    ):
        if dev_mode and len(new_to_old_file_name) >= image_count:
            break
        old_path = raw_path / new_to_old_file_name[image_info["file_name"]]
        new_path = public_path / image_info["file_name"]
        new_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(old_path, new_path)

    # Re-compress images
    add_to_tar(
        src=public_path / "test2019", out=public_path / "test2019.tar.gz"
    )  # Add to tar but don't actually compress with gzip to save time
    add_to_tar(src=public_path / "train_val2019", out=public_path / "train_val2019.tar.gz")
    # Remove uncompressed directories
    shutil.rmtree(public_path / "test2019")
    shutil.rmtree(public_path / "train_val2019")
    logger.info(f"Finished generating files for {public_path.name}")


def prepare(raw: Path, public: Path, private: Path):

    dev_mode = False
    image_count = 2 if dev_mode else float("inf")  # We copy over 2 images per category for dev mode

    # Extract train_val2019.tar.gz which contains images
    train_tar_path = raw / "train_val2019.tar.gz"
    train_extract_path = raw
    if not (raw / "train_val2019").exists():
        logger.info("Extracting raw image data...")
        shutil.unpack_archive(train_tar_path, train_extract_path)

    # Create train, test from train split
    json_path = raw / "train2019.json"
    with open(json_path, "r", encoding="utf-8") as f:
        old_train_metadata = json.load(f)

    # Organize data by category so that we can split per-category later
    annotation_image_metadata_by_category = {}  # We'll collect both `annotations` and `images` here
    for annotation_info, image_info in list(
        zip(old_train_metadata["annotations"], old_train_metadata["images"])
    ):
        assert (
            annotation_info["image_id"] == image_info["id"]
        ), f"Mismatching image_id in annotation and image: {annotation_info['image_id']} vs {image_info['id']}"
        category_id = annotation_info["category_id"]
        if category_id not in annotation_image_metadata_by_category:
            annotation_image_metadata_by_category[category_id] = []
        annotation_image_metadata_by_category[category_id].append(
            {
                "annotation": annotation_info,
                "image": image_info,
            }
        )

    # --- 1. Original Data Split (Train/Test) ---
    logger.info("--- Generating Original Train/Test Split ---")
    # Original train+val has 268,243 images, test has 35,400 images, ~0.12 ratio
    original_test_size = 0.12
    (
        original_train_split,
        original_test_split,
    ) = _split_by_category(
        annotation_image_metadata_by_category,
        test_size=original_test_size,
        random_state=0,
    )

    _generate_split_files(
        original_train_split,
        original_test_split,
        old_train_metadata,
        raw,
        public,
        private,
        dev_mode,
        image_count,
    )
    logger.info(f"Original split saved to {public.name} and {private.name}")

    # --- 2. New Validation Data Split (Train/Val) ---
    logger.info("--- Generating New Train/Validation Split ---")
    # Define new output directories
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # We want the new validation set ('test_val') to have the same size as the
    # original test set. We are splitting the *original_train_split* to get it.
    # test_val_size = new_test_size * train_size
    # We want: test_val_size ≈ test_size
    # So: new_test_size * (N * (1-0.12)) ≈ N * 0.12
    # new_test_size ≈ 0.12 / (1 - 0.12)
    val_split_test_size = original_test_size / (1.0 - original_test_size)

    (
        validation_train_split,
        validation_test_split,
    ) = _split_by_category(
        original_train_split,  # Split the TRAIN set from the first split
        test_size=val_split_test_size,
        random_state=0,  # Use same random state for consistency
    )

    _generate_split_files(
        validation_train_split,
        validation_test_split,
        old_train_metadata,
        raw,
        public_val,
        private_val,
        dev_mode,
        image_count,
    )
    logger.info(f"Validation split saved to {public_val.name} and {private_val.name}")