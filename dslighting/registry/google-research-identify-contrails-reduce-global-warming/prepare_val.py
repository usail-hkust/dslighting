import json
import random
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from mlebench.competitions.utils import get_logger, rle_encode

logger = get_logger(__name__)


def _create_answers_df(samples: list, raw_path: Path) -> pd.DataFrame:
    """Creates a DataFrame with ground truth answers for a given set of samples."""
    answers = []
    for sample in tqdm(samples, desc="Creating answers CSV"):
        record_id = sample["record_id"]
        mask = np.load(raw_path / "train" / record_id / "human_pixel_masks.npy")
        rle = rle_encode(mask)
        rle = " ".join([str(i) for i in rle]) if rle else "-"

        band = np.load(raw_path / "train" / record_id / "band_08.npy")
        height, width, _ = band.shape
        answers.append(
            {
                "record_id": record_id,
                "encoded_pixels": rle,
                "height": height,
                "width": width,
            }
        )
    return pd.DataFrame(answers)


def _copy_data_files(samples: list, raw_path: Path, dest_path: Path, include_masks: bool):
    """Copies data files (bands and optionally masks) for a given set of samples."""
    desc = f"Copying {'train' if include_masks else 'test'} files"
    for sample in tqdm(samples, desc=desc):
        record_id = sample["record_id"]
        (dest_path / record_id).mkdir(exist_ok=True, parents=True)
        # Copy bands
        for band_idx in range(8, 17):
            file_name = f"band_{band_idx:02}.npy"
            shutil.copyfile(
                src=raw_path / "train" / record_id / file_name,
                dst=dest_path / record_id / file_name,
            )
        if include_masks:
            # Copy human individual masks
            shutil.copyfile(
                src=raw_path / "train" / record_id / "human_individual_masks.npy",
                dst=dest_path / record_id / "human_individual_masks.npy",
            )
            # Copy human pixel masks
            shutil.copyfile(
                src=raw_path / "train" / record_id / "human_pixel_masks.npy",
                dst=dest_path / record_id / "human_pixel_masks.npy",
            )


