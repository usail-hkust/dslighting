from pathlib import Path

from sklearn.model_selection import train_test_split

from mlebench.utils import read_csv


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the data in raw into public and private datasets with appropriate test/train splits.
    Additionally, it creates a secondary validation split for model development.
    """
    # Create directories for the primary competition split
    public.mkdir(exist_ok=True)
    private.mkdir(exist_ok=True)

    # Create directories for the new validation split
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"
    public_val.mkdir(exist_ok=True)
    private_val.mkdir(exist_ok=True)

    # Load raw data
    old_train = read_csv(raw / "train.csv")

    # --- Block 1: Original Split (for final competition data) ---
    # This block creates the main train/test split. Its output in `public`
    # and `private` must remain unchanged from the original script.

    # Create train, test from the full raw data
    train, test = train_test_split(old_train, test_size=0.1, random_state=0)
    test_without_labels = test.drop(columns=["score"])

    # Save new train and test to the original directories
    train.to_csv(public / "train.csv", index=False)
    test.to_csv(private / "test.csv", index=False)
    test_without_labels.to_csv(public / "test.csv", index=False)

    assert len(train) + len(test) == len(old_train)
    assert len(test) == len(test_without_labels)

    # Create a sample submission file for the original test set
    submission_df = test.copy()[["id", "score"]]
    submission_df["score"] = 0
    submission_df.to_csv(public / "sample_submission.csv", index=False)

    assert len(submission_df) == len(test)

    # --- Block 2: New Validation Split (for model development) ---
    # This block takes the `train` data from the first split and splits it
    # again to create a new, smaller training set and a validation set.
    # The logic and filenames mirror the original split for consistency.

    # Create a new train/validation split from the main training set
    train_val, test_val = train_test_split(train, test_size=0.1, random_state=0)
    test_val_without_labels = test_val.drop(columns=["score"])

    # Save the new validation split data into the `_val` directories
    train_val.to_csv(public_val / "train.csv", index=False)
    test_val.to_csv(private_val / "test.csv", index=False)
    test_val_without_labels.to_csv(public_val / "test.csv", index=False)

    assert len(train_val) + len(test_val) == len(train)
    assert len(test_val) == len(test_val_without_labels)

    # Create a sample submission file for the new validation set
    submission_val_df = test_val.copy()[["id", "score"]]
    submission_val_df["score"] = 0
    submission_val_df.to_csv(public_val / "sample_submission.csv", index=False)

    assert len(submission_val_df) == len(test_val)