import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


def get_date(s: str) -> str:
    """Gets date from string in the format YYYY-MM-DD-X where `X` is an arbitrary string."""

    split = s.split("-")

    assert (
        len(split) >= 3
    ), f"Expected the string to have at least 3 parts separated by `-`. Got {len(split)} parts."

    year, month, day = split[:3]

    assert (
        isinstance(year, str) and year.isdigit()
    ), f"Expected the year to be a string of digits. Got {year} instead."

    assert (
        isinstance(month, str) and month.isdigit()
    ), f"Expected the month to be a string of digits. Got {month} instead."

    assert (
        isinstance(day, str) and day.isdigit()
    ), f"Expected the day to be a string of digits. Got {day} instead."

    date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    return date


def _process_split(
    raw_data_path: Path,
    train_ids: list,
    test_ids: list,
    public_path: Path,
    private_path: Path,
) -> None:
    """
    Helper function to process a single data split.

    It populates the public and private directories with the provided train/test IDs,
    creating the necessary file structure and artifacts (like the sample submission).
    """
    # Clean and create output directories
    shutil.rmtree(public_path, ignore_errors=True)
    shutil.rmtree(private_path, ignore_errors=True)
    public_path.mkdir(parents=True)
    private_path.mkdir(parents=True)
    (public_path / "train").mkdir()
    (public_path / "test").mkdir()

    for train_id in train_ids:
        shutil.copytree(
            src=raw_data_path / "train" / train_id,
            dst=public_path / "train" / train_id,
        )

    for test_id in test_ids:
        shutil.copytree(
            src=raw_data_path / "train" / test_id,
            dst=public_path / "test" / test_id,
        )

    # Construct test set by concatenating all ground truth csvs for the test journeys
    dfs = []
    for fpath in sorted((public_path / "test").rglob("ground_truth.csv")):
        drive_id = fpath.parent.parent.name
        phone_id = fpath.parent.name

        assert (
            drive_id in test_ids
        ), f"Expected the drive {drive_id} to be one of the new test instances. Got {drive_id} instead."

        raw_df = pd.read_csv(fpath)
        df = raw_df.copy()
        df.loc[:, "tripId"] = f"{drive_id}-{phone_id}"
        df = df[["tripId", "UnixTimeMillis", "LatitudeDegrees", "LongitudeDegrees"]]
        dfs.append(df)

    new_test_labels = pd.concat(dfs, ignore_index=True)
    # The output filename is 'test.csv' to match the competition structure.
    new_test_labels.to_csv(private_path / "test.csv", index=False)

    for fpath in (public_path / "test").rglob("ground_truth.csv"):
        fpath.unlink()  # don't include ground truth in public test data

    shutil.copytree(
        src=raw_data_path / "metadata",
        dst=public_path / "metadata",
    )

    actual_journey_ids = set(["-".join(s.split("-")[:-1]) for s in new_test_labels["tripId"]])
    assert len(actual_journey_ids) == len(test_ids), (
        f"Expected the new test instances to have {len(test_ids)} unique trip IDs. Got "
        f"{len(new_test_labels['tripId'].unique())} unique trip IDs."
    )

    sample_submission = new_test_labels.copy()
    sample_submission.loc[:, "LatitudeDegrees"] = 37.904611315634504
    sample_submission.loc[:, "LongitudeDegrees"] = -86.48107806249548

    assert len(sample_submission) == len(new_test_labels), (
        f"Expected the sample submission to have the same number of instances as the new test "
        f"instances. Got {len(sample_submission)} instances in the sample submission and "
        f"{len(new_test_labels)} new test instances."
    )

    sample_submission.to_csv(public_path / "sample_submission.csv", index=False)

    assert sorted(list(public_path.glob("train/*"))) == sorted(
        set([public_path / "train" / drive_id for drive_id in train_ids])
    ), "Expected the public train directory to contain the new train instances."

    assert sorted(list(public_path.glob("test/*"))) == sorted(
        set([public_path / "test" / drive_id for drive_id in test_ids])
    ), "Expected the public test directory to contain the new test instances."

    assert (
        len(list((public_path / "test").rglob("ground_truth.csv"))) == 0
    ), "Expected the public test directory to not contain any ground truth files."

    assert len(list((public_path / "train").rglob("ground_truth.csv"))) >= len(train_ids), (
        "Expected the public train directory to contain at least one ground truth file per new "
        "train instance."
    )


def prepare(raw: Path, public: Path, private: Path) -> None:
    # --- Stage 1: Original Split (Train / Test) ---
    # This section creates the primary competition data in `public` and `private`.
    # Its logic and outputs are identical to the original script.

    old_train_ids = sorted([folder.name for folder in (raw / "train").glob("*") if folder.is_dir()])
    dates = sorted(set([get_date(s) for s in old_train_ids]))
    new_train_dates, new_test_dates = train_test_split(dates, test_size=0.1, random_state=0)

    assert (
        len(new_train_dates) >= 1
    ), "Expected the new train set to have at least one date. Got 0 dates."

    assert (
        len(new_test_dates) >= 1
    ), "Expected the new test set to have at least one date. Got 0 dates."

    new_train_ids = sorted([i for i in old_train_ids if get_date(i) in new_train_dates])
    new_test_ids = sorted([i for i in old_train_ids if get_date(i) in new_test_dates])

    assert len(set(new_train_ids).intersection(set(new_test_ids))) == 0, (
        f"Expected the new train and test instances to be disjoint. Got an intersection of "
        f"{set(new_train_ids).intersection(set(new_test_ids))}."
    )

    assert len(new_train_ids) + len(new_test_ids) == len(old_train_ids), (
        f"Expected the number of new train and test instances to sum up to the number of old train "
        f"instances. Got {len(new_train_ids)} new train instances and {len(new_test_ids)} new test "
        f"instances which sum to {len(new_train_ids) + len(new_test_ids)} instead of "
        f"{len(old_train_ids)}."
    )

    _process_split(
        raw_data_path=raw,
        train_ids=new_train_ids,
        test_ids=new_test_ids,
        public_path=public,
        private_path=private,
    )

    # --- Stage 2: Validation Split (Train_val / Test_val) ---
    # This section creates a new validation dataset in parallel directories.
    # It takes the `new_train_ids` from the first split and splits them again
    # using the exact same methodology.

    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # The input for this split is the training set from the *first* split.
    val_split_input_dates = sorted(set([get_date(s) for s in new_train_ids]))

    # We replicate the splitting logic and parameters to get a test set of a
    # similar proportional size to the original test set.
    train_val_dates, test_val_dates = train_test_split(
        val_split_input_dates, test_size=0.1, random_state=0
    )

    train_val_ids = sorted([i for i in new_train_ids if get_date(i) in train_val_dates])
    test_val_ids = sorted([i for i in new_train_ids if get_date(i) in test_val_dates])

    _process_split(
        raw_data_path=raw,
        train_ids=train_val_ids,
        test_ids=test_val_ids,
        public_path=public_val,
        private_path=private_val,
    )