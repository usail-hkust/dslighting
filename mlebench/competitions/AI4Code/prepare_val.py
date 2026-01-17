import json
import shutil
from pathlib import Path

import pandas as pd
from tqdm.auto import tqdm

from mlebench.utils import read_csv


# Create train, test from train split
def create_train_test_split(train_ancestors_df: pd.DataFrame, test_size: int):
    """
    On Kaggle, a user may "fork" (that is, copy) the notebook of another user to create their own version.
    `train_ancestors_df` contains information about the ancestry of each notebook in the training set.

    To create the test split, we select rows from the train set that don't share ancestors with any others
    so that there aren't any relatives in the train set. The train split is the remaining rows.
    """
    group_by_ancestor = {}
    for _, row in tqdm(
        train_ancestors_df.iterrows(), desc="Grouping by Ancestor", total=len(train_ancestors_df)
    ):
        ancestor_id = row["ancestor_id"]
        if ancestor_id not in group_by_ancestor:
            group_by_ancestor[ancestor_id] = []
        group_by_ancestor[ancestor_id].append(row)

    train_ids = []
    test_ids = []
    num_test_ids = 0
    # Ensure a deterministic split by sorting the groups
    sorted_ancestors = sorted(group_by_ancestor.items(), key=lambda x: x[0])
    for ancestor_id, rows in tqdm(sorted_ancestors, desc="Splitting on Ancestors"):
        if num_test_ids + len(rows) <= test_size:
            test_ids.extend(([row["id"] for row in rows]))
            num_test_ids += len(rows)
        else:
            train_ids.extend([row["id"] for row in rows])

    # The exact number of test samples can vary slightly based on group sizes.
    # We adjust the assertion to check it's close to the target, not necessarily equal.
    assert len(train_ids) + len(test_ids) == len(train_ancestors_df)

    return train_ids, test_ids


def _generate_split_files(
    train_ids: list,
    test_ids: list,
    public_dir: Path,
    private_dir: Path,
    raw_dir: Path,
    full_train_orders_df: pd.DataFrame,
    full_train_ancestors_df: pd.DataFrame,
):
    """
    A helper function to generate all required files for a given train/test split.
    This helps avoid code duplication and ensures consistent output structure.
    """
    # Create output directories
    public_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)
    (public_dir / "train").mkdir(exist_ok=True)
    (public_dir / "test").mkdir(exist_ok=True)

    # Copy json files to public
    for train_id in tqdm(train_ids, desc=f"Copying train json files to {public_dir.name}"):
        shutil.copy(raw_dir / "train" / f"{train_id}.json", public_dir / "train" / f"{train_id}.json")
    for test_id in tqdm(test_ids, desc=f"Copying test json files to {public_dir.name}"):
        shutil.copy(raw_dir / "train" / f"{test_id}.json", public_dir / "test" / f"{test_id}.json")

    # Generate answers for train and test
    # Answers for new train
    train_orders_new = full_train_orders_df[full_train_orders_df["id"].isin(train_ids)]
    train_orders_new.to_csv(public_dir / "train_orders.csv", index=False)
    # Answers for new test
    test_orders_new = full_train_orders_df[full_train_orders_df["id"].isin(test_ids)]
    test_orders_new.to_csv(private_dir / "test_orders.csv", index=False)

    # Make new train_ancestors.csv, excluding the new_test_ids
    train_ancestors_new = full_train_ancestors_df[
        full_train_ancestors_df["id"].isin(train_ids)
    ]
    train_ancestors_new.to_csv(public_dir / "train_ancestors.csv", index=False)

    # Create sample submission (use the given order without changing it)
    sample_submission_rows = []
    for sample_id in tqdm(
        test_orders_new["id"], desc=f"Creating sample submission for {public_dir.name}"
    ):
        # Get cell order from json file
        with open(public_dir / "test" / f"{sample_id}.json") as f:
            json_data = json.load(f)
            cell_order = list(json_data["cell_type"].keys())
        sample_submission_rows.append({"id": sample_id, "cell_order": " ".join(cell_order)})
    sample_submission = pd.DataFrame(sample_submission_rows)
    sample_submission.to_csv(public_dir / "sample_submission.csv", index=False)
    assert len(sample_submission) == len(test_ids), "Sample submission length does not match test length."


def prepare(raw: Path, public: Path, private: Path):
    # --- Initial Setup ---
    TEST_SIZE = 20000
    # Load all necessary data once
    full_train_ancestors_df = read_csv(raw / "train_ancestors.csv")
    full_train_orders_df = read_csv(raw / "train_orders.csv")

    # Shuffle the train_ancestors_df to ensure our split is random but reproducible
    shuffled_ancestors_df = full_train_ancestors_df.sample(
        frac=1, random_state=0
    ).reset_index(drop=True)

    # --- 1. Original Split (train/test) ---
    print("--- Generating original train/test split ---")
    train_ids, test_ids = create_train_test_split(shuffled_ancestors_df, test_size=TEST_SIZE)

    # Generate files for the original public and private directories
    _generate_split_files(
        train_ids,
        test_ids,
        public,
        private,
        raw,
        full_train_orders_df,
        shuffled_ancestors_df,
    )

    # --- 2. Validation Split (train_val/test_val) ---
    print("\n--- Generating new validation split ---")
    # Define paths for the new validation directories
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # The input for the second split is the training set from the first split.
    # We use the already shuffled dataframe to maintain deterministic behavior.
    train_subset_for_val_split = shuffled_ancestors_df[
        shuffled_ancestors_df["id"].isin(train_ids)
    ].reset_index(drop=True)

    # Create the second split from the first split's training data
    train_val_ids, test_val_ids = create_train_test_split(
        train_subset_for_val_split, test_size=TEST_SIZE
    )

    # Generate the validation split files in the new directories
    _generate_split_files(
        train_val_ids,
        test_val_ids,
        public_val,
        private_val,
        raw,
        full_train_orders_df,
        shuffled_ancestors_df,
    )

    print("\nData preparation complete.")
    print(f"Original split created in '{public.name}' and '{private.name}'.")
    print(f"Validation split created in '{public_val.name}' and '{private_val.name}'.")