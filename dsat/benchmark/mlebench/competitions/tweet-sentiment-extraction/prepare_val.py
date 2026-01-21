from pathlib import Path
import pandas as pd

from sklearn.model_selection import train_test_split

from mlebench.utils import read_csv


def _split_and_save(
    source_df: pd.DataFrame,
    test_size: float,
    random_state: int,
    public_dir: Path,
    private_dir: Path,
    label_col: str = "selected_text",
    id_col: str = "textID",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Helper function to perform a train/test split and save the results.

    Args:
        source_df: The DataFrame to split.
        test_size: The proportion of the dataset to allocate to the test split.
        random_state: The seed used by the random number generator.
        public_dir: The directory to save public artifacts (train set, unlabeled test set).
        private_dir: The directory to save private artifacts (labeled test set).
        label_col: The name of the column containing the label.
        id_col: The name of the column containing the unique ID.

    Returns:
        A tuple containing the created train and test DataFrames.
    """
    # Ensure output directories exist
    public_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)

    # Perform the split
    train_df, test_df = train_test_split(
        source_df, test_size=test_size, random_state=random_state
    )
    test_df_without_labels = test_df.drop(columns=[label_col])

    # Save the datasets
    train_df.to_csv(public_dir / "train.csv", index=False)
    test_df.to_csv(private_dir / "test.csv", index=False)
    test_df_without_labels.to_csv(public_dir / "test.csv", index=False)

    assert len(test_df_without_labels) == len(
        test_df
    ), f"Expected test_df_without_labels ({len(test_df_without_labels)}) == test_df ({len(test_df)})"
    assert len(train_df) + len(test_df) == len(
        source_df
    ), f"Expected train_df ({len(train_df)}) + test_df ({len(test_df)}) == source_df ({len(source_df)})"

    # Create and save a sample submission file
    submission_df = test_df.copy()[[id_col, label_col]]
    submission_df[label_col] = ""

    submission_df.to_csv(public_dir / "sample_submission.csv", index=False)
    assert len(submission_df) == len(
        test_df
    ), f"Expected submission_df ({len(submission_df)}) == test_df ({len(test_df)})"

    return train_df, test_df


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the data in raw into public and private datasets with appropriate test/train splits.
    Also creates a second, parallel split for validation purposes.
    """
    old_train = read_csv(raw / "train.csv")

    # ---- Original Data Split (for final test set) ----
    # This split creates the main train and test sets for the competition.
    # The outputs in `public` and `private` are left completely unchanged.
    train_for_val_split, _ = _split_and_save(
        source_df=old_train,
        test_size=0.1,
        random_state=0,
        public_dir=public,
        private_dir=private,
    )

    # ---- New Validation Data Split ----
    # This second split takes the training set created above and splits it *again*
    # to create a new, smaller training set and a validation set. The results are
    # saved to parallel `public_val` and `private_val` directories.

    # Define paths for the new validation split
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # The original test set size was 0.1 of the total data. The new train set
    # is 0.9 of the total. To make the new validation set (test_val) have
    # roughly the same number of samples as the original test set, we use a
    # test_size of (0.1 / 0.9) = 1/9.
    validation_test_size = 1 / 9

    _split_and_save(
        source_df=train_for_val_split,
        test_size=validation_test_size,
        random_state=0,  # Use same random_state for consistency
        public_dir=public_val,
        private_dir=private_val,
    )