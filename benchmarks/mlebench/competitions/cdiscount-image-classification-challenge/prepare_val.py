import shutil
from itertools import islice
from pathlib import Path

import bson
import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the data in raw into public and private datasets with appropriate test/train splits.
    Also creates a secondary validation split in public_val/private_val directories.
    """

    dev_mode = False

    def read_ids_and_category_ids(file_path: Path) -> pd.DataFrame:
        data = bson.decode_file_iter(open(file_path, "rb"))

        records = []

        for c, d in enumerate(tqdm(data, desc="Reading BSON data")):
            records.append({"_id": d["_id"], "category_id": d["category_id"]})

        return pd.DataFrame(records)

    def filter_bson_by_ids(
        bson_file_path: Path,
        ids: set,
        write_path: Path,
        exclude_cols: list = [],
        chunk_size=1000,
        max_rows=None,
    ):
        """
        Filters a BSON file by a set of IDs and writes the filtered data to a new BSON file.
        The original _id is replaced with a new _id starting from 0 and incrementing by 1.

        Args:
            bson_file_path (Path): Path to the input BSON file.
            ids (set): Set of IDs to filter by.
            write_path (Path): Path to the output BSON file.
            exclude_cols (list): List of columns to exclude from the output.
            max_rows (int, optional): Maximum number of rows to write to the output file.
        """
        data = bson.decode_file_iter(open(bson_file_path, "rb"))
        num_written_rows = 0

        with open(write_path, "wb") as f:
            for record in tqdm(data, desc=f"Filtering BSON data for {write_path.name}"):
                if record["_id"] in ids:
                    for col in exclude_cols:
                        if col in record:
                            del record[col]
                    num_written_rows += 1
                    f.write(bson.BSON.encode(record))

                if num_written_rows % chunk_size == 0:
                    f.flush()

                if max_rows is not None and num_written_rows >= max_rows:
                    break

    def is_valid_bson_file(file_path: Path, chunk_size: int = 10000):
        try:
            with open(file_path, "rb") as f:
                data_iter = bson.decode_file_iter(f)
                for chunk in tqdm(
                    iter(lambda: list(islice(data_iter, chunk_size)), []),
                    desc=f"Validating {file_path.name}",
                ):
                    pd.DataFrame(chunk)  # Attempt to create a DataFrame from the chunk
        except Exception as e:
            print(f"BSON validation failed for {file_path}: {e}")
            return False

        return True

    def _process_and_write_split(
        train_df: pd.DataFrame,
        test_df: pd.DataFrame,
        target_public_path: Path,
        target_private_path: Path,
    ):
        """
        Helper function to process a given train/test split and write all associated files
        to the specified public and private directories.
        """
        # Create output directories
        target_public_path.mkdir(exist_ok=True)
        target_private_path.mkdir(exist_ok=True)
        
        # Sort test dataframe for consistency
        answers = test_df.sort_values(by="_id")

        # Create sample submission
        sample_submission = answers[["_id"]]
        sample_submission["category_id"] = 1000010653

        # Basic integrity checks
        assert set(train_df["_id"]).isdisjoint(
            set(answers["_id"])
        ), "Train and test sets should not have any _ids in common"
        assert sample_submission.columns.tolist() == [
            "_id",
            "category_id",
        ], f"sample_submission should have columns _id and category_id. Got {sample_submission.columns.tolist()}"

        # Write new files
        answers.to_csv(target_private_path / "answers.csv", index=False)
        sample_submission.to_csv(target_public_path / "sample_submission.csv", index=False)

        # Determine raw data source based on dev_mode
        raw_bson_source = raw / "train_example.bson" if dev_mode else raw / "train.bson"

        filter_bson_by_ids(
            bson_file_path=raw_bson_source,
            ids=set(train_df["_id"]),
            write_path=target_public_path / "train.bson",
        )
        filter_bson_by_ids(
            bson_file_path=raw_bson_source,
            ids=set(answers["_id"]),
            write_path=target_public_path / "test.bson",
            exclude_cols=["category_id"],
        )
        filter_bson_by_ids(
            bson_file_path=raw_bson_source,
            ids=set(train_df["_id"]),
            write_path=target_public_path / "train_example.bson",
            max_rows=100,
        )

        # Validate generated BSON files
        assert is_valid_bson_file(target_public_path / "train.bson")
        assert is_valid_bson_file(target_public_path / "test.bson")
        
        # Copy over other files
        shutil.copy(raw / "category_names.csv", target_public_path / "category_names.csv")

        # Final check on train_example.bson content
        actual_new_train = read_ids_and_category_ids(target_public_path / "train.bson")
        actual_new_train_example = read_ids_and_category_ids(target_public_path / "train_example.bson")

        assert actual_new_train.iloc[:100].equals(
            actual_new_train_example
        ), f"The first 100 rows of `train.bson` should be the same as `train_example.bson` in {target_public_path}"


    # --- Main Script Logic ---

    # Read the complete dataset IDs and categories
    # Original train.bson contains 7,069,896 rows. Original test.bson contains 1,768,182 rows.
    old_train = read_ids_and_category_ids(raw / "train.bson")

    # === 1. Original Split: (train -> new_train + test) ===
    # This split creates the primary competition data in `public` and `private`.
    # This block is functionally identical to the original script to ensure outputs do not change.
    print("--- Processing Original Split (public/private) ---")
    new_train, answers = train_test_split(old_train, test_size=0.1, random_state=0)
    
    assert len(new_train) + len(answers) == len(
        old_train
    ), f"The length of new_train and answers combined should be equal to the original length of old_train. Got {len(new_train) + len(answers)} and {len(old_train)}"

    _process_and_write_split(
        train_df=new_train,
        test_df=answers,
        target_public_path=public,
        target_private_path=private,
    )
    print("--- Original Split processing complete. ---")


    # === 2. New Validation Split: (new_train -> train_val + test_val) ===
    # This second split takes the `new_train` set from above and splits it again.
    # The outputs are saved to new, parallel directories `public_val` and `private_val`.
    print("\n--- Processing Validation Split (public_val/private_val) ---")
    
    # Define paths for the new validation set
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # To make the new `test_val` set have a similar size to the original `test` set (10% of total),
    # we must take a fraction of `new_train`. Since `new_train` is 90% of the total,
    # we take 1/9 of it to get our new test set. (1/9) * 0.9 = 0.1
    test_val_size_fraction = 1 / 9.0
    
    train_val, answers_val = train_test_split(
        new_train, test_size=test_val_size_fraction, random_state=0
    )

    assert len(train_val) + len(answers_val) == len(
        new_train
    ), "The validation split did not partition the new_train set correctly."
    
    _process_and_write_split(
        train_df=train_val,
        test_df=answers_val,
        target_public_path=public_val,
        target_private_path=private_val,
    )
    print("--- Validation Split processing complete. ---")