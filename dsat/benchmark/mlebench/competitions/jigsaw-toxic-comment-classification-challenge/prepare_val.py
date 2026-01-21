from pathlib import Path

from sklearn.model_selection import train_test_split

from mlebench.utils import extract, read_csv

from .classes import CLASSES


def prepare(raw: Path, public: Path, private: Path):
    # extract only what is needed
    extract(raw / "train.csv.zip", raw)
    extract(raw / "test.csv.zip", raw)
    extract(raw / "test_labels.csv.zip", raw)
    extract(raw / "sample_submission.csv.zip", raw)

    # the test set is provided, so we dont have to split the train set nor form the sample submission
    train_with_labels = read_csv(raw / "train.csv")
    test_without_labels = read_csv(raw / "test.csv")
    answers = read_csv(raw / "test_labels.csv")
    sample_submission = read_csv(raw / "sample_submission.csv")
    sample_submission[CLASSES] = 0.5

    # save to public
    train_with_labels.to_csv(public / "train.csv", index=False)
    test_without_labels.to_csv(public / "test.csv", index=False)
    sample_submission.to_csv(public / "sample_submission.csv", index=False)

    # save to private
    answers.to_csv(private / "test.csv", index=False)

    assert len(answers) == len(
        sample_submission
    ), "Private test set and sample submission should be of the same length"

    assert sorted(answers["id"]) == sorted(
        test_without_labels["id"]
    ), "Private and Public test IDs should match"
    assert sorted(sample_submission["id"]) == sorted(
        test_without_labels["id"]
    ), "Public test and sample submission IDs should match"
    assert (
        len(set(train_with_labels["id"]) & set(test_without_labels["id"])) == 0
    ), "Train and test IDs should not overlap"

    # ==================================================================
    # === New code for creating the validation set starts here ===
    # The code above this line is untouched to ensure original outputs
    # remain identical.
    # ==================================================================

    # 1. Define new paths and create the directories for the validation set.
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"
    public_val.mkdir(exist_ok=True)
    private_val.mkdir(exist_ok=True)

    # 2. Split the original training data to create a new, smaller training set
    # and a new validation set. The size of the validation set will be the same
    # as the size of the original test set.
    validation_set_size = len(test_without_labels)
    train_val, test_val_with_labels = train_test_split(
        train_with_labels,
        test_size=validation_set_size,
        random_state=42,  # Use a fixed random state for reproducibility
    )

    # 3. Prepare the validation set files, mirroring the original test set structure.
    # The public part (input features, without labels)
    test_val_without_labels = test_val_with_labels[["id", "comment_text"]].copy()

    # The private part (ground truth labels for the validation set)
    answers_val = test_val_with_labels[["id"] + CLASSES].copy()

    # 4. Create a sample submission file for the new validation set,
    # mirroring the original sample submission format.
    sample_submission_val = test_val_without_labels[["id"]].copy()
    sample_submission_val[CLASSES] = 0.5

    # 5. Save the new sets to the 'public_val' and 'private_val' directories,
    # using the same filenames as in the original 'public' and 'private' dirs.
    # Save to public_val
    train_val.to_csv(public_val / "train.csv", index=False)
    test_val_without_labels.to_csv(public_val / "test.csv", index=False)
    sample_submission_val.to_csv(public_val / "sample_submission.csv", index=False)

    # Save to private_val
    answers_val.to_csv(private_val / "test.csv", index=False)