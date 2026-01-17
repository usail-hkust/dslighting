from pathlib import Path
import pandas as pd

from sklearn.model_selection import train_test_split

from mlebench.utils import read_csv


def _split_and_save(
    source_df: pd.DataFrame,
    public_dir: Path,
    private_dir: Path,
    test_size: float,
    random_state: int,
) -> pd.DataFrame:
    """
    Splits a dataframe into train and test sets and saves them to the specified
    public and private directories, mimicking the competition data format.

    Args:
        source_df: The dataframe to be split.
        public_dir: The directory for public-facing files (train set, unlabeled test set).
        private_dir: The directory for private-facing files (test set labels).
        test_size: The proportion of the dataset to allocate to the test split.
        random_state: The seed used by the random number generator.

    Returns:
        The training set dataframe resulting from the split.
    """
    # Create train, test split
    new_train, new_test = train_test_split(
        source_df, test_size=test_size, random_state=random_state
    )
    new_test_without_labels = new_test.drop(columns=["answer_start", "answer_text"])

    # make private test match submission format
    new_test_labels = new_test[["id", "answer_text"]]
    new_test_labels.columns = ["id", "PredictionString"]

    # Ensure output directories exist
    public_dir.mkdir(exist_ok=True)
    private_dir.mkdir(exist_ok=True)
    
    # Copy over files
    new_train.to_csv(public_dir / "train.csv", index=False)
    new_test_without_labels.to_csv(public_dir / "test.csv", index=False)
    new_test_labels.to_csv(private_dir / "test.csv", index=False)

    # Create sample submission
    sample_submission = new_test_labels.copy()
    sample_submission["PredictionString"] = "dummy text"
    sample_submission.to_csv(public_dir / "sample_submission.csv", index=False)

    assert len(sample_submission) == len(
        new_test_labels
    ), "Sample submission length does not match test length."

    return new_train


def prepare(raw: Path, public: Path, private: Path):

    # --- Define paths for the new validation split ---
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Load the initial raw training data
    original_train_df = read_csv(raw / "train.csv")

    # --- First Split: Create original train/test sets ---
    # This split generates the main competition files in `public` and `private`.
    # The outputs of this step must remain identical to the original script.
    main_train_set = _split_and_save(
        source_df=original_train_df,
        public_dir=public,
        private_dir=private,
        test_size=0.1,
        random_state=0,
    )

    # --- Second Split: Create validation train/test sets from the main train set ---
    # This split uses the *training data* from the first split as its source.
    # The new `test_val` set will have approx. the same size as the original `test` set.
    # test_size for 2nd split = (size of original test) / (size of new train)
    # = (0.1 * total) / (0.9 * total) = 0.1 / 0.9
    validation_test_size = 0.1 / (1.0 - 0.1)

    _split_and_save(
        source_df=main_train_set,
        public_dir=public_val,
        private_dir=private_val,
        test_size=validation_test_size,
        random_state=0,  # Use the same random state for consistency
    )