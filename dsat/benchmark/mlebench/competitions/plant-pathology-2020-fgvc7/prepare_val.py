import shutil
from pathlib import Path

from sklearn.model_selection import train_test_split
from tqdm.auto import tqdm

from mlebench.utils import read_csv


def prepare(raw: Path, public: Path, private: Path) -> None:
    # --- Expected Column Definitions (used for both splits) ---
    expected_train_columns = ["image_id", "healthy", "multiple_diseases", "rust", "scab"]
    expected_test_columns = ["image_id"]
    expected_answers_columns = expected_train_columns
    expected_sample_submission_columns = expected_train_columns

    # =================================================================
    # == STAGE 1: Create the original train/test split.              ==
    # == This section is preserved to ensure the original `public`   ==
    # == and `private` directories are identical to the original script. ==
    # =================================================================

    old_train = read_csv(raw / "train.csv")
    new_train, answers = train_test_split(old_train, test_size=0.1, random_state=0)

    assert set(new_train.columns) == set(
        expected_train_columns
    ), f"Expected `new_train` to have columns {expected_train_columns} but got {new_train.columns}"

    assert set(answers.columns) == set(
        expected_answers_columns
    ), f"Expected `answers` to have columns {expected_answers_columns} but got {answers.columns}"

    new_train_image_ids = new_train["image_id"].unique()
    new_test_image_ids = answers["image_id"].unique()
    to_new_image_id = {
        **{old_id: f"Train_{i}" for i, old_id in enumerate(new_train_image_ids)},
        **{old_id: f"Test_{i}" for i, old_id in enumerate(new_test_image_ids)},
    }

    # IMPORTANT: The `new_train` DataFrame is modified here and will be used
    # as the input for the second split. We make a copy to preserve it
    # before its image_ids are changed in-place for the first split's output.
    train_for_val_split = new_train.copy()
    new_train["image_id"] = new_train["image_id"].replace(to_new_image_id)
    answers["image_id"] = answers["image_id"].replace(to_new_image_id)

    new_test = answers[["image_id"]].copy()

    assert set(new_test.columns) == set(
        expected_test_columns
    ), f"Expected `new_test` to have columns {expected_test_columns} but got {new_test.columns}"

    sample_submission = answers[["image_id"]].copy()
    sample_submission[["healthy", "multiple_diseases", "rust", "scab"]] = 0.25

    assert set(sample_submission.columns) == set(
        expected_sample_submission_columns
    ), f"Expected `sample_submission` to have columns {expected_sample_submission_columns} but got {sample_submission.columns}"

    private.mkdir(exist_ok=True, parents=True)
    public.mkdir(exist_ok=True, parents=True)
    (public / "images").mkdir(exist_ok=True)

    # Note: This loop copies ALL images defined in the original raw train set.
    for old_image_id in tqdm(old_train["image_id"], desc="Copying over train & test images"):
        assert old_image_id.startswith(
            "Train_"
        ), f"Expected train image id `{old_image_id}` to start with `Train_`."

        new_image_id = to_new_image_id.get(old_image_id, old_image_id)

        assert (
            raw / "images" / f"{old_image_id}.jpg"
        ).exists(), f"Image `{old_image_id}.jpg` does not exist in `{raw / 'images'}`."

        shutil.copyfile(
            src=raw / "images" / f"{old_image_id}.jpg",
            dst=public / "images" / f"{new_image_id}.jpg",
        )

    answers.to_csv(private / "test.csv", index=False)
    sample_submission.to_csv(public / "sample_submission.csv", index=False)
    new_test.to_csv(public / "test.csv", index=False)
    new_train.to_csv(public / "train.csv", index=False)

    # =================================================================
    # == STAGE 2: Create the new validation split.                   ==
    # == This section splits the `new_train` set from STAGE 1 to     ==
    # == create a smaller training set and a validation set.         ==
    # =================================================================
    print("\nStarting second split to create validation set...")

    # Define paths for the new validation set directories
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # To get a validation test set of roughly the same size as the original
    # test set (10% of total), we must take 1/9th of the training set (90% of total).
    # (0.1 * total) / (0.9 * total) = 1/9
    val_test_size = 1 / 9.0

    # Perform the second split on the original training data
    train_val, answers_val = train_test_split(
        train_for_val_split, test_size=val_test_size, random_state=0
    )

    # --- Replicate the ID renaming and file creation logic for the new split ---

    train_val_image_ids = train_val["image_id"].unique()
    test_val_image_ids = answers_val["image_id"].unique()
    to_new_val_image_id = {
        **{old_id: f"Train_{i}" for i, old_id in enumerate(train_val_image_ids)},
        **{old_id: f"Test_{i}" for i, old_id in enumerate(test_val_image_ids)},
    }

    # The original image IDs from this split are keys in `to_new_image_id`.
    # We need to map them to find the source file in `public/images`.
    # e.g., raw 'Train_123' -> 1st split 'Train_45' -> 2nd split 'Test_6'
    id_mapper_raw_to_val = {
        raw_id: val_id
        for raw_id, val_id in to_new_val_image_id.items()
    }
    
    # Get the intermediate filenames from the first split's mapping
    source_to_dest_val_map = {
        to_new_image_id[raw_id]: val_id
        for raw_id, val_id in id_mapper_raw_to_val.items()
    }


    train_val["image_id"] = train_val["image_id"].replace(to_new_val_image_id)
    answers_val["image_id"] = answers_val["image_id"].replace(to_new_val_image_id)

    test_val = answers_val[["image_id"]].copy()
    sample_submission_val = answers_val[["image_id"]].copy()
    sample_submission_val[["healthy", "multiple_diseases", "rust", "scab"]] = 0.25

    # Create the new directories
    private_val.mkdir(exist_ok=True, parents=True)
    public_val.mkdir(exist_ok=True, parents=True)
    (public_val / "images").mkdir(exist_ok=True)

    # Copy images for the validation split. The source is the `public/images`
    # directory created in the first stage.
    for source_filename_stem, dest_filename_stem in tqdm(
        source_to_dest_val_map.items(), desc="Copying over validation images"
    ):
        shutil.copyfile(
            src=public / "images" / f"{source_filename_stem}.jpg",
            dst=public_val / "images" / f"{dest_filename_stem}.jpg",
        )

    # Save all files for the validation split into the new directories
    answers_val.to_csv(private_val / "test.csv", index=False)
    sample_submission_val.to_csv(public_val / "sample_submission.csv", index=False)
    test_val.to_csv(public_val / "test.csv", index=False)
    train_val.to_csv(public_val / "train.csv", index=False)

    print("\nValidation set created successfully.")