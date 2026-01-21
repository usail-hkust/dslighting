import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from pandas import DataFrame, read_csv
from PIL import Image
from sklearn.model_selection import train_test_split

from mlebench.utils import extract


def _generate_split_artifacts(
    train_fpaths: list[Path],
    test_fpaths: list[Path],
    source_data_dir: Path,
    public_dest: Path,
    private_dest: Path,
) -> None:
    """
    Helper function to generate all required files for a given train/test split.

    This function copies the necessary image files, creates the ground-truth
    `answers.csv` for the test set, and a `sampleSubmission.csv` for the public.
    """
    public_dest.mkdir(exist_ok=True, parents=True)
    private_dest.mkdir(exist_ok=True, parents=True)

    test_img_names = {fpath.name for fpath in test_fpaths}

    # Create public train/test directories and copy images
    (public_dest / "train").mkdir(exist_ok=True)
    (public_dest / "test").mkdir(exist_ok=True)

    for fpath in train_fpaths:
        shutil.copy(fpath, public_dest / "train" / fpath.name)

    for fpath in test_fpaths:
        shutil.copy(fpath, public_dest / "test" / fpath.name)

    # Prepare ground-truth labels for the test set
    temp_private_cleaned_dir = private_dest / "train_cleaned"
    temp_private_cleaned_dir.mkdir(exist_ok=True)

    source_cleaned_dir = source_data_dir / "train_cleaned"
    for fpath in source_cleaned_dir.glob("*.png"):
        if fpath.name in test_img_names:
            shutil.copy(fpath, temp_private_cleaned_dir / fpath.name)

    # Write `answers.csv` for the test set
    dfs = []
    for fpath in sorted(temp_private_cleaned_dir.glob("*.png")):
        df = to_df(fpath)
        dfs.append(df)

    answers = DataFrame(pd.concat(dfs))
    answers.to_csv(private_dest / "answers.csv", index=False)

    shutil.rmtree(temp_private_cleaned_dir)

    # Write `sampleSubmission.csv`
    sample_submission = answers.copy()
    sample_submission["value"] = 1
    sample_submission.to_csv(public_dest / "sampleSubmission.csv", index=False)

    # Sanity checks
    assert len(list((public_dest / "train").glob("*.png"))) == len(train_fpaths), (
        f"Expected the number of images in `{public_dest}/train` to be "
        f"{len(train_fpaths)}, but got "
        f"{len(list((public_dest / 'train').glob('*.png')))}."
    )

    assert len(list((public_dest / "test").glob("*.png"))) == len(test_fpaths), (
        f"Expected {len(test_fpaths)} in the `{public_dest}/test` directory, but got "
        f"{len(list((public_dest / 'test').glob('*.png')))}."
    )

    assert read_csv(private_dest / "answers.csv").drop_duplicates().shape[0] == len(
        read_csv(private_dest / "answers.csv")
    ), (
        f"Expected `{private_dest}/answers.csv` to have unique rows, but got "
        f"{read_csv(private_dest / 'answers.csv').drop_duplicates().shape[0]} unique rows and "
        f"{len(read_csv(private_dest / 'answers.csv'))} rows in total."
    )

    assert len(read_csv(private_dest / "answers.csv")) == len(
        read_csv(public_dest / "sampleSubmission.csv")
    ), (
        f"Expected `answers.csv` and `sampleSubmission.csv` to have the same number of rows, but "
        f"got {len(read_csv(private_dest / 'answers.csv'))} rows in `answers.csv` and "
        f"{len(read_csv(public_dest / 'sampleSubmission.csv'))} rows in `sampleSubmission.csv`."
    )

    assert "id" in read_csv(private_dest / "answers.csv").columns, (
        f"Expected `answers.csv` to have an 'id' column, but got "
        f"{read_csv(private_dest / 'answers.csv').columns}."
    )

    assert "value" in read_csv(private_dest / "answers.csv").columns, (
        f"Expected `answers.csv` to have a 'value' column, but got "
        f"{read_csv(private_dest / 'answers.csv').columns}."
    )

    assert "id" in read_csv(public_dest / "sampleSubmission.csv").columns, (
        f"Expected `sampleSubmission.csv` to have an 'id' column, but got "
        f"{read_csv(public_dest / 'sampleSubmission.csv').columns}."
    )

    assert "value" in read_csv(public_dest / "sampleSubmission.csv").columns, (
        f"Expected `sampleSubmission.csv` to have a 'value' column, but got "
        f"{read_csv(public_dest / 'sampleSubmission.csv').columns}."
    )


def prepare(raw: Path, public: Path, private: Path) -> None:
    # Define paths for the new validation split
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Use a temporary directory to extract raw data to avoid side-effects
    temp_source_dir = public.parent / "temp_data_source"
    if temp_source_dir.exists():
        shutil.rmtree(temp_source_dir)
    temp_source_dir.mkdir(parents=True)

    # Extract all necessary data once
    extract(raw / "train.zip", temp_source_dir)
    extract(raw / "train_cleaned.zip", temp_source_dir)
    all_img_fpaths = sorted((temp_source_dir / "train").glob("*.png"))

    # --- First Split: The Original Train/Test Split ---
    # We set new test ratio to 0.2 to keep it number of train samples at same OOM while having enough samples for new test
    orig_train_fpaths, orig_test_fpaths = train_test_split(
        all_img_fpaths,
        test_size=0.2,
        random_state=0,
    )
    # Generate artifacts for the original public/private directories
    _generate_split_artifacts(orig_train_fpaths, orig_test_fpaths, temp_source_dir, public, private)

    # --- Second Split: Create Train/Validation Split from the Original Train Set ---
    # To keep the new validation set size similar to the original test set size,
    # we use test_size=0.25 (since 0.25 * 0.8 = 0.2).
    new_train_fpaths, val_fpaths = train_test_split(
        orig_train_fpaths, # Split the original training data again
        test_size=0.25,
        random_state=0,
    )
    # Generate artifacts for the new validation directories (public_val/private_val)
    _generate_split_artifacts(new_train_fpaths, val_fpaths, temp_source_dir, public_val, private_val)

    # Clean up the temporary source directory
    shutil.rmtree(temp_source_dir)


def to_df(img: Path) -> DataFrame:
    """Converts an image to a DataFrame, where each row corresponds to a pixel."""

    image = Image.open(img).convert("L")
    image_array = np.array(image) / 255.0

    rows, cols = image_array.shape
    data = {"id": [], "value": []}

    for row in range(rows):
        for col in range(cols):
            pixel_id = f"{img.stem}_{row+1}_{col+1}"
            pixel_value = image_array[row, col]
            data["id"].append(pixel_id)
            data["value"].append(pixel_value)

    df = DataFrame(data)

    assert (
        len(df) == rows * cols
    ), f"Expected the DataFrame to have {rows * cols} rows, but got {len(df)} rows."

    return DataFrame(data)