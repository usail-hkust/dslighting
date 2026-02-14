"""Data preparation for ScienceBench Task 40 (MD RF models)."""

from pathlib import Path
import shutil
import pandas as pd

DATA_DIR = Path("/path/to/ScienceAgent-bench/benchmark/datasets/dili_MD")
GOLD_PATH = Path("/path/to/ScienceAgent-bench/benchmark/eval_programs/gold_results/MD_gold.csv")
OUTPUT_FILES = ["MD_all_RF.csv", "MD_MCNC_RF.csv", "MD_MCLCNC_RF.csv"]


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_sample_submission(path: Path) -> None:
    samples_dir = path / "sample_submission"
    samples_dir.mkdir(parents=True, exist_ok=True)
    sample_df = pd.DataFrame(
        {
            "standardised_smiles": ["CCO", "CCN", "CCC"],
            "label": ["DILI", "NoDILI", "DILI"],
        }
    )
    for filename in OUTPUT_FILES:
        sample_df.to_csv(samples_dir / filename, index=False)


def _write_answer(path: Path, gold_df: pd.DataFrame) -> None:
    answer_df = gold_df[["label"]].copy()
    answer_df.to_csv(path / "answer.csv", index=False)


def prepare(raw: Path, public: Path, private: Path) -> None:
    print("=" * 60)
    print("Preparing ScienceBench Task 40: MD RF models")
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    _ensure_dir(public)
    _ensure_dir(private)

    required_files = [
        DATA_DIR / "mol_descriptors_training.csv",
        DATA_DIR / "standardized_compounds_excl_ambiguous_cluster.csv",
        DATA_DIR / "test.csv",
    ]
    missing = [str(f) for f in required_files if not f.exists()]
    if missing:
        raise FileNotFoundError("Missing dataset files: " + ", ".join(missing))

    for file_path in required_files:
        target = public / file_path.relative_to(DATA_DIR.parent)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, target)
    print("✓ Copied descriptor training/test files to public directory")

    _write_sample_submission(public)
    print("✓ Wrote sample submission placeholders")

    gold_df = pd.read_csv(GOLD_PATH)
    _write_answer(private, gold_df)
    print("✓ Wrote answer.csv")

    print("Preparation complete. Expected outputs:", ", ".join(f"pred_results/{name}" for name in OUTPUT_FILES))


if __name__ == "__main__":
    raise SystemExit("Use this module via the benchmark preparation tooling.")