def prepare(raw: Path, public: Path, private: Path):
    """
    We make train/test split from old train set, using same train/test proportion as the original
    competition. Concretely, the new split has 18673 train samples and 1856 test samples. We also
    copy over the validation set as-is.

    `sample_submission` is created with random predictions, either "1 3 10 5" or "-" (empty)

    A second split is performed on the train set to create a new validation set in parallel
    `public_val` and `private_val` directories.
    """
    DEV = False

    with open(raw / "train_metadata.json", "r") as f:
        train_metadata = json.load(f)
    train_metadata = train_metadata[:100] if DEV else train_metadata
    with open(raw / "validation_metadata.json", "r") as f:
        validation_metadata = json.load(f)

    # ==================================================================================
    # 1. Original Split: Create `new_train` and `new_test`
    # ==================================================================================
    if DEV:
        new_train, new_test = train_metadata[:90], train_metadata[90:]
    else:
        new_train, new_test = train_test_split(
            train_metadata, test_size=len(validation_metadata), random_state=0
        )
    logger.info(
        f"Created original split with {len(new_train)} train samples and {len(new_test)} test samples"
    )

    # ==================================================================================
    # 2. Process and Save Original Split to `public` and `private`
    # ==================================================================================
    public.mkdir(exist_ok=True)
    private.mkdir(exist_ok=True)

    # Copy train and test files
    _copy_data_files(new_train, raw, public / "train", include_masks=True)
    _copy_data_files(new_test, raw, public / "test", include_masks=False)

    # Create and save ground truth answers for the test set
    test_answers = _create_answers_df(new_test, raw)
    test_answers.to_csv(private / "answers.csv", index=False)

    # Save train metadata
    with open(public / "train_metadata.json", "w") as f:
        f.write(json.dumps(new_train))

    # Create and save a sample submission
    submission_df = test_answers.copy()
    random.seed(0)
    submission_df["encoded_pixels"] = [
        random.choice(["1 3 10 5", "-"]) for _ in range(len(submission_df))
    ]
    submission_df.to_csv(public / "sample_submission.csv", index=False)

    # Copy over existing validation data (this is unique to the original set)
    (raw / "validation").mkdir(exist_ok=True, parents=True)
    shutil.copytree(raw / "validation", public / "validation", dirs_exist_ok=True)
    shutil.copyfile(raw / "validation_metadata.json", public / "validation_metadata.json")

    # ==================================================================================
    # 3. New Validation Split: Split `new_train` into `train_val` and `test_val`
    # ==================================================================================
    train_val, test_val = train_test_split(
        new_train, test_size=len(new_test), random_state=0
    )
    logger.info(
        f"Created validation split with {len(train_val)} train_val samples and {len(test_val)} test_val samples"
    )

    # ==================================================================================
    # 4. Process and Save Validation Split to `public_val` and `private_val`
    # ==================================================================================
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"
    public_val.mkdir(exist_ok=True)
    private_val.mkdir(exist_ok=True)

    # Copy train_val and test_val files
    _copy_data_files(train_val, raw, public_val / "train", include_masks=True)
    _copy_data_files(test_val, raw, public_val / "test", include_masks=False)

    # Create and save ground truth answers for the test_val set
    test_val_answers = _create_answers_df(test_val, raw)
    # The filename must be "answers.csv" to mirror the private directory structure
    test_val_answers.to_csv(private_val / "answers.csv", index=False)

    # Save train_val metadata
    # The filename must be "train_metadata.json" to mirror the public directory structure
    with open(public_val / "train_metadata.json", "w") as f:
        f.write(json.dumps(train_val))

    # Create and save a sample submission for the validation set
    submission_val_df = test_val_answers.copy()
    random.seed(0)
    submission_val_df["encoded_pixels"] = [
        random.choice(["1 3 10 5", "-"]) for _ in range(len(submission_val_df))
    ]
    # The filename must be "sample_submission.csv" to mirror the public directory structure
    submission_val_df.to_csv(public_val / "sample_submission.csv", index=False)

    # ==================================================================================
    # 5. Sanity Checks
    # ==================================================================================
    logger.info("Performing sanity checks for original directories...")
    # Sanity checks for original directories
    assert (public / "train_metadata.json").exists(), "`train_metadata.json` doesn't exist!"
    assert (public / "sample_submission.csv").exists(), "`sample_submission.csv` doesn't exist!"
    assert (
        public / "validation_metadata.json"
    ).exists(), "`validation_metadata.json` doesn't exist!"
    assert (public / "train").exists(), "`train` directory doesn't exist!"
    assert (public / "test").exists(), "`test` directory doesn't exist!"
    assert (public / "validation").exists(), "`public` directory doesn't exist!"
    assert (private / "answers.csv").exists(), "`answers.csv` doesn't exist!"

    new_train_bands = list(img.stem for img in (public / "train").rglob("band*.npy"))
    assert (
        len(new_train_bands) == len(new_train) * 9
    ), f"Expected {len(new_train) * 9} bands in the train set, but got {len(new_train_bands)}!"
    new_test_bands = list(img.stem for img in (public / "test").rglob("band*.npy"))
    assert (
        len(new_test_bands) == len(new_test) * 9
    ), f"Expected {len(new_test) * 9} in the test set, but got {len(new_test_bands)}!"

    new_train_individual_masks = list(
        img.stem for img in (public / "train").rglob("human_individual_masks.npy")
    )
    assert len(new_train_individual_masks) == len(
        new_train
    ), f"Expected 1 human individual mask per sample in the train set, but got {len(new_train_individual_masks)}!"
    new_train_pixel_masks = list(
        img.stem for img in (public / "train").rglob("human_pixel_masks.npy")
    )
    assert len(new_train_pixel_masks) == len(
        new_train
    ), f"Expected 1 human pixel mask per sample in the train set, but got {len(new_train_pixel_masks)}!"

    logger.info("Performing sanity checks for validation directories...")
    # Sanity checks for new validation directories
    assert (public_val / "train_metadata.json").exists(), "`public_val/train_metadata.json` doesn't exist!"
    assert (public_val / "sample_submission.csv").exists(), "`public_val/sample_submission.csv` doesn't exist!"
    assert (public_val / "train").exists(), "`public_val/train` directory doesn't exist!"
    assert (public_val / "test").exists(), "`public_val/test` directory doesn't exist!"
    assert (private_val / "answers.csv").exists(), "`private_val/answers.csv` doesn't exist!"