"""Data preparation for ScienceBench Task 3 (predict bulk modulus)."""

from pathlib import Path
import shutil
import pandas as pd

SOURCE_DATA_DIR = Path("/path/to/ScienceAgent-bench/benchmark/datasets/crystalline_compound")
TRAIN_FILE = SOURCE_DATA_DIR / "compound_elastic_properties_train.csv"
TEST_FILE = SOURCE_DATA_DIR / "compound_elastic_properties_test.csv"
GOLD_FILE = Path("/path/to/ScienceAgent-bench/benchmark/eval_programs/gold_results/compound_elastic_properties_gold.csv")


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _make_sample_submission(answer_df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "material_id": answer_df["material_id"],
        "K_VRH": 0.0,
    })


def prepare(raw: Path, public: Path, private: Path) -> None:
    print("=" * 60)
    print("Preparing ScienceBench Task 3: predict bulk modulus")
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    _ensure_dir(public)
    _ensure_dir(private)

    if not TRAIN_FILE.exists() or not TEST_FILE.exists():
        raise FileNotFoundError("Expected crystalline_compound dataset is missing.")

    shutil.copy2(TRAIN_FILE, public / TRAIN_FILE.name)
    shutil.copy2(TEST_FILE, public / TEST_FILE.name)
    print("✓ Copied training and test CSV files to public directory")

    if not GOLD_FILE.exists():
        raise FileNotFoundError(f"Gold results not found at {GOLD_FILE}")

    gold_df = pd.read_csv(GOLD_FILE)
    answer_df = gold_df[["material_id", "K_VRH"]].copy()
    answer_df.to_csv(private / "answer.csv", index=False)
    print("✓ Wrote answer.csv with gold material IDs and K_VRH")

    sample_df = _make_sample_submission(answer_df)
    sample_df.to_csv(public / "sample_submission.csv", index=False)
    print("✓ Wrote sample_submission.csv placeholder")

    print("Data preparation completed.")


if __name__ == "__main__":
    raise SystemExit("Use this module via the benchmark preparation tooling.")
