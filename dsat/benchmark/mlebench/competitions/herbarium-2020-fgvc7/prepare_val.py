import json
import random
import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from mlebench.utils import get_logger

logger = get_logger(__name__)


def _create_dataset_files(
    train_data_by_cat: dict,
    test_data_by_cat: dict,
    base_metadata: dict,
    public_dir: Path,
    private_dir: Path,
    raw_dir: Path,
    dev_mode: bool,
    dev_count: int,
):
    """
    Helper function to generate the complete set of dataset files for a given split.

    This function is responsible for:
    1. Creating the `train` set (metadata.json and image files).
    2. Creating the `test` set (public metadata.json and image files).
    3. Creating the private `answers.csv` for the `test` set.
    4. Creating the public `sample_submission.csv`.
    """
    public_dir.mkdir(exist_ok=True, parents=True)
    private_dir.mkdir(exist_ok=True, parents=True)

    # --- Process Train Set ---
    new_train_metadata = base_metadata.copy()
    new_train_metadata.update({"annotations": [], "images": []})
    train_sample_count = sum(len(v) for v in train_data_by_cat.values())

    with tqdm(
        desc=f"Creating train set for {public_dir.name}",
        total=train_sample_count,
    ) as pbar:
        for category_id, annotations_images in train_data_by_cat.items():
            category_subdir = f"{category_id // 100:03d}/{category_id % 100:02d}"
            (public_dir / "nybg2020/train/images" / category_subdir).mkdir(
                exist_ok=True, parents=True
            )
            for idx, annotation_image in enumerate(annotations_images):
                new_train_metadata["annotations"].append(annotation_image["annotation"].copy())
                new_train_metadata["images"].append(annotation_image["image"].copy())

                if not dev_mode or idx < dev_count:
                    src_path = raw_dir / "nybg2020/train" / annotation_image["image"]["file_name"]
                    dst_path = public_dir / "nybg2020/train" / annotation_image["image"]["file_name"]
                    shutil.copyfile(src=src_path, dst=dst_path)

                pbar.update(1)

    with open(public_dir / "nybg2020/train/metadata.json", "w") as f:
        json.dump(new_train_metadata, f, indent=4, sort_keys=True)

    if not dev_mode:
        assert len(list((public_dir / "nybg2020/train/images").glob("**/*.jpg"))) == len(
            new_train_metadata["images"]
        )
        assert len(new_train_metadata["annotations"]) == len(new_train_metadata["images"])

    # --- Process Test Set ---
    new_test_metadata = base_metadata.copy()
    del new_test_metadata["categories"]
    del new_test_metadata["regions"]
    new_test_metadata.update({"annotations": [], "images": []})

    test_annotations_images = [item for sublist in test_data_by_cat.values() for item in sublist]
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
            src_path = raw_dir / "nybg2020/train" / annotation_image["image"]["file_name"]
            dst_path = public_dir / "nybg2020/test" / new_file_name
            dst_path.parent.mkdir(exist_ok=True, parents=True)
            shutil.copyfile(src=src_path, dst=dst_path)

    # Save public test metadata (without annotations)
    with open(public_dir / "nybg2020/test/metadata.json", "w") as f:
        public_new_test = new_test_metadata.copy()
        del public_new_test["annotations"]
        assert public_new_test.keys() == {"images", "info", "licenses"}
        json.dump(public_new_test, f, indent=4, sort_keys=True)

    if not dev_mode:
        assert len(list((public_dir / "nybg2020/test/images").glob("**/*.jpg"))) == len(
            new_test_metadata["images"]
        )
        assert len(new_test_metadata["annotations"]) == len(new_test_metadata["images"])

    # --- Save Private Test Answers and Public Sample Submission ---
    answers_rows = [
        {"Id": img["id"], "Predicted": ann["category_id"]}
        for img, ann in zip(new_test_metadata["images"], new_test_metadata["annotations"])
    ]
    answers_df = pd.DataFrame(answers_rows)
    answers_df.to_csv(private_dir / "answers.csv", index=False)

    sample_df = pd.DataFrame({"Id": answers_df["Id"], "Predicted": 0})
    sample_df.to_csv(public_dir / "sample_submission.csv", index=False)

    assert len(answers_df) == len(new_test_metadata["images"])
    assert len(sample_df) == len(answers_df)
    assert answers_df["Id"].equals(sample_df["Id"])


