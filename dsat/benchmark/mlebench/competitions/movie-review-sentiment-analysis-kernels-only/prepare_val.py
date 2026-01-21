import shutil
from pathlib import Path

from pandas import DataFrame, read_csv
from sklearn.model_selection import train_test_split

from mlebench.utils import extract


def prepare(raw: Path, public: Path, private: Path):
    """
    Prepares the dataset by performing two sequential splits.
    1. Splits the raw data into a main train/test set for the `public` and
       `private` directories.
    2. Splits the main training set again to create a smaller train/validation
       set for the `public_val` and `private_val` directories.
    """

    def _split_and_save(
        data_to_split: DataFrame,
        test_ratio: float,
        public_dir: Path,
        private_dir: Path,
        random_state: int,
    ) -> DataFrame:
        """
        Helper function to perform a data split, save files to specified
        directories, and return the resulting training set for a potential
        subsequent split.
        """
        # Ensure output directories exist
        public_dir.mkdir(parents=True, exist_ok=True)
        private_dir.mkdir(parents=True, exist_ok=True)

        # Create train and test splits from the provided dataframe
        new_train, answers = train_test_split(
            data_to_split, test_size=test_ratio, random_state=random_state
        )

        # Create public test set (unlabeled)
        new_test = answers.copy()
        new_test = new_test.drop("Sentiment", axis="columns")

        # Create sample submission
        sample_submission = answers[["PhraseId", "Sentiment"]].copy()
        sample_submission["Sentiment"] = 2

        # Checks
        assert new_train["PhraseId"].is_unique, f"PhraseId in new_train ({public_dir.name}) should be unique"
        assert new_test["PhraseId"].is_unique, f"PhraseId in new_test ({public_dir.name}) should be unique"
        assert set(new_train["PhraseId"]).isdisjoint(
            set(new_test["PhraseId"])
        ), f"PhraseId in new_train and new_test ({public_dir.name}) should be disjoint"
        assert (
            new_train.shape[0] + new_test.shape[0] == data_to_split.shape[0]
        ), "New train and new test should have the same number of rows as the input data"
        assert (
            new_train.columns.tolist() == data_to_split.columns.tolist()
        ), "New train and input data should have the same columns"
        assert new_test.columns.tolist() == [
            "PhraseId",
            "SentenceId",
            "Phrase",
        ], "new_test should have columns ['PhraseId', 'SentenceId', 'Phrase']"

        # Write CSVs to their respective directories
        answers.to_csv(private_dir / "answers.csv", index=False)
        new_train.to_csv(public_dir / "train.tsv", index=False, sep="\t")
        new_test.to_csv(public_dir / "test.tsv", index=False, sep="\t")
        sample_submission.to_csv(public_dir / "sampleSubmission.csv", index=False)

        # Zip files
        shutil.make_archive(str(public_dir / "train.tsv"), "zip", public_dir, "train.tsv")
        shutil.make_archive(str(public_dir / "test.tsv"), "zip", public_dir, "test.tsv")

        # Delete unzipped files
        (public_dir / "train.tsv").unlink()
        (public_dir / "test.tsv").unlink()

        return new_train

    # --- Main script execution starts here ---

    # Extract the raw data file
    extract(raw / "train.tsv.zip", raw)
    old_train = read_csv(raw / "train.tsv", sep="\t")

    # Define the test ratio for the first split
    test_ratio_1 = 0.3  # 66293/(156061+66293) = 0.3

    # --- First Split: Create the original public/private sets ---
    # This call produces the original, unmodified competition output.
    # The resulting training set is captured for the second split.
    train_for_val_split = _split_and_save(
        data_to_split=old_train,
        test_ratio=test_ratio_1,
        public_dir=public,
        private_dir=private,
        random_state=0,
    )

    # --- Second Split: Create the new validation sets ---
    # Define the new parallel directories for the validation split
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Calculate the test ratio for the second split. This ensures the new
    # validation set (`test_val`) is the same size as the original test set.
    # test_ratio_2 = (size of original test set) / (size of new training set)
    #              = (total * test_ratio_1) / (total * (1 - test_ratio_1))
    test_ratio_2 = test_ratio_1 / (1 - test_ratio_1)

    # Perform the second split on the training data from the first split
    _split_and_save(
        data_to_split=train_for_val_split,
        test_ratio=test_ratio_2,
        public_dir=public_val,
        private_dir=private_val,
        random_state=0,
    )