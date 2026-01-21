import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm.auto import tqdm

from mlebench.utils import read_csv


def verify_directory_sync(df: pd.DataFrame, expected_dir: Path, unexpected_dir: Path):
    """
    Checks that the dataframe contents match the directory structure.
    """
    for _, row in tqdm(
        df.iterrows(), desc=f"Verifying directory sync for {expected_dir.name}", total=len(df)
    ):
        case_day_path = expected_dir / row["case"] / f"{row['case']}_{row['day']}"
        assert (
            case_day_path.exists()
        ), f"Directory {case_day_path} does not exist but is listed in the dataframe."
        non_existent_path = unexpected_dir / row["case"] / f"{row['case']}_{row['day']}"
        assert (
            not non_existent_path.exists()
        ), f"Directory {non_existent_path} exists but is not listed in the dataframe."


def _create_split(
    input_df: pd.DataFrame,
    raw_images_dir: Path,
    output_public_path: Path,
    output_private_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Helper function to perform a train/test split on a dataframe, move image files accordingly,
    and save the resulting CSVs and submission files.

    Args:
        input_df: The dataframe to be split.
        raw_images_dir: The source directory of all raw image data.
        output_public_path: The destination directory for public files (e.g., public/ or public_val/).
        output_private_path: The destination directory for private files (e.g., private/ or private_val/).

    Returns:
        A tuple containing the created training and testing dataframes.
    """
    # ----------------------- Splitting
    # Extract case and day from 'id'
    df_to_split = input_df.copy()
    df_to_split["case"] = df_to_split["id"].apply(lambda x: x.split("_")[0])
    df_to_split["day"] = df_to_split["id"].apply(lambda x: x.split("_")[1])
    df_to_split["slice"] = df_to_split["id"].apply(lambda x: x.split("_")[-1])

    # Split cases into train and test
    unique_cases = df_to_split["case"].unique()
    train_cases, test_cases = train_test_split(unique_cases, test_size=0.1, random_state=42)

    # Initially assign entire cases to train or test set
    df_to_split["set"] = df_to_split["case"].apply(lambda x: "test" if x in test_cases else "train")

    # Then mark some days from train to be test, to match competition test description
    days_df = df_to_split[df_to_split["set"] == "train"].groupby("case")["day"].apply(set).reset_index()
    for _, row in days_df.iterrows():
        # if theres more than 4 days, we will move any days past the 4th to the test set
        days = row["day"]
        if len(days) > 4:
            days = sorted(days, key=lambda x: int(x[len("day") :]))
            days_to_move = days[4:]
            # change their set to "test"
            df_to_split.loc[
                df_to_split["case"].eq(row["case"]) & df_to_split["day"].isin(days_to_move), "set"
            ] = "test"

    # ----------------------- Move the files to the correct new locations
    new_train_dir = output_public_path / "train"
    new_test_dir = output_public_path / "test"

    # Create new directories if they don't exist
    new_train_dir.mkdir(parents=True, exist_ok=True)
    new_test_dir.mkdir(parents=True, exist_ok=True)
    output_private_path.mkdir(parents=True, exist_ok=True)

    # Move directories based on the set assignment
    for case in tqdm(unique_cases, desc=f"Splitting by case for {output_public_path.name}"):
        original_path = raw_images_dir / case
        if case in train_cases:
            new_path = new_train_dir / case
        else:
            new_path = new_test_dir / case
        shutil.copytree(original_path, new_path, dirs_exist_ok=True)

    # Move specific days from public/train/ to public/test/ for marked case-days
    for _, row in tqdm(
        df_to_split.iterrows(),
        desc=f"Handling day-based splits for {output_public_path.name}",
        total=len(df_to_split),
    ):
        if row["set"] == "test":
            source_day_path = new_train_dir / row["case"] / f"{row['case']}_{row['day']}"
            target_day_path = new_test_dir / row["case"] / f"{row['case']}_{row['day']}"
            if source_day_path.exists():
                target_day_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(source_day_path.as_posix(), target_day_path.as_posix())

    # ------------------------ Saving splits
    new_train = df_to_split[df_to_split["set"] == "train"].copy()
    new_test = df_to_split[df_to_split["set"] == "test"].copy()
    # some asserts before we drop columns
    verify_directory_sync(new_train, expected_dir=new_train_dir, unexpected_dir=new_test_dir)
    verify_directory_sync(new_test, expected_dir=new_test_dir, unexpected_dir=new_train_dir)

    # get image height and image width for the test set, since this is needed for the metric
    for _, row in tqdm(
        new_test.iterrows(),
        desc=f"Getting image dimensions for {output_public_path.name} test set",
        total=len(new_test),
    ):
        case, day, day_slice = row["case"], row["day"], row["slice"]
        image_paths = list(
            (raw_images_dir / case / f"{case}_{day}" / "scans").glob(f"slice_{day_slice}_*.png")
        )
        assert len(image_paths) == 1, f"Expected 1 image, found {len(image_paths)}"
        image_path = image_paths[0]
        width, height = (int(length) for length in image_path.stem.split("_")[2:4])
        new_test.loc[row.name, "image_width"] = width
        new_test.loc[row.name, "image_height"] = height

    # dont need these anymore, and werent part of the original data
    new_train.drop(columns=["set", "case", "day", "slice"], inplace=True)
    new_test.drop(columns=["set", "case", "day", "slice"], inplace=True)

    # create sample submission
    sample_submission = new_test.copy()
    sample_submission["segmentation"] = "1 1 5 2"
    sample_submission.drop(columns=["image_height", "image_width"], inplace=True)
    sample_submission.rename(columns={"segmentation": "predicted"}, inplace=True)
    sample_submission.to_csv(output_public_path / "sample_submission.csv", index=False, na_rep="")

    # create private files
    new_test.rename(columns={"segmentation": "predicted"}, inplace=True)
    new_test.to_csv(output_private_path / "test.csv", index=False, na_rep="")

    # create public files
    new_train.to_csv(output_public_path / "train.csv", index=False, na_rep="")
    new_test_without_labels = new_test.drop(columns=["predicted", "image_width", "image_height"])
    new_test_without_labels.to_csv(output_public_path / "test.csv", index=False, na_rep="")

    # ------------------------ checks
    assert new_test_without_labels.shape[1] == 2, "Public test should have 2 columns."
    assert new_train.shape[1] == 3, "Public train should have 3 columns."
    assert len(new_train) + len(new_test) == len(
        input_df
    ), "Train and test should sum up to the original data."

    return new_train, new_test


def prepare(raw: Path, public: Path, private: Path):
    """
    Prepares the raw data by creating two sets of splits:
    1. A main train/test split for the final competition (`public`/`private`).
    2. A validation split from the main training data (`public_val`/`private_val`).
    """
    initial_train_df = read_csv(raw / "train.csv")
    raw_images_dir = raw / "train"

    # --- 1. Create the original train/test split ---
    # This generates the primary competition files in public/ and private/.
    # The output of this step will remain identical to the original script.
    print("--- Generating main train/test split for 'public' and 'private' directories ---")
    main_train_df, _ = _create_split(
        input_df=initial_train_df,
        raw_images_dir=raw_images_dir,
        output_public_path=public,
        output_private_path=private,
    )

    # --- 2. Create the validation split from the main training set ---
    # This takes the training data from the first split and splits it again,
    # creating a smaller training set and a validation set.
    # The outputs are saved in parallel directories to avoid conflicts.
    print("\n--- Generating validation split for 'public_val' and 'private_val' directories ---")
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    _create_split(
        input_df=main_train_df,  # Use the training set from the first split as input
        raw_images_dir=raw_images_dir,  # Image sources are the same
        output_public_path=public_val,
        output_private_path=private_val,
    )

    print("\nData preparation complete.")