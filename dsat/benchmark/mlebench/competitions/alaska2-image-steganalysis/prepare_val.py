import random
import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm


def _create_dataset_split(
    train_image_paths: list,
    test_image_paths: list,
    raw_dir: Path,
    public_dir: Path,
    private_dir: Path,
    steganography_algs: list,
):
    """
    Helper function to create a dataset split (e.g., train/test or train_val/test_val).

    This function populates the public and private directories with the respective
    training images, test images, and test set ground-truth labels.
    """
    # Prepare dirs
    public_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)
    for subdir in ["Cover", "Test"] + steganography_algs:
        (public_dir / subdir).mkdir(exist_ok=True)

    # Copy over the train set for this split, giving them new ids
    for idx, fp in tqdm(
        enumerate(train_image_paths), total=len(train_image_paths), desc=f"Copying train images to {public_dir.name}"
    ):
        image_id = idx + 1  # 1-indexed
        shutil.copyfile(src=fp, dst=public_dir / "Cover" / f"{image_id:05d}.jpg")
        for alg in steganography_algs:
            shutil.copyfile(src=raw_dir / alg / fp.name, dst=public_dir / alg / f"{image_id:05d}.jpg")

    # Populate the test set for this split
    answers_rows = []
    random.seed(0)  # Reset seed for deterministic test set creation
    random.shuffle(test_image_paths)
    for idx, fp in tqdm(
        enumerate(test_image_paths), total=len(test_image_paths), desc=f"Copying test images to {public_dir.name}"
    ):
        image_id = idx + 1  # 1-indexed
        test_id = f"{image_id:04d}.jpg"
        dest = public_dir / "Test" / test_id

        # For the test set, we randomly select between the "Cover" (unedited image, negative class)
        # and one of the 3 steganography algorithms (positive class)
        # 1:1 ratio of positive:negative examples, and even distribution of steganography algorithms
        if random.choice([True, False]):
            # Negative class
            shutil.copyfile(
                src=fp,
                dst=dest,
            )
            answers_rows.append({"Id": test_id, "Label": 0})
        else:
            # Positive class
            alg = random.choice(steganography_algs)
            shutil.copyfile(src=raw_dir / alg / fp.name, dst=dest)
            answers_rows.append({"Id": test_id, "Label": 1})

    # Write answers to file
    answers_df = pd.DataFrame(answers_rows)
    answers_df.to_csv(private_dir / "test.csv", index=False)

    # Create sample submission
    sample_submission = answers_df.copy()
    sample_submission["Label"] = 0
    sample_submission.to_csv(public_dir / "sample_submission.csv", index=False)

    # Checks
    test_size = len(test_image_paths)
    assert "Id" in answers_df.columns, "Answers must have 'Id' column"
    assert "Label" in answers_df.columns, "Answers must have 'Label' column"
    assert "Id" in sample_submission.columns, "Sample submission must have 'Id' column"
    assert "Label" in sample_submission.columns, "Sample submission must have 'Label' column"
    assert (
        len(answers_df) == test_size
    ), f"Expected {test_size} test images, but got {len(answers_df)}"
    assert len(sample_submission) == len(
        answers_df
    ), f"Sample submission ({len(sample_submission)}) and answers ({len(answers_df)}) must have the same length"
    assert (
        len(list(public_dir.glob("Test/*.jpg"))) == test_size
    ), f"Expected {test_size} test images in {public_dir.name}/Test, but got {len(list(public_dir.glob('Test/*.jpg')))}"
    assert len(list(public_dir.glob("Cover/*.jpg"))) == len(
        train_image_paths
    ), f"Expected {len(train_image_paths)} train images in {public_dir.name}/Cover, but got {len(list(public_dir.glob('Cover/*.jpg')))}"
    for alg in steganography_algs:
        assert len(list(public_dir.glob(f"{alg}/*.jpg"))) == len(
            train_image_paths
        ), f"Expected {len(train_image_paths)} train images in {public_dir.name}/{alg}, but got {len(list(public_dir.glob(f'{alg}/*.jpg')))}"


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the data in raw into public and private datasets with appropriate test/train splits.
    Also creates a secondary validation split (train_val/test_val) in parallel directories.
    """
    # List of all train image IDs
    cover_images_dir = raw / "Cover"
    cover_images = sorted(list(cover_images_dir.glob("*.jpg")))
    steganography_algs = ["JMiPOD", "JUNIWARD", "UERD"]
    test_size = 5000

    # --- Stage 1: Create the main competition train/test split ---
    # This split creates the final test set used for scoring.
    # The outputs in `public` and `private` are left untouched by subsequent steps.
    train_main, test_main = train_test_split(
        cover_images, test_size=test_size, random_state=42
    )

    _create_dataset_split(
        train_image_paths=train_main,
        test_image_paths=test_main,
        raw_dir=raw,
        public_dir=public,
        private_dir=private,
        steganography_algs=steganography_algs,
    )

    # --- Stage 2: Create the validation train/test split ---
    # This performs a second split on the main training data (`train_main`)
    # to create a new, smaller training set and a validation set.
    # Outputs are saved to `public_val` and `private_val` to avoid conflicts.
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Split `train_main` again, using the same logic as the first split
    # to create a validation set of the same size as the main test set.
    train_val, test_val = train_test_split(
        train_main, test_size=test_size, random_state=42
    )

    # The new split is processed using the same helper function to ensure
    # identical directory structure, filenames, and creation logic.
    _create_dataset_split(
        train_image_paths=train_val,
        test_image_paths=test_val,
        raw_dir=raw,
        public_dir=public_val,
        private_dir=private_val,
        steganography_algs=steganography_algs,
    )