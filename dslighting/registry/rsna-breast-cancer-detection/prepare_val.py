import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm.auto import tqdm

from mlebench.utils import read_csv

# columns in train.csv
train_columns = [
    "site_id",
    "patient_id",
    "image_id",
    "laterality",
    "view",
    "age",
    "cancer",
    "biopsy",
    "invasive",
    "BIRADS",
    "implant",
    "density",
    "machine_id",
    "difficult_negative_case",
]
# columns in test.csv
test_columns = [
    "site_id",
    "patient_id",
    "image_id",
    "laterality",
    "view",
    "age",
    "implant",
    "machine_id",
    "prediction_id",
]

# columns in answers/submission
submission_columns = ["prediction_id", "cancer"]


DEV = False


def _process_split(
    source_df: pd.DataFrame,
    train_pids: set,
    test_pids: set,
    public_path: Path,
    private_path: Path,
    raw_images_path: Path,
):
    """
    Processes a data split, creating all required files and directories.

    Args:
        source_df: The DataFrame to split (e.g., the full dataset or a training subset).
        train_pids: A set of patient IDs for the training set.
        test_pids: A set of patient IDs for the test set.
        public_path: The public output directory.
        private_path: The private output directory.
        raw_images_path: Path to the original raw images.
    """
    public_path.mkdir(exist_ok=True, parents=True)
    private_path.mkdir(exist_ok=True, parents=True)

    # Create train and test dataframes from the source data
    new_train = source_df[source_df["patient_id"].isin(train_pids)].copy()
    # dont index the `prediction_id` (last col) since its not in train and we need to build it
    # index also the `cancer` column, which we'll drop later for the without_labels version
    answers = source_df[source_df["patient_id"].isin(test_pids)][
        test_columns[:-1] + ["cancer"]
    ].copy()

    new_train.to_csv(public_path / "train.csv", index=False)

    answers["prediction_id"] = answers["patient_id"].astype(str) + "_" + answers["laterality"]
    new_test_without_labels = answers.drop(columns=["cancer"])
    new_test_without_labels.to_csv(public_path / "test.csv", index=False)

    # merge multiple prediction_ids for the same patient into one for sample_submission and private test
    answers = answers[submission_columns].copy()
    # just take the first label for each prediction id -- the rest will be identical duplicates
    answers = answers.groupby("prediction_id").first().reset_index()
    answers.to_csv(private_path / "answers.csv", index=False)

    sample_submission = answers.copy()
    sample_submission["cancer"] = new_train.cancer.mean()  # mean cancer rate in train set
    sample_submission.to_csv(public_path / "sample_submission.csv", index=False)

    assert len(sample_submission) == len(
        answers
    ), "sample_submission and test.csv should have the same number of rows"
    assert len(new_test_without_labels) + len(new_train) == len(
        source_df
    ), "The sum of the rows in new_test_without_labels and new_train should be equal to the number of rows in the source_df"
    # because of the merging
    assert len(answers) != len(
        new_test_without_labels
    ), "new_test and new_test_without_labels should have different number of rows"

    assert (
        answers.columns.tolist() == submission_columns
    ), f"answers should have columns {submission_columns}"
    assert (
        sample_submission.columns.tolist() == submission_columns
    ), f"sample_submission should have columns {submission_columns}"

    assert (
        new_train.columns.tolist() == source_df.columns.tolist()
    ), f"new_train should have columns {source_df.columns.tolist()}, got {new_train.columns.tolist()}"
    assert (
        new_test_without_labels.columns.tolist() == test_columns
    ), f"new_test_without_labels should have columns {test_columns}, got {new_test_without_labels.columns.tolist()}"

    assert set(new_test_without_labels["patient_id"]).isdisjoint(
        set(new_train["patient_id"])
    ), "new_test_without_labels and new_train should have disjoint patient_ids"

    # finally, split the images
    (public_path / "train_images").mkdir(exist_ok=True)
    for patient_id in tqdm(train_pids, desc=f"Copying train images to {public_path.name}"):
        patient_id_str = str(patient_id)
        patient_dir = public_path / "train_images" / patient_id_str
        patient_dir.mkdir(exist_ok=True)
        image_ids = new_train[new_train["patient_id"] == patient_id]["image_id"].to_list()
        for image_id in image_ids:
            shutil.copy(raw_images_path / patient_id_str / f"{image_id}.dcm", patient_dir)

    (public_path / "test_images").mkdir(exist_ok=True)
    for patient_id in tqdm(test_pids, desc=f"Copying test images to {public_path.name}"):
        patient_id_str = str(patient_id)
        patient_dir = public_path / "test_images" / patient_id_str
        patient_dir.mkdir(exist_ok=True)
        image_ids = new_test_without_labels[new_test_without_labels["patient_id"] == patient_id][
            "image_id"
        ].to_list()
        for image_id in image_ids:
            shutil.copy(raw_images_path / patient_id_str / f"{image_id}.dcm", patient_dir)

    # final checks
    assert len(list((public_path / "train_images").rglob("*.dcm"))) == len(
        new_train
    ), "Number of images in train_images should be equal to the number of rows in new_train"
    assert len(list((public_path / "test_images").rglob("*.dcm"))) == len(
        new_test_without_labels
    ), "Number of images in test_images should be equal to the number of rows in new_test_without_labels"


def prepare(raw: Path, public: Path, private: Path):

    old_train = read_csv(raw / "train.csv")
    # work on 5k samples for now, instead of 54k
    if DEV:
        old_train = old_train.sample(5000, random_state=42)

    # "You can expect roughly 8,000 patients" in the test set
    # so, split on patients. There are 11913 patients in train set
    # Original ratio is 8000/ (8000 + 11913) ~ 0.4
    # We use 0.1 to avoid taking too many samples out of train
    all_patient_ids = old_train["patient_id"].unique()
    train_patients_orig, test_patients_orig = train_test_split(
        all_patient_ids, test_size=0.1, random_state=42
    )

    # --- 1. Create the original public/private split ---
    # This call generates the primary competition data. Its outputs must not be changed.
    _process_split(
        source_df=old_train,
        train_pids=set(train_patients_orig),
        test_pids=set(test_patients_orig),
        public_path=public,
        private_path=private,
        raw_images_path=raw / "train_images",
    )

    # --- 2. Create the new validation split ---
    # Define new parallel directories for the validation set.
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Split the *original training patients* again to create a new train/validation set.
    # We use the same test_size and random_state to replicate the splitting methodology.
    train_val_patients, test_val_patients = train_test_split(
        train_patients_orig, test_size=0.1, random_state=42
    )

    # The source data for this second split is the original training data.
    original_train_df = old_train[old_train["patient_id"].isin(train_patients_orig)].copy()

    # This call generates the new validation data in public_val/private_val.
    _process_split(
        source_df=original_train_df,
        train_pids=set(train_val_patients),
        test_pids=set(test_val_patients),
        public_path=public_val,
        private_path=private_val,
        raw_images_path=raw / "train_images",
    )