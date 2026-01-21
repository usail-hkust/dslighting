from pathlib import Path

import pandas as pd


def _create_competition_files(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    old_test_columns: pd.Index,
    old_sample_submission: pd.DataFrame,
    public_dir: Path,
    private_dir: Path,
    to_predict: list,
) -> None:
    """
    Helper function to generate the set of competition files for a given train/test split.
    This function creates the public and private directories and populates them with:
    - public/train.json
    - public/test.json
    - public/sample_submission.csv
    - private/test.csv (ground truth)
    """
    public_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)

    # Create `test.csv` by exploding each list in the `reactivity` and `deg_*` columns, analogous
    # to `pd.explode`. Only the first `seq_scored` items are scored out of a possible `seq_length`
    # items. For each row, we keep track of whether it's scored or not with the `keep` column.
    records = []

    for _, row in test_df.iterrows():
        n = row["seq_scored"]

        assert len(row["reactivity"]) == n
        assert len(row["deg_Mg_pH10"]) == n
        assert len(row["deg_pH10"]) == n
        assert len(row["deg_Mg_50C"]) == n
        assert len(row["deg_50C"]) == n

        for j in range(n):
            records.append(
                {
                    "id_seqpos": f"{row['id']}_{j}",
                    "reactivity": row["reactivity"][j],
                    "deg_Mg_pH10": row["deg_Mg_pH10"][j],
                    "deg_pH10": row["deg_pH10"][j],
                    "deg_Mg_50C": row["deg_Mg_50C"][j],
                    "deg_50C": row["deg_50C"][j],
                    "keep": True,
                }
            )

        k = row["seq_length"]

        assert n < k

        for j in range(n, k):
            records.append(
                {
                    "id_seqpos": f"{row['id']}_{j}",
                    "reactivity": 0.0,
                    "deg_Mg_pH10": 0.0,
                    "deg_pH10": 0.0,
                    "deg_Mg_50C": 0.0,
                    "deg_50C": 0.0,
                    "keep": False,
                }
            )

    # Write `answers.csv`
    answers = pd.DataFrame(records)
    answers.to_csv(private_dir / "test.csv", index=False, float_format="%.10f")

    # Write `train.json`
    train_df["index"] = range(len(train_df))
    train_df.to_json(public_dir / "train.json", orient="records", lines=True)

    # Write `test.json`
    test_without_labels = test_df[old_test_columns].copy()
    test_without_labels["index"] = range(len(test_without_labels))
    test_without_labels.to_json(public_dir / "test.json", orient="records", lines=True)

    # Write `sample_submission.csv`
    new_sample_submission = answers[["id_seqpos"] + to_predict].copy()
    new_sample_submission.loc[:, to_predict] = 0.0
    new_sample_submission.to_csv(
        public_dir / "sample_submission.csv", index=False, float_format="%.10f"
    )

    # Sanity checks
    assert "test" not in train_df.columns
    assert "test" not in test_df.columns

    assert set(test_without_labels.columns) == set(old_test_columns), (
        f"Expected the columns of the new test to be the same as the old test, but got "
        f"{set(test_without_labels.columns)} instead of {set(old_test_columns)}."
    )

    assert set(to_predict).intersection(set(test_without_labels.columns)) == set(), (
        f"Expected the columns to predict aren't included in the new test, but got "
        f"{set(to_predict) ^ set(test_without_labels.columns)} instead of the empty set."
    )

    assert set(new_sample_submission.columns) == set(old_sample_submission.columns), (
        f"Expected the columns of the new sample submission to be the same as the old sample "
        f"submission, but got {set(new_sample_submission.columns)} instead of "
        f"{set(old_sample_submission.columns)}."
    )

    assert len(answers) == len(new_sample_submission), (
        f"Expected the answers to have the same length as the new sample submission, but got "
        f"{len(answers)} instead of {len(new_sample_submission)}."
    )

    # we can use [0] because all sequences have the same length
    assert len(new_sample_submission) == (
        len(test_without_labels) * test_without_labels["seq_length"].iloc[0]
    ), (
        "Expected new_sample_submission length to be equal to max seq_length * len(new_test)."
        f"Got {len(new_sample_submission)} instead of {len(test_without_labels) * test_without_labels['seq_length']}."
    )


def prepare(raw: Path, public: Path, private: Path) -> None:
    old_train = pd.read_json(raw / "train.json", lines=True)
    old_test = pd.read_json(raw / "test.json", lines=True)
    old_sample_submission = pd.read_csv(raw / "sample_submission.csv")

    to_predict = ["reactivity", "deg_Mg_pH10", "deg_pH10", "deg_Mg_50C", "deg_50C"]
    test_size = 0.1
    n_test_samples = int(len(old_train) * test_size)

    # First split: Create the main train and test sets from the raw data
    # only put samples that pass the SN filter in the test set, as per comp data desc
    old_train["test"] = False
    test_indices = (
        old_train[old_train["SN_filter"] > 0].sample(n=n_test_samples, random_state=0).index
    )
    old_train.loc[test_indices, "test"] = True

    new_train = old_train[~old_train["test"]].copy().drop(columns=["test"])
    new_test = old_train[old_train["test"]].copy().drop(columns=["test"])

    # Generate the original competition files. This ensures the contents of `public`
    # and `private` directories remain identical to the original script's output.
    _create_competition_files(
        train_df=new_train,
        test_df=new_test,
        old_test_columns=old_test.columns,
        old_sample_submission=old_sample_submission,
        public_dir=public,
        private_dir=private,
        to_predict=to_predict,
    )

    # --- New: Create a validation set by splitting the training set further ---

    # Define new directories for the validation set, parallel to the original ones
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Second split: Create a new, smaller training set and a validation set.
    # The logic and size are replicated from the first split for consistency.
    val_split_base = new_train.copy()
    val_split_base["test"] = False
    val_test_indices = (
        val_split_base[val_split_base["SN_filter"] > 0]
        .sample(n=n_test_samples, random_state=0)  # Use same size and random state
        .index
    )
    val_split_base.loc[val_test_indices, "test"] = True

    train_val = val_split_base[~val_split_base["test"]].copy().drop(columns=["test"])
    test_val = val_split_base[val_split_base["test"]].copy().drop(columns=["test"])

    # Generate the validation competition files in the new directories.
    # The file structure and names inside public_val/private_val will mirror
    # the original public/private directories.
    _create_competition_files(
        train_df=train_val,
        test_df=test_val,
        old_test_columns=old_test.columns,
        old_sample_submission=old_sample_submission,
        public_dir=public_val,
        private_dir=private_val,
        to_predict=to_predict,
    )

    # Final sanity checks
    assert len(new_train) + len(new_test) == len(old_train), (
        f"Expected the length of the new train set plus the length of the new test set to be "
        f"equal to the length of the old train set, but got {len(new_train) + len(new_test)} "
        f"instead of {len(old_train)}."
    )
    assert len(train_val) + len(test_val) == len(new_train), (
        f"Expected the length of the validation train set plus the length of the validation test set to be "
        f"equal to the length of the main train set, but got {len(train_val) + len(test_val)} "
        f"instead of {len(new_train)}."
    )