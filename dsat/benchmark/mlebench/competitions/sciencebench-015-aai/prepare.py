"""Prepare data for ScienceBench task 15 (admet_ai)."""

from __future__ import annotations

from pathlib import Path
import shutil
import pandas as pd


DATASET_ROOT = Path("/path/to/ScienceAgent-bench/benchmark/datasets/ames")
GOLD_FILE = Path("/path/to/ScienceAgent-bench/benchmark/eval_programs/gold_results/admet_ai_gold.csv")
EXPECTED_OUTPUT = "aai_preds.csv"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _copy_dataset(dataset_root: Path, target_root: Path) -> int:
    """Copy the Ames dataset into the public directory."""
    if not dataset_root.exists():
        raise FileNotFoundError(f"Source dataset not found: {dataset_root}")

    copied = 0
    for item in dataset_root.rglob("*"):
        if not item.is_file() or item.name.startswith("."):
            continue
        relative = item.relative_to(dataset_root)
        destination = target_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, destination)
        copied += 1
        if copied <= 10:
            print(f"  ✓ Copied: {relative}")
    if copied > 10:
        print(f"  ... and {copied - 10} more files")
    return copied


def _write_sample_submission(dataset_root: Path, public_dir: Path) -> None:
    """Build a sample submission aligned with the gold file schema."""
    test_path = dataset_root / "test.csv"
    if not test_path.exists():
        raise FileNotFoundError(f"Test file not found at {test_path}")

    test_df = pd.read_csv(test_path, index_col=0)
    sample_df = test_df[["Drug_ID", "Drug"]].copy()
    sample_df["Y"] = 0.5  # Placeholder probability
    sample_path = public_dir / "sample_submission.csv"
    sample_df.to_csv(sample_path, index=False)
    print(f"✓ Created {sample_path.name} with {len(sample_df)} rows")


def _write_answers(private_dir: Path) -> None:
    """Copy the gold answers used by the grader."""
    if not GOLD_FILE.exists():
        raise FileNotFoundError(f"Gold file missing: {GOLD_FILE}")
    gold_df = pd.read_csv(GOLD_FILE)
    first_col = gold_df.columns[0]
    if first_col.startswith("Unnamed"):
        gold_df = gold_df.drop(columns=[first_col])
    answer_path = private_dir / "answer.csv"
    gold_df.to_csv(answer_path, index=False)
    print(f"✓ Copied answer.csv with {len(gold_df)} rows")


def prepare(raw: Path, public: Path, private: Path) -> None:
    """
    Stage the Ames mutagenicity dataset for ScienceBench task 15.

    Args:
        raw: Optional pre-staged dataset directory. If empty, the canonical dataset is used.
        public: Directory exposed to participants.
        private: Directory used internally for grading.
    """
    print("=" * 60)
    print("Preparing ScienceBench Task 15: admet_ai")
    print("=" * 60)
    print(f"Raw directory: {raw}")
    print(f"Public directory: {public}")
    print(f"Private directory: {private}")

    _ensure_dir(public)
    _ensure_dir(private)

    dataset_root = raw if raw.exists() and any(raw.iterdir()) else DATASET_ROOT
    if dataset_root is not DATASET_ROOT:
        print("✓ Using provided raw dataset directory.")
    else:
        print(f"⚠ Raw directory missing or empty. Using canonical dataset: {DATASET_ROOT}")

    total_copied = _copy_dataset(dataset_root, public)
    print(f"  Total files copied: {total_copied}")

    _write_sample_submission(dataset_root, public)
    _write_answers(private)

    print(f"\nData preparation completed. Expected submission file: pred_results/{EXPECTED_OUTPUT}")


if __name__ == "__main__":
    raise SystemExit("Use via the benchmark preparation tooling.")
