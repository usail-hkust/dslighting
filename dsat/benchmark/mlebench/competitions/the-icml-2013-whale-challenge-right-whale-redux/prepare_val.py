import re
import shutil
from pathlib import Path
from typing import List

import pandas as pd
from tqdm import tqdm


def _create_split(
    train_files: List[Path],
    test_files: List[Path],
    public_path: Path,
    private_path: Path,
):
    """
    Helper function to process and save a single train/test split.

    This function handles file copying, renaming, zipping, and the creation of
    answer and sample submission files for a given set of train/test files.
    """
    # Create output directories if they don't exist
    public_path.mkdir(exist_ok=True, parents=True)
    private_path.mkdir(exist_ok=True, parents=True)

    # Process and copy train files
    train_output_dir = public_path / "train2"
    train_output_dir.mkdir(exist_ok=True)
    # Sort files to ensure deterministic indexing
    sorted_train_files = sorted(train_files)
    for idx, sample in enumerate(
        tqdm(sorted_train_files, desc=f"Creating train set for {public_path.name}")
    ):
        new_sample_name = re.sub(r"TRAIN\d+", f"TRAIN{idx}", sample.name)
        new_sample = train_output_dir / new_sample_name
        shutil.copy(sample, new_sample)

    # Process and copy test files, collecting answers
    answer_rows = []
    test_output_dir = public_path / "test2"
    test_output_dir.mkdir(exist_ok=True)
    # Sort files to ensure deterministic indexing
    sorted_test_files = sorted(test_files)
    for idx, sample in enumerate(
        tqdm(sorted_test_files, desc=f"Creating test set for {public_path.name}")
    ):
        new_sample_name = sample.name.split("TRAIN")[0] + f"Test{idx}.aif"
        new_sample = test_output_dir / new_sample_name
        shutil.copy(sample, new_sample)
        answer_rows.append(
            {"clip": new_sample_name, "probability": 1 if sample.stem.endswith("_1") else 0}
        )

    # Assertions to verify file counts
    assert len(sorted_train_files) == len(list(train_output_dir.glob("*.aif")))
    assert len(sorted_test_files) == len(list(test_output_dir.glob("*.aif")))

    # Create zipped versions and remove temporary unzipped directories
    shutil.make_archive(public_path / "train2", "zip", public_path, "train2")
    shutil.make_archive(public_path / "test2", "zip", public_path, "test2")
    shutil.rmtree(train_output_dir)
    shutil.rmtree(test_output_dir)

    # Create answer file
    answers_df = pd.DataFrame(answer_rows)
    answers_df.to_csv(private_path / "test.csv", index=False)
    assert set(answers_df.columns) == set(["clip", "probability"])

    # Create sample submission file
    sample_submission = answers_df.copy()
    sample_submission["probability"] = 0
    sample_submission.to_csv(public_path / "sampleSubmission.csv", index=False)
    assert set(sample_submission.columns) == set(["clip", "probability"])


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the data in raw into public and private datasets with appropriate test/train splits.
    Also creates a secondary validation split in public_val/private_val directories.
    """
    # Data is in train2.zip - we need to unzip it
    shutil.unpack_archive(raw / "train2.zip", raw)

    # Files are named as
    # Train: "YYYYMMDD_HHMMSS_{seconds}_TRAIN{idx}_{label:0,1}.aif"
    # Test: "YYYYMMDD_HHMMSS_{seconds}_Test{idx}.aif"

    # There are 4 days in Train and 3 days in Test
    # In our new dataset, we'll just split Train_old into 2 days for Train and 2 days for Test

    samples_by_date = {}
    n_train_old = 0
    for sample in (raw / "train2").iterdir():
        date = sample.name.split("_")[0]
        if date not in samples_by_date:
            samples_by_date[date] = []
        samples_by_date[date].append(sample)
        n_train_old += 1

    assert len(samples_by_date) == 4, "Expected 4 days in Train_old"
    dates = sorted(list(samples_by_date.keys()))

    # --- 1. Create the Original Split (public/private) ---
    # This split uses the first two days for training and the last two days for testing.
    # The outputs of this step must remain identical to the original script.
    original_train_files = samples_by_date[dates[0]] + samples_by_date[dates[1]]
    original_test_files = samples_by_date[dates[2]] + samples_by_date[dates[3]]

    _create_split(
        train_files=original_train_files,
        test_files=original_test_files,
        public_path=public,
        private_path=private,
    )

    # --- 2. Create the New Validation Split (public_val/private_val) ---
    # This second split takes the original *training* data (the first two days) and
    # splits it again, using the same date-based logic. The first day becomes the
    # new training set, and the second day becomes the new validation (test) set.
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    validation_train_files = samples_by_date[dates[0]]
    validation_test_files = samples_by_date[dates[1]]

    _create_split(
        train_files=validation_train_files,
        test_files=validation_test_files,
        public_path=public_val,
        private_path=private_val,
    )

    # Final cleanup of the raw unzipped directory after all processing is complete
    shutil.rmtree(raw / "train2")

    # Final top-level assertions from the original script
    assert (
        len(original_train_files) + len(original_test_files) == n_train_old
    ), f"Expected {n_train_old} total samples in new_train ({len(original_train_files)}) and new_test ({len(original_test_files)})"
    assert (public / "sampleSubmission.csv").exists()
    assert (private / "test.csv").exists()