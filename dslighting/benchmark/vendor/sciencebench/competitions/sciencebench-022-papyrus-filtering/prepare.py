"""Data preparation for ScienceBench Task 22 (Papyrus filtering)."""

from __future__ import annotations

from pathlib import Path
import shutil
import pandas as pd

DATA_DIR = None  # set inside prepare()
SOURCE_FILES = None  # set inside prepare()
GOLD_PATH = None  # set inside prepare()
EXPECTED_OUTPUT = "papyrus_filtered.pkl"


def _ensure(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _copy_sources(target_dir: Path) -> None:
    missing = [str(f) for f in SOURCE_FILES if not f.exists()]
    if missing:
        raise FileNotFoundError("Missing dataset files: " + ", ".join(missing))

    for file_path in SOURCE_FILES:
        dest = target_dir / file_path.relative_to(DATA_DIR.parent)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, dest)
        print(f"  ✓ Copied: {file_path.name}")


def _write_sample_submission(public_dir: Path, gold_df: pd.DataFrame) -> None:
    sample_df = gold_df.head(min(5, len(gold_df))).reset_index(drop=True)
    sample_path = public_dir / "sample_submission.pkl"
    sample_df.to_pickle(sample_path)
    print(f"✓ Wrote sample_submission.pkl with {len(sample_df)} rows")

    readme_path = public_dir / "sample_submission.txt"
    readme_path.write_text(
        "Create pred_results/papyrus_filtered.pkl as a pickled pandas DataFrame matching the gold schema.\n",
        encoding="utf-8",
    )
    print("✓ Added sample_submission.txt instructions")


def _write_private_artifacts(private_dir: Path, gold_df: pd.DataFrame) -> None:
    summary = {
        "rows": [len(gold_df)],
        "columns": [len(gold_df.columns)],
    }
    pd.DataFrame(summary).to_csv(private_dir / "answer_summary.csv", index=False)
    gold_df.to_pickle(private_dir / "answer.pkl")
    print("✓ Wrote answer_summary.csv and answer.pkl")


def prepare(raw: Path, public: Path, private: Path) -> None:
    global DATA_DIR, SOURCE_FILES, GOLD_PATH
    DATA_DIR = raw / "papyrus"
    SOURCE_FILES = [     DATA_DIR / "papyrus_unfiltered.pkl",     DATA_DIR / "papyrus_protein_set.pkl", ]
    GOLD_PATH = raw / "papyrus_filtered_gold.pkl"
    print("=" * 60)
    print("Preparing ScienceBench Task 22: Papyrus filtering")
    print("=" * 60)
    print("Public directory:", public)
    print("Private directory:", private)

    _ensure(public)
    _ensure(private)

    dataset_root = raw if raw.exists() and any(raw.iterdir()) else DATA_DIR
    if dataset_root is DATA_DIR:
        print(f"⚠ Raw directory missing or empty. Using canonical dataset: {DATA_DIR}")
    else:
        print("✓ Using provided raw dataset directory.")

    _copy_sources(public)

    gold_df = pd.read_pickle(GOLD_PATH)
    _write_sample_submission(public, gold_df)
    _write_private_artifacts(private, gold_df)


    print(f"\nData preparation completed. Expected output: pred_results/{EXPECTED_OUTPUT}")

if __name__ == "__main__":
    raise SystemExit("Use this module via the benchmark preparation tooling.")
