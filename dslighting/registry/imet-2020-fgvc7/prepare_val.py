import shutil
from pathlib import Path

from sklearn.model_selection import train_test_split
from tqdm import tqdm

from mlebench.utils import read_csv


def _process_split(
    train_df,
    test_df,
    public_path: Path,
    private_path: Path,
    raw_images_path: Path,
    dev: bool,
):
    """
    Helper function to process a single data split (train/test).

    It handles the creation of directories, writing of CSVs (train, answers,
    sample_submission), and copying of image files. This ensures a consistent
    output structure for any given split.
    """
    # Create output directories
    public_path.mkdir(exist_ok=True, parents=True)
    private_path.mkdir(exist_ok=True, parents=True)
    (public_path / "test").mkdir(exist_ok=True)
    (public_path / "train").mkdir(exist_ok=True)

    # The test_df is the ground truth for the test set
    answers = test_df

    # Create a sample submission from the answers dataframe
    sample_submission_df = answers.copy()
    sample_submission_df["attribute_ids"] = "0 1 2"

    # Checks
    assert len(answers) == len(
        sample_submission_df
    ), "Answers and sample submission should have the same length"
    assert (
        sample_submission_df.columns.tolist() == answers.columns.tolist()
    ), "Sample submission and answers should have the same columns"

    # Write CSVs
    train_df.to_csv(public_path / "train.csv", index=False)
    answers.to_csv(private_path / "answers.csv", index=False)
    sample_submission_df.to_csv(public_path / "sample_submission.csv", index=False)

    # If in dev mode, reduce the number of images to copy for faster execution
    if dev:
        train_df_to_copy = train_df.head(int(len(train_df) * 0.1))
        answers_to_copy = answers.head(int(len(answers) * 0.1))
    else:
        train_df_to_copy = train_df
        answers_to_copy = answers

    # Copy train images
    for file_id in tqdm(
        train_df_to_copy["id"], desc=f"Copying train images to {public_path.name}"
    ):
        shutil.copyfile(
            src=raw_images_path / f"{file_id}.png",
            dst=public_path / "train" / f"{file_id}.png",
        )

    # Copy test images
    for file_id in tqdm(
        answers_to_copy["id"], desc=f"Copying test images to {public_path.name}"
    ):
        shutil.copyfile(
            src=raw_images_path / f"{file_id}.png",
            dst=public_path / "test" / f"{file_id}.png",
        )

    # File copying checks
    assert len(list(public_path.glob("train/*.png"))) == len(
        train_df_to_copy
    ), f"Train images in {public_path.name} should match dataframe"
    assert len(list(public_path.glob("test/*.png"))) == len(
        answers_to_copy
    ), f"Test images in {public_path.name} should match dataframe"


def prepare(raw: Path, public: Path, private: Path):

    dev = False

    # --- 1. Original Split: Create main train and test sets ---

    # Create train, test from train split
    old_train = read_csv(raw / "train.csv")
    # 25958/(142119+ 25958) = 0.15 original test split
    main_train, main_test = train_test_split(old_train, test_size=0.15, random_state=0)

    # Checks
    assert len(main_test) + len(main_train) == len(
        old_train
    ), "New train and test should have the same length as the old train"
    assert (
        main_test.columns.tolist() == old_train.columns.tolist()
    ), "Answers and old_train should have the same columns"
    assert (
        main_train.columns.tolist() == old_train.columns.tolist()
    ), "New train and old train should have the same columns"
    assert set(main_train["id"]).isdisjoint(
        set(main_test["id"])
    ), "New train and answers should have no overlap of rows"

    # Process and save the original split to `public` and `private` directories
    _process_split(
        train_df=main_train,
        test_df=main_test,
        public_path=public,
        private_path=private,
        raw_images_path=raw / "train",
        dev=dev,
    )

    # Copy over metadata file for the original split
    shutil.copyfile(src=raw / "labels.csv", dst=public / "labels.csv")

    # --- 2. New Validation Split: Create validation train and test sets ---

    # Define paths for the new validation split, parallel to the original ones
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # The test_size for the second split is calculated to yield a validation set
    # of approximately the same size as the original test set.
    # Original test set size = 0.15 * N
    # Original train set size = 0.85 * N
    # We want: test_size_val * (0.85 * N) ~= 0.15 * N
    # So, test_size_val ~= 0.15 / 0.85
    test_size_for_val_split = 0.15 / (1 - 0.15)

    # Split the main_train set again to create a smaller training set and a validation set.
    # We use the same random_state to ensure this split is also deterministic.
    train_val, test_val = train_test_split(
        main_train, test_size=test_size_for_val_split, random_state=0
    )

    # Process and save the validation split to `public_val` and `private_val`.
    # The filenames and structure will be identical to the original split, but
    # will contain the new, smaller training set and the validation set.
    _process_split(
        train_df=train_val,
        test_df=test_val,
        public_path=public_val,
        private_path=private_val,
        raw_images_path=raw / "train",
        dev=dev,
    )

    # Copy over metadata file for the validation split
    shutil.copyfile(src=raw / "labels.csv", dst=public_val / "labels.csv")