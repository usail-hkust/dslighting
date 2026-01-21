from pathlib import Path

from sklearn.model_selection import train_test_split

from mlebench.competitions.utils import df_to_one_hot
from mlebench.utils import extract, read_csv

from .classes import CLASSES


def prepare(raw: Path, public: Path, private: Path):
    target_col = "author"
    id_col = "id"

    # extract only what we need
    extract(raw / "train.zip", raw)

    # =================================================================
    # == Original Data Split (for `public` and `private` directories)
    # =================================================================
    # Create main train/test split from the raw data
    old_train = read_csv(raw / "train.csv")
    train_main, test_main = train_test_split(old_train, test_size=0.1, random_state=0)
    test_main_without_labels = test_main.drop(columns=[target_col])

    # private test matches the format of sample submission
    one_hot_test_main = df_to_one_hot(
        test_main.drop(columns=["text"]),
        id_column=id_col,
        target_column=target_col,
        classes=CLASSES,
    )
    # fill the sample submission with arbitrary values (matching kaggle.com)
    sample_submission = one_hot_test_main.copy()
    sample_submission["EAP"] = 0.403493538995863
    sample_submission["HPL"] = 0.287808366106543
    sample_submission["MWS"] = 0.308698094897594

    # save files to original public/private directories
    train_main.to_csv(public / "train.csv", index=False)
    test_main_without_labels.to_csv(public / "test.csv", index=False)
    sample_submission.to_csv(public / "sample_submission.csv", index=False)
    one_hot_test_main.to_csv(private / "test.csv", index=False)

    # =====================================================================
    # == New Validation Split (for `public_val` and `private_val` dirs)
    # =====================================================================
    # Define and create the new parallel directories for the validation set
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"
    public_val.mkdir(parents=True, exist_ok=True)
    private_val.mkdir(parents=True, exist_ok=True)

    # Split the main training set again to create a new, smaller training set and a validation set.
    # The logic and random_state are replicated to ensure the validation set size is
    # consistent with the main test set size.
    train_val, test_val = train_test_split(train_main, test_size=0.1, random_state=0)
    test_val_without_labels = test_val.drop(columns=[target_col])

    # Process the new validation set's labels, mirroring the original logic
    one_hot_test_val = df_to_one_hot(
        test_val.drop(columns=["text"]),
        id_column=id_col,
        target_column=target_col,
        classes=CLASSES,
    )

    # Create a new sample submission for the validation set
    sample_submission_val = one_hot_test_val.copy()
    sample_submission_val["EAP"] = 0.403493538995863
    sample_submission_val["HPL"] = 0.287808366106543
    sample_submission_val["MWS"] = 0.308698094897594

    # Save files to the new validation directories using identical filenames
    train_val.to_csv(public_val / "train.csv", index=False)
    test_val_without_labels.to_csv(public_val / "test.csv", index=False)
    sample_submission_val.to_csv(public_val / "sample_submission.csv", index=False)
    one_hot_test_val.to_csv(private_val / "test.csv", index=False)