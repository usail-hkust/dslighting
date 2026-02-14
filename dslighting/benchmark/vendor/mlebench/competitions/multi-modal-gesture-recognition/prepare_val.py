import random
import shutil
from pathlib import Path

import pandas as pd


def _create_split(
    source_df: pd.DataFrame,
    test_tar_name: str,
    train_tar_names: list[str],
    raw_dir: Path,
    public_dir: Path,
    private_dir: Path,
) -> pd.DataFrame:
    """
    Helper function to perform a data split based on specified tar files.

    It unpacks a given test tarball to identify test sample IDs, splits the
    source dataframe into train/test sets, creates all necessary public and private
    CSV files, copies the relevant data tarballs, and returns the newly created
    training dataframe for potential subsequent splits.
    """
    # Unpack the test file to get test IDs
    # The ID is the last 4 digits of the sample filename (e.g., "0300" from "Sample00300.zip")
    test_data_dir_name = test_tar_name.replace(".tar.gz", "")
    shutil.unpack_archive(raw_dir / test_tar_name, raw_dir / test_data_dir_name)
    test_ids = sorted([fp.stem[-4:] for fp in (raw_dir / test_data_dir_name).glob("*.zip")])

    # Create the new training dataframe for this split
    new_training_df = source_df[~source_df["Id"].isin(test_ids)]
    new_training_df.to_csv(public_dir / "training.csv", index=False)
    assert len(new_training_df) == len(source_df) - len(test_ids)

    # Make private answers
    answers_df = source_df[source_df["Id"].isin(test_ids)]
    answers_df.to_csv(private_dir / "test.csv", index=False)
    assert len(answers_df) == len(test_ids)

    # Make new public test.csv (IDs only)
    test_df = pd.DataFrame({"Id": test_ids})
    test_df.to_csv(public_dir / "test.csv", index=False)
    assert len(test_df) == len(test_ids)

    # Make new public randomPredictions.csv
    # predictions are random shufflings of numbers 1-20 (no repeats)
    random.seed(0)
    preds = []
    for _ in range(len(test_ids)):
        pred = " ".join(str(x) for x in random.sample(range(1, 21), 20))
        preds.append(pred)
    random_predictions_df = pd.DataFrame({"Id": test_ids, "Sequence": preds})
    random_predictions_df.to_csv(public_dir / "randomPredictions.csv", index=False)
    assert len(random_predictions_df) == len(test_ids)

    # Copy over the designated test set tarball
    shutil.copyfile(src=raw_dir / test_tar_name, dst=public_dir / "test.tar.gz")

    # Copy over the designated training tarballs for this split
    for file in train_tar_names:
        shutil.copyfile(src=raw_dir / file, dst=public_dir / file)

    return new_training_df


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the data in raw into public and private datasets with appropriate test/train splits.

    Raw dataset has:
    - Train: training1, training2, training3, training4
    - Val: validation1, validation2, validation3 (no labels)
    - Test: (not available)

    New prepared dataset has:
    - Train: training1, training2, training3
    - Val: validation1, validation2, validation3 (no labels)
    - Test: training4 (renamed to `test.tar.gz`)

    Furthermore,
    - We modify the `training.csv` to remove training4 samples
    - We modify the `test.csv` and `randomPredictions.csv` to include only training4 IDs

    No other changes. We copy over the remaining files (devel01-40.7z, valid_all_files_combined.7z, sample_code_mmrgc.zip) as-is.
    """
    # --- Setup new directories for the validation split ---
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"
    public_val.mkdir(exist_ok=True)
    private_val.mkdir(exist_ok=True)

    # Load the complete training data manifest
    full_training_df = pd.read_csv(raw / "training.csv", dtype={"Id": str, "Sequence": str})

    # --- 1. Create the original public/private split ---
    # This split is identical to the original script's behavior.
    # Train set: training1, 2, 3. Test set: training4.
    original_train_tars = ["training1.tar.gz", "training2.tar.gz", "training3.tar.gz"]
    original_test_tar = "training4.tar.gz"

    train_df_for_val_split = _create_split(
        source_df=full_training_df,
        test_tar_name=original_test_tar,
        train_tar_names=original_train_tars,
        raw_dir=raw,
        public_dir=public,
        private_dir=private,
    )

    # Copy over validation and other miscellaneous files to the 'public' directory
    files_to_copy = [
        "validation1.tar.gz",
        "validation2.tar.gz",
        "validation3.tar.gz",
        "devel01-40.7z",
        "valid_all_files_combined.7z",
        "sample_code_mmrgc.zip",
    ]
    for file in files_to_copy:
        shutil.copyfile(src=raw / file, dst=public / file)

    # --- 2. Create the new public_val/private_val split ---
    # This second split uses the training data from the first split as its source.
    # New train set: training1, 2. New test (validation) set: training3.
    val_train_tars = ["training1.tar.gz", "training2.tar.gz"]
    val_test_tar = "training3.tar.gz"

    _create_split(
        source_df=train_df_for_val_split,
        test_tar_name=val_test_tar,
        train_tar_names=val_train_tars,
        raw_dir=raw,
        public_dir=public_val,
        private_dir=private_val,
    )

    # Copy over validation and other files to 'public_val' to mirror the 'public' structure
    for file in files_to_copy:
        shutil.copyfile(src=raw / file, dst=public_val / file)