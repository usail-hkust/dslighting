"""
Data preparation for ScienceBench Task 2: mat_feature_select
"""

from pathlib import Path
import shutil
import pandas as pd


SOURCE_DATA_FILE = "diffusion_data_nofeatures_new.xlsx"
GOLD_FILE = "answer.csv"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _build_sample_submission(gold_df: pd.DataFrame) -> pd.DataFrame:
    sample = gold_df.copy()
    for column in sample.columns:
        if pd.api.types.is_numeric_dtype(sample[column]):
            sample[column] = 0
        else:
            sample[column] = ""
    return sample


def prepare(raw: Path, public: Path, private: Path) -> None:
    """Prepare data for ScienceBench Task 2."""
    print("=" * 60)
    print("Preparing ScienceBench Task 2: mat_feature_select")
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    _ensure_dir(public)
    _ensure_dir(private)

    source_path = raw / SOURCE_DATA_FILE
    gold_path = raw / GOLD_FILE

    if not source_path.exists():
        raise FileNotFoundError(f"Expected source dataset at {source_path}")

    dataset_target = public / SOURCE_DATA_FILE
    shutil.copy2(source_path, dataset_target)
    print(f"✓ Copied dataset to public: {dataset_target.name}")

    if not gold_path.exists():
        raise FileNotFoundError(f"Expected gold results at {gold_path}")

    gold_df = pd.read_csv(gold_path)
    gold_df.to_csv(private / "answer.csv", index=False)
    print("✓ Wrote answer.csv with gold features")

    sample_df = _build_sample_submission(gold_df)
    sample_df.to_csv(public / "sample_submission.csv", index=False)
    print("✓ Wrote sample_submission.csv")

    print("Data preparation completed.")


if __name__ == "__main__":
    raise SystemExit("This module is intended for import by preparation utilities, not direct execution.")

