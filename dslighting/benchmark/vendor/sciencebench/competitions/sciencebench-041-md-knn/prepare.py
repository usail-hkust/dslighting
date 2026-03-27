"""Data preparation for ScienceBench Task 41 (MD KNN models)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

OUTPUT_FILES = ["MD_all_KNN.csv", "MD_MCNC_KNN.csv", "MD_MCLCNC_KNN.csv"]


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _default_dataset_dir() -> Path:
    root = Path(__file__).resolve().parents[5]
    return root / "ScienceAgent-bench" / "benchmark" / "datasets" / "dili_MD"


def _default_gold_path() -> Path:
    root = Path(__file__).resolve().parents[5]
    return root / "ScienceAgent-bench" / "benchmark" / "eval_programs" / "gold_results" / "MD_gold.csv"


def _write_sample_submission(path: Path) -> None:
    samples_dir = path / "sample_submission"
    samples_dir.mkdir(parents=True, exist_ok=True)
    sample_df = pd.DataFrame(
        {
            "standardised_smiles": ["SMILES_SAMPLE_1", "SMILES_SAMPLE_2"],
            "label": ["DILI", "NoDILI"],
        }
    )
    for filename in OUTPUT_FILES:
        sample_df.to_csv(samples_dir / filename, index=False)


def _write_answer(path: Path, gold_df: pd.DataFrame) -> None:
    answer_df = gold_df[["label"]].copy()
    answer_df.to_csv(path / "answer.csv", index=False)


def prepare(raw: Path, public: Path, private: Path) -> None:
    print("=" * 60)
    print("Preparing ScienceBench Task 41: MD KNN models")
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    _ensure_dir(public)
    _ensure_dir(private)

    data_dir = raw if raw.exists() else _default_dataset_dir()
    if not data_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {data_dir}")

    required_files = [
        data_dir / "mol_descriptors_training.csv",
        data_dir / "standardized_compounds_excl_ambiguous_cluster.csv",
        data_dir / "test.csv",
    ]
    missing = [str(f) for f in required_files if not f.exists()]
    if missing:
        raise FileNotFoundError("Missing dataset files: " + ", ".join(missing))

    for file_path in required_files:
        target = public / file_path.relative_to(data_dir.parent)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, target)
    print("✓ Copied descriptor training/test files to public directory")

    _write_sample_submission(public)
    print("✓ Wrote sample submission placeholders")

    gold_path = _default_gold_path()
    gold_df = pd.read_csv(gold_path)
    _write_answer(private, gold_df)
    print("✓ Wrote answer.csv")

    print("Preparation complete. Expected outputs:", ", ".join(f"pred_results/{name}" for name in OUTPUT_FILES))


if __name__ == "__main__":
    raise SystemExit("Use this module via the benchmark preparation tooling.")
