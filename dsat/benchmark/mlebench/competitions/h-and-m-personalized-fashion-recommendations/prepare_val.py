import os
import shutil
from pathlib import Path

import pandas as pd

from mlebench.utils import read_csv


def _split_and_process_data(transactions_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Splits a dataframe into train and test sets based on the last 7 days of transactions.

    Args:
        transactions_df: The input dataframe with transaction data.

    Returns:
        A tuple containing:
        - new_train_df: The training data (all data except the last 7 days).
        - answers_df: The ground truth answers for the test set (last 7 days).
    """
    df = transactions_df.copy()
    if "purchase_id" not in df.columns:
        df["purchase_id"] = (
            df["customer_id"].astype(str)
            + "_"
            + df["article_id"].astype(str)
            + "_"
            + df["t_dat"].astype(str)
        )

    # The task is to predict what purchases will be made in the next 7 days.
    # To create our test set, we will take the purchases made in the last 7 days of the training set.
    df["t_dat_parsed"] = pd.to_datetime(df["t_dat"])  # Parse t_dat to datetime in a new column
    max_date = df["t_dat_parsed"].max()  # Find the maximum date in the t_dat_parsed column
    df["in_last_7_days"] = df["t_dat_parsed"] >= (max_date - pd.Timedelta(days=7))

    new_train_df = df[df["in_last_7_days"] == False].copy()
    new_test_df = df[df["in_last_7_days"] == True].copy()

    # Train/test checks
    assert (
        not new_test_df["purchase_id"].isin(new_train_df["purchase_id"]).any()
    ), "No purchase_ids should be shared between a test and train split"

    new_train_df = new_train_df.drop(columns=["purchase_id", "t_dat_parsed", "in_last_7_days"])

    # Answers, contains only customers that actually made purchases in the test period.
    answers_df = (
        new_test_df.groupby("customer_id")["article_id"]
        .apply(lambda x: " ".join(x.astype(str)))
        .reset_index()
    )
    # rename 'article_id' to 'prediction'
    answers_df = answers_df.rename(columns={"article_id": "prediction"})

    return new_train_df, answers_df


def _copy_static_files(raw_path: Path, public_path: Path):
    """Copies static competition files (articles, customers, images) to a public directory."""
    # Sample submission, which contains all customer ids.
    shutil.copyfile(
        src=raw_path / "sample_submission.csv",
        dst=public_path / "sample_submission.csv",
    )
    # Copy files and images directory
    shutil.copyfile(
        src=raw_path / "articles.csv",
        dst=public_path / "articles.csv",
    )
    shutil.copyfile(
        src=raw_path / "customers.csv",
        dst=public_path / "customers.csv",
    )
    shutil.copytree(
        src=raw_path / "images",
        dst=public_path / "images",
        dirs_exist_ok=True,
    )


def _run_output_checks(train_df: pd.DataFrame, answers_df: pd.DataFrame):
    """Runs assertions to check the format of final output dataframes."""
    expected_train_columns = ["t_dat", "customer_id", "article_id", "price", "sales_channel_id"]
    assert (
        train_df.columns.tolist() == expected_train_columns
    ), f"Unexcpected columns in new_train, expected {expected_train_columns}, got {train_df.columns.tolist()}"

    expected_answer_columns = ["customer_id", "prediction"]
    assert (
        answers_df.columns.tolist() == expected_answer_columns
    ), f"Unexcpected columns in answers, expected {expected_answer_columns}, got {answers_df.columns.tolist()}"
    assert answers_df["customer_id"].nunique() == len(
        answers_df
    ), "There should be no duplicate customer_ids in answers"


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the data in raw into public and private datasets with appropriate test/train splits.
    Also creates a second, parallel validation split (in public_val/private_val).
    """
    # Create train, test from train split
    raw_transactions = read_csv(raw / "transactions_train.csv")

    # --- Original Data Split (Train/Test) ---
    # This split generates the main competition files.
    train_orig, answers_orig = _split_and_process_data(raw_transactions)

    # Write original public and private files
    answers_orig.to_csv(private / "answers.csv", index=False)
    train_orig.to_csv(public / "transactions_train.csv", index=False)
    _copy_static_files(raw, public)
    _run_output_checks(train_orig, answers_orig)

    # --- New Validation Data Split (Train/Val) ---
    # Define and create the new directories for the validation set.
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"
    public_val.mkdir(parents=True, exist_ok=True)
    private_val.mkdir(parents=True, exist_ok=True)

    # This second split takes the *output training set* from the first split
    # and splits it again to create a new, smaller training set and a validation set.
    train_val, answers_val = _split_and_process_data(train_orig)

    # Write validation set files to the new directories, mirroring the original structure.
    answers_val.to_csv(private_val / "answers.csv", index=False)
    train_val.to_csv(public_val / "transactions_train.csv", index=False)
    _copy_static_files(raw, public_val)
    _run_output_checks(train_val, answers_val)