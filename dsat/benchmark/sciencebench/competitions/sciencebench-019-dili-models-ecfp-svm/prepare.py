"""Data preparation for ScienceBench Task 19 (DILI SVM models)."""

from pathlib import Path
import shutil
import pandas as pd

DATA_DIR = Path("/path/to/ScienceAgent-bench/benchmark/datasets/dili")
GOLD_PATH = Path("/path/to/ScienceAgent-bench/benchmark/eval_programs/gold_results/test_DILI_gold.csv")
OUTPUT_FILE = "test_DILI_predictions.csv"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_sample_submission(path: Path, gold_df: pd.DataFrame) -> None:
    sample_df = gold_df[["standardised_smiles"]].copy()
    sample_df["label"] = "DILI"
    sample_df.to_csv(path / "sample_submission.csv", index=False)


def _write_answer(path: Path, gold_df: pd.DataFrame) -> None:
    answer_df = gold_df[["standardised_smiles", "label"]].copy()
    answer_df.to_csv(path / "answer.csv", index=False)


def prepare(raw: Path, public: Path, private: Path) -> None:
    print("=" * 60)
    print("Preparing ScienceBench Task 19: DILI SVM models")
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    _ensure_dir(public)
    _ensure_dir(private)

    required_files = [DATA_DIR / "train.csv", DATA_DIR / "test.csv"]
    missing = [str(f) for f in required_files if not f.exists()]
    if missing:
        raise FileNotFoundError("Missing dataset files: " + ", ".join(missing))

    for file_path in required_files:
        target = public / file_path.relative_to(DATA_DIR.parent)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, target)
    print("✓ Copied DILI train/test CSV files to public directory")

    gold_df = pd.read_csv(GOLD_PATH)
    _write_sample_submission(public, gold_df)
    print("✓ Wrote sample_submission.csv")

    _write_answer(private, gold_df)
    print("✓ Wrote answer.csv")

    print(f"Preparation complete. Expected output: pred_results/{OUTPUT_FILE}")


if __name__ == "__main__":
    raise SystemExit("Use this module via the benchmark preparation tooling.")
