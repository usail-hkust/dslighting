import json
import shutil
from pathlib import Path
from typing import List, Dict

import pandas as pd
import py7zr
from sklearn.model_selection import train_test_split

from mlebench.utils import extract


def _create_split_files(
    train_set: List[Dict],
    test_set: List[Dict],
    test_fields: List[str],
    public_dir: Path,
    private_dir: Path,
):
    """
    Helper function to generate all files for a given train/test split.

    This function creates:
    - public/{train.json.7z, test.json.7z, sample_submission.csv.7z}
    - private/{test.csv, sample_submission.csv}
    """
    # Ensure output directories exist
    public_dir.mkdir(exist_ok=True, parents=True)
    private_dir.mkdir(exist_ok=True, parents=True)

    # Create test set without labels
    test_set_without_labels = []
    for sample in test_set:
        sample_copy = {key: sample[key] for key in test_fields}
        test_set_without_labels.append(sample_copy)

    # Write new train and test splits to a temporary directory
    tmp_data_dir = private_dir / "tmp_data"
    tmp_data_dir.mkdir(exist_ok=True)
    try:
        with open(tmp_data_dir / "train.json", "w") as f:
            json.dump(train_set, f)
        with open(tmp_data_dir / "test.json", "w") as f:
            json.dump(test_set_without_labels, f)

        # Compress the JSON files into the public directory
        with py7zr.SevenZipFile(public_dir / "train.json.7z", "w") as archive:
            archive.write(
                tmp_data_dir / "train.json",
                arcname="train.json",
            )
        with py7zr.SevenZipFile(public_dir / "test.json.7z", "w") as archive:
            archive.write(
                tmp_data_dir / "test.json",
                arcname="test.json",
            )

        # Make answers as csv from the labeled test set
        answer_rows = [
            {"id": sample["id"], "is_iceberg": int(sample["is_iceberg"])}
            for sample in test_set
        ]
        answers = pd.DataFrame(answer_rows)
        answers.to_csv(private_dir / "test.csv", index=False)

        # Make a sample submission file
        sample_submission = answers.copy()
        sample_submission["is_iceberg"] = 0.5
        sample_submission.to_csv(private_dir / "sample_submission.csv", index=False)
        with py7zr.SevenZipFile(public_dir / "sample_submission.csv.7z", "w") as archive:
            archive.write(
                private_dir / "sample_submission.csv",
                arcname="sample_submission.csv",
            )
    finally:
        # Ensure temporary files are removed
        shutil.rmtree(tmp_data_dir)

    # --- Final checks for this split ---
    assert len(test_set) == len(
        test_set_without_labels
    ), f"Expected test_set ({len(test_set)}) to have the same length as test_set_without_labels ({len(test_set_without_labels)})"
    assert len(answers) == len(
        test_set
    ), f"Expected answers ({len(answers)}) to have the same length as test_set ({len(test_set)})"
    assert len(sample_submission) == len(
        test_set
    ), f"Expected sample_submission ({len(sample_submission)}) to have the same length as test_set ({len(test_set)})"
    assert set(answers.columns) == set(
        ["id", "is_iceberg"]
    ), "Answers must have 'id' and 'is_iceberg' columns"
    assert set(sample_submission.columns) == set(
        ["id", "is_iceberg"]
    ), "Sample submission must have 'id' and 'is_iceberg' columns"
    train_ids = set([sample["id"] for sample in train_set])
    test_ids = set([sample["id"] for sample in test_set])
    assert train_ids.isdisjoint(test_ids), "Train and test ids should not overlap"


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the data in raw into public and private datasets with appropriate test/train splits.
    Also creates a secondary validation split (public_val, private_val) for model development.
    """
    extract(raw / "train.json.7z", raw)
    extract(raw / "test.json.7z", raw)
    old_train = json.load((raw / "data/processed/train.json").open())
    old_test = json.load((raw / "data/processed/test.json").open())

    all_fields = list([key for key in old_train[0].keys()])
    assert all(
        set(all_fields) == set([key for key in sample.keys()]) for sample in old_train
    ), "Inconsistent fields in train set"
    test_fields = list([key for key in old_test[0].keys()])
    assert all(
        set(test_fields) == set([key for key in sample.keys()]) for sample in old_test
    ), "Inconsistent fields in test set"

    # --- First Split: Create the main train/test sets for the competition ---
    # Old ratio is Train set - 1,604 samples; Test set - 8,424 samples (~84% ratio)
    # We do a 20% ratio to avoid removing too many samples from train
    new_train, new_test = train_test_split(old_train, test_size=0.2, random_state=0)

    # Generate the original public and private directory files
    _create_split_files(
        train_set=new_train,
        test_set=new_test,
        test_fields=test_fields,
        public_dir=public,
        private_dir=private,
    )

    # Check that the total number of samples is conserved in the first split
    assert len(new_train) + len(new_test) == len(
        old_train
    ), f"Expected {len(old_train)} total samples in new_train ({len(new_train)}) and new_test ({len(new_test)})"

    # --- Second Split: Create a validation set from the main training set ---
    # Define paths for the new validation split
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # The goal is for the new validation set (test_val) to have the same size as the original test set (new_test).
    # test_size = len(new_test) / len(new_train) = (0.2 * N) / (0.8 * N) = 0.25
    test_size_for_val_split = len(new_test) / len(new_train)
    train_val, test_val = train_test_split(
        new_train, test_size=test_size_for_val_split, random_state=0
    )

    # Generate the validation public_val and private_val directory files
    _create_split_files(
        train_set=train_val,
        test_set=test_val,
        test_fields=test_fields,
        public_dir=public_val,
        private_dir=private_val,
    )