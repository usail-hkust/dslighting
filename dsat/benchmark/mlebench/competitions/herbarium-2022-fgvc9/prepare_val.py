import json
import random
import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from mlebench.utils import get_logger

logger = get_logger(__name__)


def _organize_data_by_category(metadata: dict) -> dict:
    """Organizes image and annotation data by category ID."""
    annotations_images_by_category = {}
    for annotation, image in list(zip(metadata["annotations"], metadata["images"])):
        assert annotation["image_id"] == image["image_id"]
        category_id = annotation["category_id"]
        if category_id not in annotations_images_by_category:
            annotations_images_by_category[category_id] = []
        annotations_images_by_category[category_id].append(
            {
                "annotation": annotation,
                "image": image,
            }
        )
    return annotations_images_by_category


def _split_data(data_by_category: dict, test_size: float, random_state: int) -> tuple[dict, dict]:
    """Splits data for each category into train and test sets."""
    train_annotations_images_by_category = {}
    test_annotations_images_by_category = {}
    for category_id, annotations_images in data_by_category.items():
        # Each category needs to be in both train and test
        train_annotations_images, test_annotations_images = train_test_split(
            annotations_images, test_size=test_size, random_state=random_state
        )
        assert len(train_annotations_images) > 0 and len(test_annotations_images) > 0
        train_annotations_images_by_category[category_id] = train_annotations_images
        test_annotations_images_by_category[category_id] = test_annotations_images
    return train_annotations_images_by_category, test_annotations_images_by_category


def _process_train_set(
    train_data: dict, base_metadata: dict, raw_path: Path, output_public_path: Path
):
    """Processes and writes the training set data, images, and metadata."""
    logger.info(f"Processing train set for output: {output_public_path}")
    new_train_metadata = base_metadata.copy()
    new_train_metadata.update({"annotations": [], "images": []})
    train_sample_count = sum(len(v) for v in train_data.values())

    output_train_images_path = output_public_path / "train_images"

    with tqdm(
        desc=f"Creating train dataset in {output_public_path.name}",
        total=train_sample_count,
    ) as pbar:
        for category_id, annotations_images in train_data.items():
            category_subdir = f"{category_id // 100:03d}/{category_id % 100:02d}"
            (output_train_images_path / category_subdir).mkdir(exist_ok=True, parents=True)
            for idx, annotation_image in enumerate(annotations_images):
                new_image_id = f"{category_id:05d}__{(idx + 1):03d}"
                new_file_name = f"{category_subdir}/{new_image_id}.jpg"

                new_annotation = annotation_image["annotation"].copy()
                new_annotation["image_id"] = new_image_id
                new_train_metadata["annotations"].append(new_annotation)

                new_image = annotation_image["image"].copy()
                new_image["image_id"] = new_image_id
                new_image["file_name"] = new_file_name
                new_train_metadata["images"].append(new_image)

                src_path = raw_path / "train_images" / annotation_image["image"]["file_name"]
                dst_path = output_train_images_path / new_file_name
                shutil.copyfile(src=src_path, dst=dst_path)

                pbar.update(1)

    with open(output_public_path / "train_metadata.json", "w") as f:
        json.dump(new_train_metadata, f, indent=4, sort_keys=True)

    assert len(list(output_train_images_path.glob("**/*.jpg"))) == len(
        new_train_metadata["images"]
    )
    assert len(new_train_metadata["annotations"]) == len(new_train_metadata["images"])


