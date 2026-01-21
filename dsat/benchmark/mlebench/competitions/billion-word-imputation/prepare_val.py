import os
import shutil
import zipfile
from pathlib import Path

import numpy as np
from tqdm.auto import tqdm

from mlebench.utils import extract, get_logger

np_rng = np.random.RandomState(0)

logger = get_logger(__name__)


def count_lines_in_file(file_path):
    line_count = 0
    with open(file_path, "r", encoding="utf-8") as file:
        for _line in file:
            line_count += 1
    return line_count


def compress_file_to_zip(src_file: Path, zip_file: Path):
    with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(src_file, arcname=src_file.name)


def remove_random_word(sentence: str) -> str:
    """
    Remove a random 'word' (sequence of characters, delimited by whitespace) from a sentence.
    Does not remove first or last words.

    Punctuation counts as a word, and is already separated by whitespace.
    """
    words = sentence.split()
    index = np_rng.randint(1, len(words) - 1)
    return " ".join(words[:index] + words[index + 1 :])


def _split_and_process_data(
    input_file: Path,
    output_train_file: Path,
    output_public_test_file: Path,
    output_private_test_file: Path,
    total_lines: int,
) -> tuple[int, int]:
    """
    Helper function to perform the core data splitting and processing logic.

    Reads from an input file and splits it into a train and test set based on a
    probabilistic condition, writing them to the specified output files.
    """
    with (
        open(input_file, "r", encoding="utf-8") as old_train,
        open(output_train_file, "w", encoding="utf-8") as public_train,
        open(output_public_test_file, "w", encoding="utf-8") as public_test,
        open(output_private_test_file, "w", encoding="utf-8") as private_test,
    ):
        public_test.write('"id","sentence"\n')
        private_test.write('"id","sentence"\n')
        test_count = 0
        train_count = 0
        # there is one sentence per line
        for sentence in tqdm(old_train, desc=f"Processing {input_file.name}", total=total_lines):
            # we will put ~0.01 of the data in test, the rest in train, matching kaggle's original split
            # some sentences only have 2 words, so can't remove a word -- keep them in train
            if np_rng.uniform() <= 0.01 and len(sentence.strip().split()) > 2:
                # get rid of linebreak and escape quotes
                sentence_clean = sentence.strip().replace('"', '""')
                removed_word_sentence = remove_random_word(sentence_clean)
                private_test.write(f'{test_count},"{sentence_clean}"\n')
                public_test.write(f'{test_count},"{removed_word_sentence}"\n')
                test_count += 1
            else:
                public_train.write(sentence)
                train_count += 1
    return train_count, test_count


def prepare(raw: Path, public: Path, private: Path):
    logger.info("Extracting raw / train_v2.txt.zip")
    extract(raw / "train_v2.txt.zip", raw)

    # Define and create the new validation directories
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"
    public_val.mkdir(exist_ok=True, parents=True)
    private_val.mkdir(exist_ok=True, parents=True)

    # --- 1. Original Split (raw -> train/test) ---
    logger.info("--- Generating original train/test split ---")
    # computed this ahead of time
    total_lines = 30301028
    original_train_count, original_test_count = _split_and_process_data(
        input_file=raw / "train_v2.txt",
        output_train_file=public / "train_v2.txt",
        output_public_test_file=public / "test_v2.txt",
        output_private_test_file=private / "test.csv",
        total_lines=total_lines,
    )
    assert (
        original_train_count + original_test_count == total_lines
    ), "Sum of train and test samples must equal total samples for original split."

    # --- 2. Second Split (train -> train_val/test_val) ---
    logger.info("--- Generating validation split from the new training set ---")
    # The input for the second split is the training set from the first split.
    val_split_input_file = public / "train_v2.txt"
    val_split_total_lines = original_train_count
    val_train_count, val_test_count = _split_and_process_data(
        input_file=val_split_input_file,
        output_train_file=public_val / "train_v2.txt",
        output_public_test_file=public_val / "test_v2.txt",
        output_private_test_file=private_val / "test.csv",
        total_lines=val_split_total_lines,
    )
    assert (
        val_train_count + val_test_count == val_split_total_lines
    ), "Sum of train_val and test_val samples must equal total samples for validation split."

    # --- 3. Process and Compress Original public/private directories ---
    logger.info("--- Compressing and cleaning up original public/private directories ---")
    # we will be compressing the public files (to match what's on kaggle.com)
    # so copy our sample submission to private so we have access to it
    shutil.copy(public / "test_v2.txt", private / "sample_submission.csv")

    # compress the public files
    logger.info("Compressing train_v2.txt")
    compress_file_to_zip(public / "train_v2.txt", public / "train_v2.txt.zip")
    logger.info("Compressing test_v2.txt")
    compress_file_to_zip(public / "test_v2.txt", public / "test_v2.txt.zip")
    # remove the original files
    (public / "train_v2.txt").unlink()
    (public / "test_v2.txt").unlink()

    # --- 4. Process and Compress New public_val/private_val directories ---
    logger.info("--- Compressing and cleaning up validation public_val/private_val directories ---")
    # Replicate the process for the validation set
    shutil.copy(public_val / "test_v2.txt", private_val / "sample_submission.csv")

    # compress the public_val files
    logger.info("Compressing validation train_v2.txt")
    compress_file_to_zip(public_val / "train_v2.txt", public_val / "train_v2.txt.zip")
    logger.info("Compressing validation test_v2.txt")
    compress_file_to_zip(public_val / "test_v2.txt", public_val / "test_v2.txt.zip")
    # remove the original files
    (public_val / "train_v2.txt").unlink()
    (public_val / "test_v2.txt").unlink()

    # --- 5. Final Checks ---
    logger.info("--- Running final checks ---")
    # Original Checks
    assert not (public / "train_v2.txt").exists(), "public / 'train_v2.txt' should not exist"
    assert (public / "train_v2.txt.zip").exists(), "public / 'train_v2.txt.zip' should exist"
    assert not (public / "test_v2.txt").exists(), "public / 'test_v2.txt' should not exist"
    assert (public / "test_v2.txt.zip").exists(), "public / 'test_v2.txt.zip' should exist"

    private_test_line_count = count_lines_in_file(private / "test.csv")
    assert (
        private_test_line_count - 1 == original_test_count
    ), "private / 'test.csv' has incorrect number of lines"
    assert (
        count_lines_in_file(private / "sample_submission.csv") == private_test_line_count
    ), "private / 'sample_submission.csv' has incorrect number of lines"

    # New Checks for Validation Set
    assert not (public_val / "train_v2.txt").exists(), "public_val / 'train_v2.txt' should not exist"
    assert (public_val / "train_v2.txt.zip").exists(), "public_val / 'train_v2.txt.zip' should exist"
    assert not (public_val / "test_v2.txt").exists(), "public_val / 'test_v2.txt' should not exist"
    assert (public_val / "test_v2.txt.zip").exists(), "public_val / 'test_v2.txt.zip' should exist"

    private_val_test_line_count = count_lines_in_file(private_val / "test.csv")
    assert (
        private_val_test_line_count - 1 == val_test_count
    ), "private_val / 'test.csv' has incorrect number of lines"
    assert (
        count_lines_in_file(private_val / "sample_submission.csv") == private_val_test_line_count
    ), "private_val / 'sample_submission.csv' has incorrect number of lines"