from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from mlebench.utils import get_logger

logger = get_logger(__name__)


def extract_string(document_text: str, start_token_idx: int, end_token_idx: int) -> str:
    document_tokens = document_text.split(" ")
    extract_tokens = document_tokens[start_token_idx:end_token_idx]
    return " ".join(extract_tokens)


def create_submission_files(
    lightweight_test_df: pd.DataFrame, public_path: Path, private_path: Path, n_test_samples: int
):
    """
    Creates the gold submission (private) and sample submission (public) files.
    """
    # Create a gold submission with columns "example_id", "PredictionString"
    gold_rows = []
    for idx, sample in tqdm(
        lightweight_test_df.iterrows(),
        total=len(lightweight_test_df),
        desc=f"Creating submission files for {public_path.name}",
    ):
        sample = sample.to_dict()
        assert len(sample["annotations"]) == 1
        annotation = sample["annotations"][0]

        # Create short answer
        # Multiple answers are possible: yes_no_answer or one of short_answers
        # We just take the first one
        if annotation["yes_no_answer"] != "NONE":
            answer = annotation["yes_no_answer"]
        elif len(annotation["short_answers"]) > 0:
            start_token = annotation["short_answers"][0]["start_token"]
            end_token = annotation["short_answers"][0]["end_token"]
            answer = f"{start_token}:{end_token}"
        else:
            answer = ""

        gold_rows.append(
            {"example_id": f"{sample['example_id']}_short", "PredictionString": answer}
        )

        # Create long answer
        if annotation["long_answer"]["start_token"] != -1:
            start_token = annotation["long_answer"]["start_token"]
            end_token = annotation["long_answer"]["end_token"]
            answer = f"{start_token}:{end_token}"
        else:
            answer = ""

        gold_rows.append({"example_id": f"{sample['example_id']}_long", "PredictionString": answer})

    gold_submission = pd.DataFrame(gold_rows)
    gold_submission.to_csv(private_path / "gold_submission.csv", index=False)

    # Sample submission
    sample_submission = gold_submission.copy()
    sample_submission["PredictionString"] = ""
    sample_submission.to_csv(public_path / "sample_submission.csv", index=False)

    assert len(gold_submission) == 2 * n_test_samples
    assert len(sample_submission) == 2 * n_test_samples


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the data in raw into public and private datasets with appropriate test/train splits.
    Then, it further splits the created train set into a smaller train set and a validation set.
    """
    # Define and create paths for the new validation split
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"
    public_val.mkdir(exist_ok=True)
    private_val.mkdir(exist_ok=True)

    # --- STAGE 1: Create Original Train/Test Split ---
    # This section creates the original `public` and `private` outputs.

    train_file = "simplified-nq-train.jsonl"
    public_train_file = public / "simplified-nq-train.jsonl"

    logger.info("Counting lines in raw data file...")
    with open(raw / train_file, "r") as f:
        n_lines_raw = sum(1 for _ in f)
    logger.info(f"Found {n_lines_raw} lines in raw data file.")

    # Read data in chunks to avoid memory issues
    train_ids, test_ids = [], []
    lightweight_test = []  # We'll use this to create a gold submission later
    with tqdm(total=n_lines_raw, desc="Splitting raw data -> train/test") as pbar:
        for df in pd.read_json(raw / train_file, orient="records", lines=True, chunksize=1_000):
            # Convert IDs to strings, Kaggle.com is inconsistent about this but strings make more sense
            df["example_id"] = df["example_id"].astype(str)
            new_train, new_test = train_test_split(df, test_size=0.1, random_state=0)

            keys_to_keep = [
                "example_id",
                "question_text",
                "document_text",
                "long_answer_candidates",
            ]
            new_test_without_labels = new_test.copy()[keys_to_keep]

            # Append lines to new train and test
            with open(public_train_file, "a") as f:
                f.write(new_train.to_json(orient="records", lines=True))
            with open(private / "test.jsonl", "a") as f:
                f.write(new_test.to_json(orient="records", lines=True))
            with open(public / "simplified-nq-test.jsonl", "a") as f:
                f.write(new_test_without_labels.to_json(orient="records", lines=True))

            train_ids.extend(new_train["example_id"].tolist())
            test_ids.extend(new_test["example_id"].tolist())
            lightweight_test.append(
                new_test.copy()[["example_id", "question_text", "annotations"]]
            )  # For gold submission
            pbar.update(len(df))

    lightweight_test_df = pd.concat(lightweight_test, ignore_index=True)

    assert len(train_ids) + len(test_ids) == n_lines_raw
    assert len(lightweight_test_df) == len(test_ids)

    # Create submission files for the original test set
    create_submission_files(lightweight_test_df, public, private, len(test_ids))
    logger.info("Finished creating original `public` and `private` directories.")

    # --- STAGE 2: Create Validation Split from the new Train Set ---
    # This section reads the train set created in Stage 1 and splits it again.
    # The outputs are written to `public_val` and `private_val` directories.

    logger.info("Counting lines in the created train file for validation split...")
    with open(public_train_file, "r") as f:
        n_lines_train = sum(1 for _ in f)
    logger.info(f"Found {n_lines_train} lines in train file.")

    train_val_ids, test_val_ids = [], []
    lightweight_test_val = []  # For the validation set's gold submission
    with tqdm(total=n_lines_train, desc="Splitting train data -> train_val/test_val") as pbar:
        # Read the newly created train file in chunks for the second split
        for df_train_chunk in pd.read_json(
            public_train_file, orient="records", lines=True, chunksize=1_000
        ):
            # Replicate the splitting logic on the training data
            new_train_val, new_test_val = train_test_split(
                df_train_chunk, test_size=0.1, random_state=0
            )

            keys_to_keep = [
                "example_id",
                "question_text",
                "document_text",
                "long_answer_candidates",
            ]
            new_test_val_without_labels = new_test_val.copy()[keys_to_keep]

            # Append lines to the new validation-split train and test files
            with open(public_val / "simplified-nq-train.jsonl", "a") as f:
                f.write(new_train_val.to_json(orient="records", lines=True))
            with open(private_val / "test.jsonl", "a") as f:
                f.write(new_test_val.to_json(orient="records", lines=True))
            with open(public_val / "simplified-nq-test.jsonl", "a") as f:
                f.write(new_test_val_without_labels.to_json(orient="records", lines=True))

            train_val_ids.extend(new_train_val["example_id"].tolist())
            test_val_ids.extend(new_test_val["example_id"].tolist())
            lightweight_test_val.append(
                new_test_val.copy()[["example_id", "question_text", "annotations"]]
            )
            pbar.update(len(df_train_chunk))

    lightweight_test_val_df = pd.concat(lightweight_test_val, ignore_index=True)

    assert len(train_val_ids) + len(test_val_ids) == n_lines_train
    assert len(lightweight_test_val_df) == len(test_val_ids)

    # Create submission files for the new validation set
    create_submission_files(lightweight_test_val_df, public_val, private_val, len(test_val_ids))
    logger.info("Finished creating new `public_val` and `private_val` directories.")