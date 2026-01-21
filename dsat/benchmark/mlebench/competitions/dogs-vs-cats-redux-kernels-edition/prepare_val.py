import shutil
from pathlib import Path
from typing import List

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from mlebench.utils import compress, extract


def _process_split(
    image_paths: List[Path],
    public_dir: Path,
    private_dir: Path,
    test_size: float,
    random_state: int,
) -> List[Path]:
    """
    Splits a list of image paths into train/test sets and generates all required files.

    This function encapsulates the logic for:
    1. Splitting data.
    2. Copying and renaming images to public train/test subdirectories.
    3. Compressing the public train/test image directories.
    4. Creating the private answer key for the test set.
    5. Creating a public sample submission file.

    Args:
        image_paths: A list of Path objects for the images to be split.
        public_dir: The public output directory (e.g., 'data/public').
        private_dir: The private output directory (e.g., 'data/private').
        test_size: The proportion of the dataset to allocate to the test set.
        random_state: The seed for the random number generator.

    Returns:
        A list of Path objects corresponding to the training set of this split.
    """
    public_dir.mkdir(exist_ok=True, parents=True)
    private_dir.mkdir(exist_ok=True, parents=True)

    # Perform the split
    train_images, test_images = train_test_split(
        image_paths, test_size=test_size, random_state=random_state
    )

    # Copy over train images. Rename cat files to cat.0.jpg, cat.1.jpg, etc.
    # Rename dog files to dog.0.jpg, dog.1.jpg, etc.
    cat_ctr = 0
    dog_ctr = 0
    (public_dir / "train").mkdir(exist_ok=True)
    for img in tqdm(train_images, desc=f"Processing train set for {public_dir.name}"):
        if "cat" in img.name:
            shutil.copy(img, public_dir / "train" / f"cat.{cat_ctr}.jpg")
            cat_ctr += 1
        else:
            shutil.copy(img, public_dir / "train" / f"dog.{dog_ctr}.jpg")
            dog_ctr += 1
    assert cat_ctr + dog_ctr == len(
        train_images
    ), f"Expected {len(train_images)} train images but got {cat_ctr + dog_ctr} images."

    # Copy over test images. Rename files to 1.jpg, 2.jpg, etc.
    (public_dir / "test").mkdir(exist_ok=True)
    for i, img in enumerate(tqdm(test_images, desc=f"Processing test set for {public_dir.name}"), start=1):
        shutil.copy(img, public_dir / "test" / f"{i}.jpg")
    assert i == len(test_images), f"Expected {len(test_images)} test images but got {i} images."

    # Compress train and test images
    compress(public_dir / "train", public_dir / "train.zip", exist_ok=True)
    compress(public_dir / "test", public_dir / "test.zip", exist_ok=True)

    # Make answers
    answers = pd.DataFrame(
        {
            "id": [i for i in range(1, len(test_images) + 1)],
            "label": [int("dog" in img.name) for img in test_images],
        }
    )
    answers.to_csv(private_dir / "answers.csv", index=False)
    assert len(answers) == len(
        test_images
    ), f"Expected {len(test_images)} answers but got {len(answers)} answers."

    # Make sample submission
    sample_submission = pd.DataFrame(
        {
            "id": [i for i in range(1, len(test_images) + 1)],
            "label": [0.5 for _ in range(1, len(test_images) + 1)],
        }
    )
    sample_submission.to_csv(public_dir / "sample_submission.csv", index=False)
    assert len(sample_submission) == len(
        test_images
    ), f"Expected {len(test_images)} sample submission rows but got {len(sample_submission)} rows."

    return train_images


def prepare(raw: Path, public: Path, private: Path):
    # This part remains from the original script
    extract(raw / "train.zip", raw)
    extract(raw / "test.zip", raw)

    all_train_images = sorted(list((raw / "train").glob("*.jpg")))
    
    # --- 1. Original Split (train -> train + test) ---
    # This call generates the original competition files in `public` and `private`.
    # The logic and outputs of this step are unchanged.
    # Original test ratio has Train set - 25,000 samples; Test set - 12,500 samples (33% ratio)
    # We use 0.1 ratio to avoid removing too many samples from train
    original_test_size = 0.1
    main_train_set = _process_split(
        image_paths=all_train_images,
        public_dir=public,
        private_dir=private,
        test_size=original_test_size,
        random_state=0,
    )

    # --- 2. New Validation Split (main_train_set -> train_val + test_val) ---
    # This call generates a new, parallel set of files for validation purposes.
    # It operates *only* on the training data from the first split.
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # To make the new test_val set have the same size as the original test set,
    # we adjust the test_size for the second split.
    # new_size = original_test_size / (1 - original_test_size)
    # e.g., 0.1 / (1 - 0.1) = 0.1 / 0.9 = 1/9
    validation_test_size = original_test_size / (1 - original_test_size)

    _process_split(
        image_paths=main_train_set,
        public_dir=public_val,
        private_dir=private_val,
        test_size=validation_test_size,
        random_state=0,  # Use the same random state for consistency
    )

    # Final cleanup is done after all splits are complete
    shutil.rmtree(raw / "train")
    shutil.rmtree(raw / "test")