def _split_data_by_category(
    data_by_cat: dict, test_size: float, random_state: int
) -> tuple[dict, dict]:
    """Splits data within each category into train and test sets."""
    train_split = {}
    test_split = {}
    for category_id, annotations_images in data_by_cat.items():
        n_samples = len(annotations_images)
        if n_samples == 1:
            train_annotations_images = annotations_images
            test_annotations_images = []
        elif n_samples < 5:
            # Ensure at least 1 sample in test for small categories
            current_test_size = max(1, int(n_samples * test_size))
            train_annotations_images = annotations_images[:-current_test_size]
            test_annotations_images = annotations_images[-current_test_size:]
        else:
            train_annotations_images, test_annotations_images = train_test_split(
                annotations_images, test_size=test_size, random_state=random_state
            )
        train_split[category_id] = train_annotations_images
        test_split[category_id] = test_annotations_images
    return train_split, test_split


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the raw data into public and private datasets with appropriate test/train splits.
    This version also creates a second, parallel split for validation purposes.
    """
    dev_mode = False
    dev_count = 2  # Copy over n images per category when in dev mode

    # Create directories for the new validation split
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Load raw data and organize by category
    json_path = raw / "nybg2020/train/metadata.json"
    with open(json_path, "r", encoding="latin-1") as f:
        old_train_metadata = json.load(f)

    annotations_images_by_category = {}
    for annotation, image in list(
        zip(old_train_metadata["annotations"], old_train_metadata["images"])
    ):
        assert annotation["image_id"] == image["id"]
        category_id = annotation["category_id"]
        if category_id not in annotations_images_by_category:
            annotations_images_by_category[category_id] = []
        annotations_images_by_category[category_id].append(
            {"annotation": annotation, "image": image}
        )

    # --- First Split: Create the main train/test sets (80/20 split of raw data) ---
    logger.info("Performing first split: raw data -> train/test")
    original_test_size = 0.2
    train_data_by_cat, test_data_by_cat = _split_data_by_category(
        annotations_images_by_category,
        test_size=original_test_size,
        random_state=0,
    )

    # Generate the original `public` and `private` outputs
    _create_dataset_files(
        train_data_by_cat,
        test_data_by_cat,
        old_train_metadata,
        public,
        private,
        raw,
        dev_mode,
        dev_count,
    )

    # --- Second Split: Create the validation train/test sets from the main train set ---
    # The goal is a validation set (`test_val`) of roughly the same size as the original test set.
    # Original split: train=0.8*N, test=0.2*N
    # Second split on train data: We need a test fraction of (0.2*N)/(0.8*N) = 0.25
    logger.info("Performing second split: train data -> train_val/test_val")
    validation_test_size = 0.25
    train_val_data_by_cat, test_val_data_by_cat = _split_data_by_category(
        train_data_by_cat,  # Use the training data from the first split as input
        test_size=validation_test_size,
        random_state=0,  # Use same random state for consistency
    )

    # Generate the new `public_val` and `private_val` outputs
    _create_dataset_files(
        train_val_data_by_cat,
        test_val_data_by_cat,
        old_train_metadata,
        public_val,
        private_val,
        raw,
        dev_mode,
        dev_count,
    )

    logger.info("Data preparation complete.")
    if not dev_mode:
        # Final sanity check on total annotations
        total_original = len(old_train_metadata["annotations"])
        total_in_first_split = sum(len(v) for v in train_data_by_cat.values()) + sum(
            len(v) for v in test_data_by_cat.values()
        )
        total_in_second_split = sum(len(v) for v in train_val_data_by_cat.values()) + sum(
            len(v) for v in test_val_data_by_cat.values()
        )
        assert total_original == total_in_first_split
        assert total_in_second_split == sum(len(v) for v in train_data_by_cat.values())