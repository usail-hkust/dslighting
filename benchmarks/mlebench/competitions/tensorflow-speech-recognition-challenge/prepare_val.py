import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from mlebench.utils import extract

CLASSES = [
    "yes",
    "no",
    "up",
    "down",
    "left",
    "right",
    "on",
    "off",
    "stop",
    "go",
    "unknown",
    "silence",
]


@dataclass(frozen=True)
class AudioFile:
    label: str
    path: Path


def _create_and_populate_split(
    files_to_split: List[AudioFile],
    public_dir: Path,
    private_dir: Path,
    test_size: float,
    random_state: int,
) -> List[AudioFile]:
    """
    Splits a list of audio files into train and test sets, and populates the
    corresponding public and private directories.

    Args:
        files_to_split: A list of AudioFile objects to be split.
        public_dir: The public directory to save training data and test stubs.
        private_dir: The private directory to save test ground truth.
        test_size: The proportion of the dataset to allocate to the test split.
        random_state: The seed used by the random number generator.

    Returns:
        A list of AudioFile objects that were assigned to the training set.
    """
    train_files, test_files = train_test_split(
        files_to_split, test_size=test_size, random_state=random_state
    )

    # Make necessary directories
    public_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)

    labels = list(
        dict.fromkeys([file.label for file in train_files])
    )  # Gets unique elements deterministically

    for label in labels:
        (public_dir / "train" / "audio" / label).mkdir(parents=True, exist_ok=True)

    (public_dir / "test" / "audio").mkdir(parents=True, exist_ok=True)

    # Copy over train and test files
    desc_suffix = public_dir.name
    for file in tqdm(train_files, desc=f"Copying train files to {desc_suffix}"):
        shutil.copyfile(
            src=file.path,
            dst=public_dir / "train" / "audio" / file.label / file.path.name,
        )

    test_records = []

    for idx, file in enumerate(tqdm(test_files, desc=f"Copying test files to {desc_suffix}")):
        # Rename files, since training audio files across labels aren't necessarily unique.
        new_id = str(idx).zfill(8)
        new_name = f"clip_{new_id}.wav"
        test_records.append({"fname": new_name, "label": file.label})

        shutil.copyfile(
            src=file.path,
            dst=public_dir / "test" / "audio" / new_name,
        )

    test = pd.DataFrame.from_records(test_records)
    test.to_csv(private_dir / "test.csv", index=False)

    test_without_labels = test.drop(columns=["label"])
    sample_submission = test_without_labels.copy()
    sample_submission["label"] = "silence"
    sample_submission.to_csv(public_dir / "sample_submission.csv", index=False)

    # Sanity checks
    test_audio_files = list((public_dir / "test" / "audio").glob("*.wav"))
    num_test_files = len(test_audio_files)
    num_submission_entries = len(sample_submission)
    assert num_test_files == num_submission_entries, (
        f"The number of test audio files ({num_test_files}) does not match the number of entries "
        f"in sample_submission.csv ({num_submission_entries}). Please check the file copying process."
    )

    return train_files


def prepare(raw: Path, public: Path, private: Path):
    # extract only what we need
    extract(raw / "train.7z", raw)

    # Create train, test from train split
    audio_dir = raw / "train" / "audio"
    all_audio_files = sorted(
        [AudioFile(fpath.parent.name, fpath) for fpath in audio_dir.rglob("*.wav")],
        key=lambda x: f"{x.label}_{x.path.name}",
    )

    # --- First Split: Create the original train/test sets ---
    # This call populates the original `public` and `private` directories.
    # It returns the files assigned to the training set for the next split.
    train_files_for_val_split = _create_and_populate_split(
        files_to_split=all_audio_files,
        public_dir=public,
        private_dir=private,
        test_size=0.1,
        random_state=0,
    )

    # --- Second Split: Create the new train_val/test_val sets ---
    # Define new paths for the validation split, parallel to the original ones.
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # To get a validation test set of the same size as the original test set,
    # we take a 1/9 slice of the remaining 90% of the data (0.1 / 0.9 = 1/9).
    _create_and_populate_split(
        files_to_split=train_files_for_val_split,
        public_dir=public_val,
        private_dir=private_val,
        test_size=1 / 9,
        random_state=0, # Use the same random_state for deterministic behavior
    )