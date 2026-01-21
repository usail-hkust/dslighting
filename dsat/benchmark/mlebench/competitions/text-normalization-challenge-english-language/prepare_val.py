import csv
import zipfile
from pathlib import Path
from typing import Tuple

import pandas as pd
from sklearn.model_selection import train_test_split

from mlebench.utils import extract, read_csv


def _split_and_process(
    input_df: pd.DataFrame, test_size: float, random_state: int
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splits a DataFrame into train/test sets and processes them for the competition format.

    This function encapsulates the core logic of splitting data based on unique sentence IDs,
    re-indexing the new splits, and creating the corresponding test data, answers, and
    sample submission files.

    Args:
        input_df: The DataFrame to split.
        test_size: The proportion of the dataset to allocate to the test split.
        random_state: The seed used by the random number generator.

    Returns:
        A tuple containing:
        - new_train_df: The processed training data.
        - new_test_df: The processed, unlabeled test data.
        - answers_df: The ground truth labels for the test data.
        - submission_df: A sample submission file for the test data.
    """
    # We split so that we don't share any sentence_ids between train and test
    unique_sentence_ids = input_df["sentence_id"].unique()
    train_sentence_ids, test_sentence_ids = train_test_split(
        unique_sentence_ids, test_size=test_size, random_state=random_state
    )
    new_train_df = input_df[input_df["sentence_id"].isin(train_sentence_ids)].copy()
    answers_df = input_df[input_df["sentence_id"].isin(test_sentence_ids)].copy()
    assert set(new_train_df["sentence_id"]).isdisjoint(
        set(answers_df["sentence_id"])
    ), f"sentence_id is not disjoint between train and test sets"

    # "sentence_id" counts need to be reset for new_train_df and answers_df
    new_train_id_mapping = {
        old_id: new_id
        for new_id, old_id in enumerate(new_train_df["sentence_id"].unique())
    }
    new_train_df.loc[:, "sentence_id"] = new_train_df["sentence_id"].map(
        new_train_id_mapping
    )
    answers_id_mapping = {
        old_id: new_id
        for new_id, old_id in enumerate(answers_df["sentence_id"].unique())
    }
    answers_df.loc[:, "sentence_id"] = answers_df["sentence_id"].map(answers_id_mapping)

    # Create new test set
    new_test_df = answers_df.drop(["after", "class"], axis=1).copy()

    # Reformat answers to match sample submission format
    answers_formatted = answers_df[["sentence_id", "token_id", "after"]].copy()
    answers_formatted["id"] = (
        answers_formatted["sentence_id"].astype(str)
        + "_"
        + answers_formatted["token_id"].astype(str)
    )
    answers_formatted = answers_formatted[["id", "after"]]

    # Create sample submission
    submission_df = new_test_df[["sentence_id", "token_id", "before"]].copy()
    submission_df["id"] = (
        submission_df["sentence_id"].astype(str)
        + "_"
        + submission_df["token_id"].astype(str)
    )
    submission_df["after"] = submission_df["before"]
    submission_df = submission_df[["id", "after"]]

    # Checks
    assert new_train_df.columns.tolist() == [
        "sentence_id",
        "token_id",
        "class",
        "before",
        "after",
    ], f"new_train_df.columns.tolist() == {new_train_df.columns.tolist()}"
    assert new_test_df.columns.tolist() == [
        "sentence_id",
        "token_id",
        "before",
    ], f"new_test_df.columns.tolist() == {new_test_df.columns.tolist()}"
    assert submission_df.columns.tolist() == [
        "id",
        "after",
    ], f"submission_df.columns.tolist() == {submission_df.columns.tolist()}"
    assert answers_formatted.columns.tolist() == [
        "id",
        "after",
    ], f"answers_formatted.columns.tolist() == {answers_formatted.columns.tolist()}"
    assert len(new_test_df) + len(new_train_df) == len(
        input_df
    ), f"New train and test sets do not sum to old train set, got {len(new_test_df) + len(new_train_df)} and {len(input_df)}"

    return new_train_df, new_test_df, answers_formatted, submission_df


def _write_and_zip_outputs(
    public_dir: Path,
    private_dir: Path,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    answers_df: pd.DataFrame,
    submission_df: pd.DataFrame,
):
    """
    Writes the processed DataFrames to the specified directories and creates zip archives.
    """
    public_dir.mkdir(exist_ok=True, parents=True)
    private_dir.mkdir(exist_ok=True, parents=True)

    # Define file paths
    answers_path = private_dir / "answers.csv"
    private_submission_path = private_dir / "sample_submission.csv"
    public_train_path = public_dir / "en_train.csv"
    public_test_path = public_dir / "en_test_2.csv"
    public_submission_path = public_dir / "en_sample_submission_2.csv"

    # Write CSVs
    answers_df.to_csv(
        answers_path, index=False, quotechar='"', quoting=csv.QUOTE_NONNUMERIC
    )
    submission_df.to_csv(
        private_submission_path,
        index=False,
        quotechar='"',
        quoting=csv.QUOTE_NONNUMERIC,
    )
    train_df.to_csv(
        public_train_path, index=False, quotechar='"', quoting=csv.QUOTE_NONNUMERIC
    )
    test_df.to_csv(
        public_test_path, index=False, quotechar='"', quoting=csv.QUOTE_NONNUMERIC
    )
    submission_df.to_csv(
        public_submission_path,
        index=False,
        quotechar='"',
        quoting=csv.QUOTE_NONNUMERIC,
    )

    # Zip up public files
    with zipfile.ZipFile(public_dir / "en_train.csv.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(public_train_path, arcname="en_train.csv")
    with zipfile.ZipFile(public_dir / "en_test_2.csv.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(public_test_path, arcname="en_test_2.csv")
    with zipfile.ZipFile(
        public_dir / "en_sample_submission_2.csv.zip", "w", zipfile.ZIP_DEFLATED
    ) as zipf:
        zipf.write(public_submission_path, arcname="en_sample_submission_2.csv")

    # Clean up intermediate CSVs
    public_train_path.unlink()
    public_test_path.unlink()
    public_submission_path.unlink()


def prepare(raw: Path, public: Path, private: Path):

    # Extract
    extract(raw / "en_test_2.csv.zip", raw)  # We only use the 2nd stage test set
    extract(raw / "en_train.csv.zip", raw)
    extract(raw / "en_sample_submission_2.csv.zip", raw)

    # Load original training data
    old_train = read_csv(raw / "en_train.csv")

    # --- Stage 1: Create the original train/test split ---
    new_train, new_test, answers, sample_submission = _split_and_process(
        input_df=old_train, test_size=0.1, random_state=0
    )

    # Write the original public and private directory files
    _write_and_zip_outputs(
        public_dir=public,
        private_dir=private,
        train_df=new_train,
        test_df=new_test,
        answers_df=answers,
        submission_df=sample_submission,
    )

    # --- Stage 2: Create the new train_val/test_val split ---
    # Define new output directories for the validation split
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Create the validation split from the 'new_train' data generated in Stage 1
    # We use the same splitting logic and parameters to ensure consistency.
    train_val, test_val, answers_val, submission_val = _split_and_process(
        input_df=new_train, test_size=0.1, random_state=0
    )

    # Write the validation public and private directory files
    _write_and_zip_outputs(
        public_dir=public_val,
        private_dir=private_val,
        train_df=train_val,
        test_df=test_val,
        answers_df=answers_val,
        submission_df=submission_val,
    )