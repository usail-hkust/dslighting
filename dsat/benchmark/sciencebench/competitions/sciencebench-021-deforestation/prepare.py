"""Prepare deforestation data for ScienceBench Task 21."""

from __future__ import annotations

from pathlib import Path
import shutil
import pandas as pd


DATASET_ROOT = Path("/path/to/ScienceAgent-bench/benchmark/datasets/deforestation")
GOLD_FILE = Path("/path/to/ScienceAgent-bench/benchmark/eval_programs/gold_results/deforestation_rate_gold.csv")
EXPECTED_OUTPUT = "deforestation_rate.csv"


def _ensure(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _copy_dataset(dataset_root: Path, target_root: Path) -> int:
    if not dataset_root.exists():
        raise FileNotFoundError(f"Source dataset not found: {dataset_root}")

    copied = 0
    for item in dataset_root.rglob("*"):
        if not item.is_file() or item.name.startswith("."):
            continue
        rel = item.relative_to(dataset_root)
        dest = target_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, dest)
        copied += 1
        if copied <= 10:
            print(f"  ✓ Copied: {rel}")
    if copied > 10:
        print(f"  ... and {copied - 10} more files")
    return copied


def _write_sample_submission(public_dir: Path, gold_df: pd.DataFrame) -> None:
    sample_df = gold_df.copy()
    sample_df["percentage_deforestation"] = 0.0
    sample_df.to_csv(public_dir / "sample_submission.csv", index=False)
    print("✓ Created sample_submission.csv")


def _write_answers(private_dir: Path, gold_df: pd.DataFrame) -> None:
    gold_df.to_csv(private_dir / "answer.csv", index=False)
    print("✓ Created answer.csv")


def prepare(raw: Path, public: Path, private: Path) -> None:
    print("=" * 60)
    print("Preparing ScienceBench Task 21: deforestation analysis")
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    _ensure(public)
    _ensure(private)

    dataset_root = raw if raw.exists() and any(raw.iterdir()) else DATASET_ROOT
    if dataset_root is DATASET_ROOT:
        print(f"⚠ Raw directory missing or empty. Using canonical dataset: {DATASET_ROOT}")
    else:
        print("✓ Using provided raw dataset directory.")

    total_copied = _copy_dataset(dataset_root, public)
    print(f"  Total files copied: {total_copied}")

    if not GOLD_FILE.exists():
        raise FileNotFoundError(f"Gold file missing: {GOLD_FILE}")
    gold_df = pd.read_csv(GOLD_FILE)

    _write_sample_submission(public, gold_df)
    _write_answers(private, gold_df)

    print(f"\nData preparation completed. Expected output: pred_results/{EXPECTED_OUTPUT}")


if __name__ == "__main__":
    raise SystemExit("Use via the benchmark preparation tooling.")
