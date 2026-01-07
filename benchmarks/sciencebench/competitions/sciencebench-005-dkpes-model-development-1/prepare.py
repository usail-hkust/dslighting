"""Data preparation for ScienceBench task 5 (DKPES model development)."""

from pathlib import Path
import shutil
import pandas as pd


def prepare(raw: Path, public: Path, private: Path) -> None:
    print("=" * 60)
    print("Preparing ScienceBench Task 5: DKPES model development")
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    if not raw.exists():
        raise FileNotFoundError(f"Raw dataset directory not found: {raw}")

    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(p for p in raw.glob("*.csv"))
    for csv_file in csv_files:
        shutil.copy2(csv_file, public / csv_file.name)
        print(f"✓ Copied {csv_file.name} to public directory")

    gold_path = Path("/path/to/ScienceAgent-bench/benchmark/eval_programs/gold_results/dkpes_test_gold.csv")
    if not gold_path.exists():
        raise FileNotFoundError(f"Gold labels not found at: {gold_path}")

    gold_df = pd.read_csv(gold_path)
    sample_df = gold_df[["index"]].copy()
    sample_df["Signal-inhibition"] = 0.0
    sample_df.to_csv(public / "sample_submission.csv", index=False)
    print("✓ Created sample_submission.csv with DKPES indices")

    gold_df.to_csv(private / "answer.csv", index=False)
    print("✓ Copied gold labels to private/answer.csv")

    print("Preparation complete.")


if __name__ == "__main__":
    raise SystemExit("Use via the benchmark preparation tooling.")
