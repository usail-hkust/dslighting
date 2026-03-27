"""Prepare data for ScienceBench task 16 (compound filter)."""

from __future__ import annotations

from pathlib import Path
import shutil
import pandas as pd

DATASET_ROOT = None  # set inside prepare()
GOLD_FILE = None  # set inside prepare()
EXPECTED_OUTPUT = "compound_filter_results.txt"


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


def _write_sample_submission(public_dir: Path) -> None:
    sample_lines = [
        "# One SMILES per line, in the order you wish to submit.",
        "SMILES_PLACEHOLDER_1",
        "SMILES_PLACEHOLDER_2",
        "SMILES_PLACEHOLDER_3",
    ]
    sample_path = public_dir / "sample_submission.txt"
    sample_path.write_text("\n".join(sample_lines) + "\n", encoding="utf-8")
    print(f"✓ Created {sample_path.name}")


def _write_answers(private_dir: Path) -> None:
    if not GOLD_FILE.exists():
        raise FileNotFoundError(f"Gold file missing: {GOLD_FILE}")
    gold_text = GOLD_FILE.read_text(encoding="utf-8")

    answer_txt = private_dir / EXPECTED_OUTPUT
    answer_txt.write_text(gold_text, encoding="utf-8")

    smiles = [line.strip() for line in gold_text.splitlines() if line.strip()]
    answer_csv = private_dir / "answer.csv"
    pd.DataFrame({"SMILES": smiles}).to_csv(answer_csv, index=False)

    print(f"✓ Copied gold results to {answer_txt.name}")
    print(f"✓ Created answer.csv with {len(smiles)} rows")


def prepare(raw: Path, public: Path, private: Path) -> None:
    global DATASET_ROOT, GOLD_FILE
    DATASET_ROOT = raw / "compound_filter"
    GOLD_FILE = raw / "antibioticsai_filter_gold_results.txt"
    print("=" * 60)
    print("Preparing ScienceBench Task 16: compound filter")
    print("=" * 60)
    print(f"Raw directory: {raw}")
    print(f"Public directory: {public}")
    print(f"Private directory: {private}")

    _ensure(public)
    _ensure(private)

    dataset_root = raw if raw.exists() and any(raw.iterdir()) else DATASET_ROOT
    if dataset_root is DATASET_ROOT:
        print(f"⚠ Raw directory missing or empty. Using canonical dataset: {DATASET_ROOT}")
    else:
        print("✓ Using provided raw dataset directory.")

    total_copied = _copy_dataset(dataset_root, public)
    print(f"  Total files copied: {total_copied}")

    _write_sample_submission(public)
    _write_answers(private)

    print("\nData preparation completed.")
    print(f"  Expected submission file: pred_results/{EXPECTED_OUTPUT}")


if __name__ == "__main__":
    raise SystemExit("Use via the benchmark preparation tooling.")
