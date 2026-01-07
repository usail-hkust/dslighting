"""Data preparation for ScienceBench Task 13 (HIV property prediction)."""

from pathlib import Path
import shutil
import pandas as pd

DATA_DIR = Path("/path/to/ScienceAgent-bench/benchmark/datasets/hiv")
OUTPUT_FILENAME = "pred_results/hiv_test_pred.csv"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_sample_submission(path: Path) -> None:
    sample_df = pd.DataFrame({
        "smiles": ["SMILES_SAMPLE"],
        "HIV_active": [0],
    })
    sample_df.to_csv(path / "sample_submission.csv", index=False)


def _write_answer(path: Path, gold_df: pd.DataFrame) -> None:
    answer_df = gold_df[["smiles", "HIV_active"]].copy()
    answer_df.to_csv(path / "answer.csv", index=False)


def prepare(raw: Path, public: Path, private: Path) -> None:
    print("=" * 60)
    print("Preparing ScienceBench Task 13: HIV property prediction")
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    _ensure_dir(public)
    _ensure_dir(private)

    required_files = [
        DATA_DIR / "HIV_train.csv",
        DATA_DIR / "HIV_dev.csv",
        DATA_DIR / "HIV_test.csv",
        DATA_DIR / "HIV_README",
    ]
    missing = [str(f) for f in required_files if not f.exists()]
    if missing:
        raise FileNotFoundError("Missing dataset files: " + ", ".join(missing))

    for file_path in required_files:
        target = public / file_path.relative_to(DATA_DIR.parent)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, target)
    print("✓ Copied HIV dataset files to public directory")

    _write_sample_submission(public)
    print("✓ Wrote sample_submission.csv")

    gold_path = Path("/path/to/ScienceAgent-bench/benchmark/eval_programs/gold_results/HIV_gold.csv")
    gold_df = pd.read_csv(gold_path)
    _write_answer(private, gold_df)
    print("✓ Wrote answer.csv")

    print("Preparation complete. Expected submission file:", OUTPUT_FILENAME)


if __name__ == "__main__":
    raise SystemExit("Use this module via the benchmark preparation tooling.")
