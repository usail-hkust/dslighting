import glob
import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from mlebench.utils import extract, read_csv


def _process_split(
    source_df: pd.DataFrame,
    test_size: float,
    random_state: int,
    source_geometry_paths: list,
    public_dir: Path,
    private_dir: Path,
) -> pd.DataFrame:
    """
    Helper function to perform a data split, re-index, and write all necessary files.

    Args:
        source_df: The DataFrame to split.
        test_size: The proportion of the dataset to allocate to the test split.
        random_state: The seed used by the random number generator.
        source_geometry_paths: A list of paths to all original geometry files.
        public_dir: The destination directory for public-facing files (train set, test features).
        private_dir: The destination directory for private-facing files (test labels).

    Returns:
        The created training DataFrame, which can be used for a subsequent split.
    """
    # Ensure destination directories exist
    public_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)

    # Create train, test from the source dataframe
    new_train, new_test = train_test_split(
        source_df, test_size=test_size, random_state=random_state
    )

    # Make ids go 1, 2, ... for both train and test. Keep old ids so we can map ids of other files
    old_train_id_to_new = {
        old_id: new_id for new_id, old_id in enumerate(new_train["id"], start=1)
    }  # id starts from 1
    new_train["id"] = new_train["id"].map(old_train_id_to_new)

    old_test_id_to_new = {
        old_id: new_id for new_id, old_id in enumerate(new_test["id"], start=1)
    }  # id starts from 1
    new_test["id"] = new_test["id"].map(old_test_id_to_new)

    new_test_without_labels = new_test.drop(
        columns=["formation_energy_ev_natom", "bandgap_energy_ev"]
    )

    # Copy over files
    new_train.to_csv(public_dir / "train.csv", index=False)
    new_test.to_csv(private_dir / "test.csv", index=False)
    new_test_without_labels.to_csv(public_dir / "test.csv", index=False)

    # --- Process and copy geometry files for the new train set ---
    train_geometry_dir = public_dir / "train"
    for src in source_geometry_paths:
        original_id = int(Path(src).parts[-2])
        if original_id not in old_train_id_to_new:  # Filter for train ids
            continue

        new_id = old_train_id_to_new[original_id]
        dest_dir = train_geometry_dir / str(new_id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(src=src, dst=dest_dir / "geometry.xyz")
    assert len(list(train_geometry_dir.glob("**/*.xyz"))) == len(
        new_train
    ), f"Expected {len(new_train)} train geometry files in {public_dir}, found {len(list(train_geometry_dir.glob('**/*.xyz')))}"

    # --- Process and copy geometry files for the new test set ---
    test_geometry_dir = public_dir / "test"
    for src in source_geometry_paths:
        original_id = int(Path(src).parts[-2])
        if original_id not in old_test_id_to_new:  # Filter for test ids
            continue

        new_id = old_test_id_to_new[original_id]
        dest_dir = test_geometry_dir / str(new_id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(src=src, dst=dest_dir / "geometry.xyz")
    assert len(list(test_geometry_dir.glob("**/*.xyz"))) == len(
        new_test
    ), f"Expected {len(new_test)} test geometry files in {public_dir}, found {len(list(test_geometry_dir.glob('**/*.xyz')))}"

    # Create mock submission
    sample_submission = pd.DataFrame(
        {"id": new_test["id"], "formation_energy_ev_natom": 0.1779, "bandgap_energy_ev": 1.8892}
    )
    sample_submission.to_csv(public_dir / "sample_submission.csv", index=False)
    assert len(sample_submission) == len(
        new_test
    ), f"Sample submission in {public_dir} should have the same number of rows as its test set"

    return new_train


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the data in raw into public and private datasets with appropriate test/train splits.
    Also creates a secondary validation split (public_val/private_val) from the training data.
    """
    # Define paths for the new validation set
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Extract only what we need
    extract(raw / "train.zip", raw / "train")
    extract(raw / "train.csv.zip", raw / "train.csv")
    extract(raw / "test.zip", raw / "test")
    extract(raw / "test.csv.zip", raw / "test.csv")

    # Load initial data and geometry paths
    initial_train_df = read_csv(raw / "train.csv/train.csv")
    all_geometry_paths = sorted(glob.glob(str(raw / "train/train/**/*.xyz")))

    # --- First Split: Create original public/private datasets ---
    # This split is identical to the original script to ensure unchanged outputs.
    train_df_after_first_split = _process_split(
        source_df=initial_train_df,
        test_size=0.1,
        random_state=0,
        source_geometry_paths=all_geometry_paths,
        public_dir=public,
        private_dir=private,
    )

    # --- Second Split: Create new validation datasets from the first split's train set ---
    # The test_size is set to 1/9 of the incoming data (which is 90% of the original).
    # This makes the new test_val set size equal to the original test set size (0.1 * T = 1/9 * 0.9 * T).
    _process_split(
        source_df=train_df_after_first_split,
        test_size=1 / 9,
        random_state=0,
        source_geometry_paths=all_geometry_paths,
        public_dir=public_val,
        private_dir=private_val,
    )