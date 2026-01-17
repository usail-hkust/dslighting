import csv
import zipfile
from pathlib import Path

from sklearn.model_selection import train_test_split

from mlebench.utils import compress, extract, read_csv


def _process_split(input_df, public_path, private_path, test_size, random_state):
    """
    Splits an input DataFrame into train and test sets, processes them,
    and writes the final files to the specified public and private paths.

    This function encapsulates the entire data preparation logic for one split,
    ensuring it can be reused for creating both the main test set and a
    subsequent validation set.

    Args:
        input_df: The DataFrame to be split.
        public_path: The directory to save public artifacts (e.g., train data, test features).
        private_path: The directory to save private artifacts (e.g., test labels).
        test_size: The proportion of the dataset to allocate to the test split.
        random_state: The seed used by the random number generator.

    Returns:
        The newly created training DataFrame, which can be used for a subsequent split.
    """
    # Create train and test splits from the provided dataframe
    # We split so that we don't share any sentence_ids between train and test
    unique_sentence_ids = input_df["sentence_id"].unique()
    train_sentence_ids, test_sentence_ids = train_test_split(
        unique_sentence_ids, test_size=test_size, random_state=random_state
    )
    new_train = input_df[input_df["sentence_id"].isin(train_sentence_ids)]
    answers = input_df[input_df["sentence_id"].isin(test_sentence_ids)]
    assert set(new_train["sentence_id"]).isdisjoint(
        set(answers["sentence_id"])
    ), f"sentence_id is not disjoint between train and test sets"

    # "sentence_id" counts need to be reset for new_train and answers
    new_train_id_mapping = {
        old_id: new_id for new_id, old_id in enumerate(new_train["sentence_id"].unique())
    }
    new_train["sentence_id"] = new_train["sentence_id"].map(new_train_id_mapping)
    answers_id_mapping = {
        old_id: new_id for new_id, old_id in enumerate(answers["sentence_id"].unique())
    }
    answers["sentence_id"] = answers["sentence_id"].map(answers_id_mapping)

    # Create new test set
    new_test = answers.drop(["after", "class"], axis=1).copy()

    # Reformat answers to match sample submission format
    answers = answers[["sentence_id", "token_id", "after"]].copy()
    answers["id"] = answers["sentence_id"].astype(str) + "_" + answers["token_id"].astype(str)
    answers = answers[["id", "after"]]

    # Create sample submission
    sample_submission = new_test[["sentence_id", "token_id", "before"]].copy()
    sample_submission["id"] = (
        sample_submission["sentence_id"].astype(str)
        + "_"
        + sample_submission["token_id"].astype(str)
    )
    sample_submission["after"] = sample_submission["before"]
    sample_submission = sample_submission[["id", "after"]]

    # Checks
    assert new_train.columns.tolist() == [
        "sentence_id",
        "token_id",
        "class",
        "before",
        "after",
    ], f"new_train.columns.tolist() == {new_train.columns.tolist()}"
    assert new_test.columns.tolist() == [
        "sentence_id",
        "token_id",
        "before",
    ], f"new_test.columns.tolist() == {new_test.columns.tolist()}"
    assert sample_submission.columns.tolist() == [
        "id",
        "after",
    ], f"sample_submission.columns.tolist() == {sample_submission.columns.tolist()}"
    assert answers.columns.tolist() == [
        "id",
        "after",
    ], f"answers.columns.tolist() == {answers.columns.tolist()}"
    assert len(new_test) + len(new_train) == len(
        input_df
    ), f"New train and test sets do not sum to old train set, got {len(new_test) + len(new_train)} and {len(input_df)}"

    # Write CSVs
    answers.to_csv(
        private_path / "answers.csv", index=False, quotechar='"', quoting=csv.QUOTE_NONNUMERIC
    )
    sample_submission.to_csv(
        private_path / "sample_submission.csv", index=False, quotechar='"', quoting=csv.QUOTE_NONNUMERIC
    )
    new_train.to_csv(
        public_path / "ru_train.csv", index=False, quotechar='"', quoting=csv.QUOTE_NONNUMERIC
    )
    new_test.to_csv(
        public_path / "ru_test_2.csv", index=False, quotechar='"', quoting=csv.QUOTE_NONNUMERIC
    )
    sample_submission.to_csv(
        public_path / "ru_sample_submission_2.csv",
        index=False,
        quotechar='"',
        quoting=csv.QUOTE_NONNUMERIC,
    )

    # Zip up
    with zipfile.ZipFile(public_path / "ru_train.csv.zip", "w") as zipf:
        zipf.write(public_path / "ru_train.csv", arcname="ru_train.csv")
    with zipfile.ZipFile(public_path / "ru_test_2.csv.zip", "w") as zipf:
        zipf.write(public_path / "ru_test_2.csv", arcname="ru_test_2.csv")
    with zipfile.ZipFile(public_path / "ru_sample_submission_2.csv.zip", "w") as zipf:
        zipf.write(public_path / "ru_sample_submission_2.csv", arcname="ru_sample_submission_2.csv")
    (public_path / "ru_train.csv").unlink()
    (public_path / "ru_test_2.csv").unlink()
    (public_path / "ru_sample_submission_2.csv").unlink()

    return new_train


def prepare(raw: Path, public: Path, private: Path):
    # Define paths for the new validation set split
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Create all output directories ahead of time
    for p in [public, private, public_val, private_val]:
        p.mkdir(parents=True, exist_ok=True)

    # Extract
    extract(raw / "ru_test_2.csv.zip", raw)  # We only use the 2nd stage test set
    extract(raw / "ru_train.csv.zip", raw)
    extract(raw / "ru_sample_submission_2.csv.zip", raw)

    # Load initial raw data
    initial_train_data = read_csv(raw / "ru_train.csv")

    # --- First Split: Create Original Train and Test sets ---
    # This call generates the final public/private outputs. These must not be changed.
    # The returned DataFrame is the training set from this split.
    main_train_set = _process_split(
        input_df=initial_train_data,
        public_path=public,
        private_path=private,
        test_size=0.1,
        random_state=0,
    )

    # --- Second Split: Create New Train and Validation sets ---
    # This call takes the training data from the first split and splits it again
    # using the exact same logic. The outputs are written to the new _val directories.
    _ = _process_split(
        input_df=main_train_set,
        public_path=public_val,
        private_path=private_val,
        test_size=0.1,  # Use same proportion
        random_state=0, # Use same random seed for consistent splitting logic
    )