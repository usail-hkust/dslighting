import json
import shutil
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from sklearn.model_selection import train_test_split


def _create_split(
    data_to_split: List[Dict],
    test_size: float,
    test_fields: List[str],
    public_path: Path,
    private_path: Path,
    random_state: int,
) -> List[Dict]:
    """
    Helper function to perform a data split and create all required files.

    Args:
        data_to_split: The list of data samples to be split.
        test_size: The proportion of the dataset to allocate to the test split.
        test_fields: The list of fields to keep in the test set.
        public_path: The directory for public-facing files (train set, unlabeled test set).
        private_path: The directory for private files (test set labels).
        random_state: The seed for the random number generator.

    Returns:
        The training portion of the split, to be used for subsequent splits if needed.
    """
    # Create output directories if they don't exist
    public_path.mkdir(parents=True, exist_ok=True)
    private_path.mkdir(parents=True, exist_ok=True)

    # Create train, test from the provided data
    train_set, test_set = train_test_split(
        data_to_split, test_size=test_size, random_state=random_state
    )

    test_set_without_labels = []
    for sample in test_set:
        # Keep only the fields that should be in the test set
        sample_unlabeled = {key: sample[key] for key in test_fields}
        test_set_without_labels.append(sample_unlabeled)

    # Save the new train and test splits to the public directory
    with open(public_path / "train.json", "w") as f:
        json.dump(train_set, f, indent=4)
    with open(public_path / "test.json", "w") as f:
        json.dump(test_set_without_labels, f, indent=4)
    # Also save zipped versions
    shutil.make_archive(public_path / "train", "zip", public_path, "train.json")
    shutil.make_archive(public_path / "test", "zip", public_path, "test.json")

    # Create answers for the private directory
    answers_rows = []
    for sample in test_set:
        answers_rows.append(
            {
                "request_id": sample["request_id"],
                "requester_received_pizza": int(sample["requester_received_pizza"]),
            }
        )
    answers = pd.DataFrame(answers_rows)
    answers.to_csv(private_path / "test.csv", index=False)

    # Create sample submission for the public directory
    sample_submission = answers.copy()
    sample_submission["requester_received_pizza"] = 0
    sample_submission.to_csv(public_path / "sampleSubmission.csv", index=False)

    # Perform checks
    assert len(train_set) + len(test_set) == len(
        data_to_split
    ), f"Expected {len(data_to_split)} total samples, but got {len(train_set)} in train and {len(test_set)} in test"
    assert len(test_set) == len(
        test_set_without_labels
    ), "Test set and unlabeled test set must have the same length"
    assert len(answers) == len(test_set), "Answers must have the same length as the test set"
    assert len(sample_submission) == len(
        test_set
    ), "Sample submission must have the same length as the test set"
    assert set(answers.columns) == set(
        ["request_id", "requester_received_pizza"]
    ), "Answers must have 'request_id' and 'requester_received_pizza' columns"
    assert set(sample_submission.columns) == set(
        ["request_id", "requester_received_pizza"]
    ), "Sample submission must have 'request_id' and 'requester_received_pizza' columns"

    return train_set


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the data in raw into public and private datasets with appropriate test/train splits.
    Then, it creates a second, parallel validation split from the first training set.
    """

    # Load data
    with open(raw / "train.json") as f:
        old_train = json.load(f)
    with open(raw / "test.json") as f:
        old_test = json.load(f)

    test_ratio = len(old_test) / (len(old_train) + len(old_test))

    all_fields = list([key for key in old_train[0].keys()])
    assert all(set(all_fields) == set([key for key in sample.keys()]) for sample in old_train)
    test_fields = list([key for key in old_test[0].keys()])
    assert all(set(test_fields) == set([key for key in sample.keys()]) for sample in old_test)

    # --- Original Split ---
    # This split creates the primary `public` and `private` competition data.
    # The returned `new_train` set will be used for the subsequent validation split.
    new_train = _create_split(
        data_to_split=old_train,
        test_size=test_ratio,
        test_fields=test_fields,
        public_path=public,
        private_path=private,
        random_state=0,
    )

    # --- New Validation Split ---
    # Define new directories for the validation set, parallel to the original ones.
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # To keep the new test set (`test_val`) size consistent with the original test set,
    # we adjust the test ratio for the second split.
    # val_test_size = original_test_size / original_train_size
    val_test_size = test_ratio / (1.0 - test_ratio)

    # Create the validation split using the same logic, but on the `new_train` data
    # and saving to the new `_val` directories.
    _create_split(
        data_to_split=new_train,
        test_size=val_test_size,
        test_fields=test_fields,
        public_path=public_val,
        private_path=private_val,
        random_state=0,
    )