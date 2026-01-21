import shutil
from pathlib import Path
from typing import Dict

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from mlebench.utils import read_csv


def _process_and_save_split(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    answers_df: pd.DataFrame,
    public_path: Path,
    private_path: Path,
    raw_path: Path,
    raw_supplementary_data: Dict[str, pd.DataFrame],
):
    """
    Helper function to process and save a single data split (e.g., train/test or train_val/test_val).

    This function takes a pair of train/test sets, filters the supplementary data accordingly,
    performs checks, and writes all the necessary files to the specified public and private directories.
    """
    public_path.mkdir(exist_ok=True)
    private_path.mkdir(exist_ok=True)

    # Create sample submission for the current test set
    sample_submission = test_df[["id"]].copy()
    sample_submission["scalar_coupling_constant"] = 0

    # Filter supplementary data to only include molecules present in the training set
    train_molecules = set(train_df["molecule_name"])
    filtered_supplementary_data = {}
    for name, df in raw_supplementary_data.items():
        filtered_supplementary_data[name] = df[df["molecule_name"].isin(train_molecules)]

    # Checks before writing
    for name, dataset in filtered_supplementary_data.items():
        assert set(dataset["molecule_name"]) == train_molecules, (
            f"[{public_path.name}] Filtered {name} should exactly match the molecule names "
            "present in the train set."
        )

    assert set(train_df["molecule_name"]).isdisjoint(
        set(test_df["molecule_name"])
    ), f"[{public_path.name}] Train and test sets should not share any molecule names."

    assert set(train_df["id"]).isdisjoint(
        set(test_df["id"])
    ), f"[{public_path.name}] Train and test sets should not share any sample ids."

    assert len(sample_submission) == len(
        test_df
    ), f"[{public_path.name}] Sample submission length does not match test length."

    # Write CSVs to public and private directories
    answers_df.to_csv(private_path / "answers.csv", index=False)

    train_df.to_csv(public_path / "train.csv", index=False)
    test_df.to_csv(public_path / "test.csv", index=False)
    sample_submission.to_csv(public_path / "sample_submission.csv", index=False)

    for name, df in filtered_supplementary_data.items():
        df.to_csv(public_path / f"{name}.csv", index=False)

    # Copy over molecule structure .xyz files for the training set
    structures_xyz_path = public_path / "structures"
    structures_xyz_path.mkdir(parents=True, exist_ok=True)
    for molecule_name in tqdm(
        train_df["molecule_name"].unique(),
        desc=f"Copying .xyz files to {public_path.name}",
    ):
        src_file = raw_path / "structures" / f"{molecule_name}.xyz"
        dst_file = structures_xyz_path / f"{molecule_name}.xyz"
        shutil.copyfile(src=src_file, dst=dst_file)

    # Checks after writing
    assert len(list(structures_xyz_path.glob("*.xyz"))) == len(
        train_df["molecule_name"].unique()
    ), (
        f"[{public_path.name}] The number of files in {structures_xyz_path} should match the number "
        "of unique molecule names in the train set."
    )


def prepare(raw: Path, public: Path, private: Path):
    """
    Prepares the data by performing two splits:
    1. A main split of the raw data into a definitive train/test set.
       Outputs are saved to `public/` and `private/`.
    2. A validation split of the main training set into a smaller train/validation set.
       Outputs are saved to `public_val/` and `private_val/`, mirroring the main output structure.
    """
    # Load all data from raw directory first
    old_train = read_csv(raw / "train.csv")

    # Load all supplementary data into a dictionary for easy filtering later
    raw_supplementary_data = {
        "structures": read_csv(raw / "structures.csv"),
        "dipole_moments": read_csv(raw / "dipole_moments.csv"),
        "magnetic_shielding_tensors": read_csv(raw / "magnetic_shielding_tensors.csv"),
        "mulliken_charges": read_csv(raw / "mulliken_charges.csv"),
        "potential_energy": read_csv(raw / "potential_energy.csv"),
        "scalar_coupling_contributions": read_csv(raw / "scalar_coupling_contributions.csv"),
    }

    # --- Create main Train/Test Split (Original Logic) ---
    # The outputs of this split are final and must not be changed.
    grouped_by_molecule = list(old_train.groupby("molecule_name"))
    train_groups, test_groups = train_test_split(grouped_by_molecule, test_size=0.1, random_state=0)
    new_train = pd.concat([group for _, group in train_groups])
    answers = pd.concat([group for _, group in test_groups])
    new_test = answers.drop(columns=["scalar_coupling_constant"])

    # Process and save the main split to `public` and `private` directories
    _process_and_save_split(
        train_df=new_train,
        test_df=new_test,
        answers_df=answers,
        public_path=public,
        private_path=private,
        raw_path=raw,
        raw_supplementary_data=raw_supplementary_data,
    )

    # --- Create Validation Split (New Logic) ---
    # This second split uses the `new_train` set from above to create a smaller
    # training set and a new validation set.
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Split the `new_train` set by molecule groups again.
    # The original test set was 10% of the total. The new train set is 90% of the total.
    # To get a validation set of a similar size (10% of total), the test_size for this
    # second split should be (10% / 90%) = 1/9.
    train_val_groups, test_val_groups = train_test_split(
        train_groups, test_size=1 / 9, random_state=0
    )
    train_val = pd.concat([group for _, group in train_val_groups])
    answers_val = pd.concat([group for _, group in test_val_groups])
    test_val = answers_val.drop(columns=["scalar_coupling_constant"])

    # Process and save the validation split to `public_val` and `private_val` directories
    _process_and_save_split(
        train_df=train_val,
        test_df=test_val,
        answers_df=answers_val,
        public_path=public_val,
        private_path=private_val,
        raw_path=raw,
        raw_supplementary_data=raw_supplementary_data,
    )