def _process_test_set(
    test_data: dict, raw_path: Path, output_public_path: Path, output_private_path: Path
):
    """Processes and writes the test set data, images, metadata, and private answers."""
    logger.info(
        f"Processing test set for outputs: {output_public_path} and {output_private_path}"
    )
    new_test_metadata = {"annotations": [], "images": []}
    test_annotations_images = [item for sublist in test_data.values() for item in sublist]
    random.Random(0).shuffle(test_annotations_images)

    output_test_images_path = output_public_path / "test_images"

    for idx, annotation_image in tqdm(
        enumerate(test_annotations_images),
        desc=f"Creating test dataset in {output_public_path.name}",
        total=len(test_annotations_images),
    ):
        new_image_id = str(idx)
        new_file_name = f"{idx // 1000:03d}/test-{idx:06d}.jpg"

        new_annotation = annotation_image["annotation"].copy()
        new_annotation["image_id"] = new_image_id
        new_test_metadata["annotations"].append(new_annotation)

        new_image = annotation_image["image"].copy()
        new_image["image_id"] = new_image_id
        new_image["file_name"] = new_file_name
        new_test_metadata["images"].append(new_image)

        src_path = raw_path / "train_images" / annotation_image["image"]["file_name"]
        dst_path = output_test_images_path / new_file_name
        dst_path.parent.mkdir(exist_ok=True, parents=True)
        shutil.copyfile(src=src_path, dst=dst_path)

    with open(output_public_path / "test_metadata.json", "w") as f:
        json.dump(new_test_metadata["images"], f, indent=4, sort_keys=True)

    answers_rows = [
        {"Id": image["image_id"], "Predicted": annotation["category_id"]}
        for image, annotation in zip(new_test_metadata["images"], new_test_metadata["annotations"])
    ]
    answers_df = pd.DataFrame(answers_rows)
    answers_df.to_csv(output_private_path / "answers.csv", index=False)

    sample_rows = [{"Id": image["image_id"], "Predicted": 42} for image in new_test_metadata["images"]]
    sample_df = pd.DataFrame(sample_rows)
    sample_df.to_csv(output_public_path / "sample_submission.csv", index=False)

    assert len(list(output_test_images_path.glob("**/*.jpg"))) == len(new_test_metadata["images"])
    assert len(new_test_metadata["annotations"]) == len(new_test_metadata["images"])
    assert len(answers_df) == len(new_test_metadata["images"])
    assert len(sample_df) == len(answers_df)


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the raw data into public and private datasets with appropriate test/train splits.

    `train_metadata.json` is the "table of contents" for our data, with the following structure:
    (More details at https://www.kaggle.com/competitions/herbarium-2022-fgvc9/data)
    ```
    {
        "annotations" : [annotation],
        "categories" : [category],
        "genera" : [genus]
        "images" : [image],
        "distances" : [distance],
        "licenses" : [license],
        "institutions" : [institution]
    }
    ```
    - `images` and `annotations` are both N-length lists corresponding to the N samples.
        We'll need to split each of these lists into train and test.
    - The other fields are dataset-wide metadata that we don't need to touch.

    Other notes:
    - train/test splits need to occur per category (each category should be in both train and test).
    - The `test_images` and `train_images` folders have nested subdirs to make it easier to browse
        - `train_images` is structured as `{category_id[:3]}/{category_id[3:]}/{image_id}.jpg`
        - `test_images` is structured as `{image_idx[:3]}/test-{image_idx}.jpg` (to not reveal the category)
    - When we create the new splits, we re-assign image indices so that we don't give away labels based on the index
        - train images are indexed within their own category
        - test images follow a flat index after shuffling the categories
    """
    # Load raw data and organize it by category
    with open(raw / "train_metadata.json") as f:
        old_train_metadata = json.load(f)
    annotations_images_by_category = _organize_data_by_category(old_train_metadata)

    # --- 1. Create the original public/private datasets ---
    # This first split creates the main train and test sets.
    # The outputs in `public` and `private` will be identical to the original script.
    logger.info("--- Creating original train/test split for 'public' and 'private' directories ---")
    original_train_split, original_test_split = _split_data(
        annotations_images_by_category, test_size=0.2, random_state=0
    )

    _process_train_set(original_train_split, old_train_metadata, raw, public)
    _process_test_set(original_test_split, raw, public, private)
    logger.info("Finished creating original 'public' and 'private' datasets.")

    # --- 2. Create the validation datasets from the original training set ---
    # This second split takes the `original_train_split` and splits it *again*
    # to create a new, smaller training set and a validation set.
    # The outputs are saved to new `public_val` and `private_val` directories.
    logger.info("--- Creating validation split for 'public_val' and 'private_val' directories ---")
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"
    public_val.mkdir(exist_ok=True, parents=True)
    private_val.mkdir(exist_ok=True, parents=True)

    # The input for this split is the *train set* from the first split.
    # We use the exact same splitting logic to ensure consistency.
    train_val_split, test_val_split = _split_data(
        original_train_split, test_size=0.2, random_state=0
    )

    _process_train_set(train_val_split, old_train_metadata, raw, public_val)
    _process_test_set(test_val_split, raw, public_val, private_val)
    logger.info("Finished creating validation 'public_val' and 'private_val' datasets.")