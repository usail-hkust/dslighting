from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


def _split_and_save(
    input_features: np.ndarray,
    input_labels: np.ndarray,
    test_proportion: float,
    random_state: int,
    output_public_path: Path,
    output_private_path: Path,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Helper function to perform a split, save files to specified paths, and return the new training set.

    This function encapsulates the logic for:
    1. Splitting input data into training and testing sets.
    2. Creating the necessary directory structure.
    3. Saving the training data, (unlabeled) test data, and sample submission to the public path.
    4. Saving the ground-truth test labels to the private path.
    5. Performing sanity checks on the created files.

    Args:
        input_features: The feature data to be split.
        input_labels: The corresponding labels for the feature data.
        test_proportion: The proportion of the dataset to allocate to the test split.
        random_state: The seed used by the random number generator for reproducibility.
        output_public_path: The base directory for public-facing files.
        output_private_path: The base directory for private/solution files.

    Returns:
        A tuple containing the features and labels of the newly created training set,
        which can be used for subsequent splits.
    """
    input_idxs = range(len(input_features))

    # Create new splits
    new_train_idxs, new_test_idxs = train_test_split(
        input_idxs, test_size=test_proportion, random_state=random_state
    )

    new_train = input_features[new_train_idxs]
    new_train_label = input_labels[new_train_idxs]
    new_test = input_features[new_test_idxs]
    new_test_label = input_labels[new_test_idxs]

    answers_df = pd.DataFrame({"Id": range(len(new_test)), "ClassId": new_test_label})

    # Create sample submission
    sample_submission = answers_df.copy()
    sample_submission["ClassId"] = 0

    # Create directories
    (output_public_path / "timit_11" / "timit_11").mkdir(parents=True, exist_ok=True)
    output_private_path.mkdir(parents=True, exist_ok=True)


    # Save files
    np.save(output_public_path / "timit_11" / "timit_11" / "train_11.npy", new_train)
    np.save(output_public_path / "timit_11" / "timit_11" / "train_label_11.npy", new_train_label)
    np.save(output_public_path / "timit_11" / "timit_11" / "test_11.npy", new_test)
    sample_submission.to_csv(output_public_path / "sampleSubmission.csv", index=False)
    answers_df.to_csv(output_private_path / "answers.csv", index=False)

    # Sanity checks
    assert (
        output_public_path / "timit_11" / "timit_11" / "train_11.npy"
    ).exists(), f"`train_11.npy` doesn't exist in {output_public_path}!"
    assert (
        output_public_path / "timit_11" / "timit_11" / "train_label_11.npy"
    ).exists(), f"`train_label_11.npy` doesn't exist in {output_public_path}!"
    assert (
        output_public_path / "timit_11" / "timit_11" / "test_11.npy"
    ).exists(), f"`test_11.npy` doesn't exist in {output_public_path}!"
    assert (
        output_public_path / "sampleSubmission.csv"
    ).exists(), f"`sampleSubmission.csv` doesn't exist in {output_public_path}!"
    assert (
        output_private_path / "answers.csv"
    ).exists(), f"`answers.csv` doesn't exist in {output_private_path}!"

    assert len(new_train) + len(new_test) == len(
        input_features
    ), f"Expected {len(input_features)} samples in combined new train and test splits, got {len(new_train) + len(new_test)}!"

    # Return the new training set for potential further splitting
    return new_train, new_train_label


def prepare(raw: Path, public: Path, private: Path):
    """
    Create a primary train/test split and a secondary train/validation split.
    The primary split results are saved to `public` and `private` directories.
    The secondary split results are saved to parallel `public_val` and `private_val` directories.
    """
    # Load original data from raw directory
    old_train = np.load(raw / "timit_11" / "timit_11" / "train_11.npy")
    old_train_label = np.load(raw / "timit_11" / "timit_11" / "train_label_11.npy")
    
    # Determine the test set proportion from the original competition data
    old_test = np.load(raw / "timit_11" / "timit_11" / "test_11.npy")
    old_test_prop = len(old_test) / (len(old_train) + len(old_test))  # ~= 0.268
    RANDOM_STATE = 0

    # --- First Split: Create Original public/private datasets ---
    # This call generates the exact same output as the original script.
    # It returns the features/labels of its training set, which we will use for the next split.
    train_for_val_split, train_label_for_val_split = _split_and_save(
        input_features=old_train,
        input_labels=old_train_label,
        test_proportion=old_test_prop,
        random_state=RANDOM_STATE,
        output_public_path=public,
        output_private_path=private,
    )

    # --- Second Split: Create New public_val/private_val datasets ---
    # Define the new parallel directories for the validation set
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Call the helper again, this time splitting the data from the *first* split's training set.
    # This creates the new training set (train_val) and validation set (test_val).
    # The splitting logic, proportion, and random state are identical to the first split.
    _split_and_save(
        input_features=train_for_val_split,
        input_labels=train_label_for_val_split,
        test_proportion=old_test_prop,
        random_state=RANDOM_STATE,
        output_public_path=public_val,
        output_private_path=private_val,
    )