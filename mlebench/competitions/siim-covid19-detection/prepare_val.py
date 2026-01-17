import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from mlebench.utils import read_csv


def _process_split(
    train_study_df: pd.DataFrame,
    test_study_df: pd.DataFrame,
    full_image_df: pd.DataFrame,
    raw_data_root: Path,
    output_public_path: Path,
    output_private_path: Path,
    dev_mode: bool,
):
    """
    Helper function to process a single data split and generate all required output files.

    Args:
        train_study_df: DataFrame of studies for the training set.
        test_study_df: DataFrame of studies for the test set.
        full_image_df: DataFrame of all images, to be filtered for this split.
        raw_data_root: Path to the original raw data.
        output_public_path: Path to the public output directory.
        output_private_path: Path to the private output directory.
        dev_mode: Boolean flag for development mode.
    """
    # Create output directories if they don't exist
    output_public_path.mkdir(parents=True, exist_ok=True)
    (output_public_path / "train").mkdir(exist_ok=True)
    (output_public_path / "test").mkdir(exist_ok=True)
    output_private_path.mkdir(parents=True, exist_ok=True)

    # Save the study-level train CSV
    train_study_df.to_csv(output_public_path / "train_study_level.csv", index=False)

    # Filter and save the image-level CSVs based on the study split
    split_train_image = full_image_df[
        (full_image_df["StudyInstanceUID"] + "_study").isin(train_study_df["id"])
    ]
    split_test_image = full_image_df[
        (full_image_df["StudyInstanceUID"] + "_study").isin(test_study_df["id"])
    ]
    split_train_image = split_train_image.sort_values(by="id")
    split_test_image = split_test_image.sort_values(by="id")
    if not dev_mode:
        assert len(split_train_image) + len(split_test_image) == len(
            full_image_df[
                (full_image_df["StudyInstanceUID"] + "_study").isin(
                    pd.concat([train_study_df["id"], test_study_df["id"]])
                )
            ]
        ), f"Image split mismatch"
    split_train_image.to_csv(output_public_path / "train_image_level.csv", index=False)

    # Copy image data for the split
    for study_id in tqdm(train_study_df["id"], desc=f"Copying train data to {output_public_path.name}"):
        study_id = study_id.replace("_study", "")
        shutil.copytree(raw_data_root / "train" / study_id, output_public_path / "train" / study_id, dirs_exist_ok=True)
    for study_id in tqdm(test_study_df["id"], desc=f"Copying test data to {output_public_path.name}"):
        study_id = study_id.replace("_study", "")
        shutil.copytree(raw_data_root / "train" / study_id, output_public_path / "test" / study_id, dirs_exist_ok=True)

    assert len(list(output_public_path.glob("train/*"))) == len(
        train_study_df
    ), f"Expected {len(train_study_df)} studies in {output_public_path.name}/train"
    assert len(list(output_public_path.glob("test/*"))) == len(
        test_study_df
    ), f"Expected {len(test_study_df)} studies in {output_public_path.name}/test"


    # Create gold answer submission for the test set
    rows = []
    for idx, row in test_study_df.iterrows():
        label = ["negative", "typical", "indeterminate", "atypical"][row[1:].argmax()]
        rows.append({"id": row["id"], "PredictionString": f"{label} 1 0 0 1 1"})
    for idx, row in split_test_image.iterrows():
        rows.append({"id": row["id"], "PredictionString": row["label"]})

    answers = pd.DataFrame(rows)
    assert len(answers) == len(test_study_df) + len(
        split_test_image
    ), f"Expected {len(test_study_df) + len(split_test_image)} answers"
    answers.to_csv(output_private_path / "test.csv", index=False)

    # Create sample submission for the test set
    rows = []
    for idx, row in test_study_df.iterrows():
        rows.append({"id": row["id"], "PredictionString": "negative 1 0 0 1 1"})
    for idx, row in split_test_image.iterrows():
        rows.append({"id": row["id"], "PredictionString": "none 1 0 0 1 1"})

    sample_submission = pd.DataFrame(rows)
    assert len(sample_submission) == len(test_study_df) + len(
        split_test_image
    ), f"Expected {len(test_study_df) + len(split_test_image)} sample answers"
    sample_submission.to_csv(output_public_path / "sample_submission.csv", index=False)


def prepare(raw: Path, public: Path, private: Path):
    """
    There are two tasks:
    - Image level: Object detection problem - detect the presence of pneumonia in the image using bounding boxes
    - Study level: Classification problem - classify the study into one of the four classes

    Images in train/ and test/ are stored in paths with the form {study}/{series}/{image}.

    Original train has 6,334 samples, and test "is of roughly the same scale as the training dataset".
    We'll split the original train into a new train/test split with 90/10 ratio.

    The split happens at the study level, with image level following accordingly.
    """
    DEV_MODE = False

    # Read the original full datasets
    train_study = read_csv(raw / "train_study_level.csv")
    train_image = read_csv(raw / "train_image_level.csv")

    if DEV_MODE:
        # randomly sample 200 rows for development
        train_study = train_study.sample(n=200, random_state=0)

    # --- First Split: Create the main train/test sets ---
    # This split creates the primary competition data, saved to `public` and `private`.
    new_train_study, new_test_study = train_test_split(train_study, test_size=0.1, random_state=0)
    new_train_study = new_train_study.sort_values(by="id").reset_index(drop=True)
    new_test_study = new_test_study.sort_values(by="id").reset_index(drop=True)

    _process_split(
        train_study_df=new_train_study,
        test_study_df=new_test_study,
        full_image_df=train_image,
        raw_data_root=raw,
        output_public_path=public,
        output_private_path=private,
        dev_mode=DEV_MODE,
    )

    # --- Second Split: Create the validation train/test sets ---
    # This split takes the *training set* from the first split (`new_train_study`)
    # and splits it again to create a validation set. The outputs are saved to
    # parallel `public_val` and `private_val` directories.
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # We use the exact same splitting parameters to maintain consistency.
    # The new test set (`test_val_study`) will be 10% of the `new_train_study`.
    train_val_study, test_val_study = train_test_split(new_train_study, test_size=0.1, random_state=0)
    train_val_study = train_val_study.sort_values(by="id").reset_index(drop=True)
    test_val_study = test_val_study.sort_values(by="id").reset_index(drop=True)

    _process_split(
        train_study_df=train_val_study,
        test_study_df=test_val_study,
        full_image_df=train_image, # The full image set is used for filtering
        raw_data_root=raw,
        output_public_path=public_val,
        output_private_path=private_val,
        dev_mode=DEV_MODE,
    )