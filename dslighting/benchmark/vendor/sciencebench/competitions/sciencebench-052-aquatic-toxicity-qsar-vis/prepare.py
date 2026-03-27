"""
Data preparation for ScienceBench task 52
Dataset: aquatic_toxicity
"""

from __future__ import annotations

import base64
import shutil
from pathlib import Path

import pandas as pd

EXPECTED_FILENAME = "aquatic_toxicity_qsar_vis.png"


def _dataset_dir() -> Path:
    root = Path(__file__).resolve().parents[5]
    return root / "ScienceAgent-bench" / "benchmark" / "datasets" / "aquatic_toxicity"


def _gold_path() -> Path:
    root = Path(__file__).resolve().parents[5]
    return root / "ScienceAgent-bench" / "benchmark" / "eval_programs" / "gold_results" / "aquatic_toxicity_qsar_vis_gold.png"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def prepare(raw: Path, public: Path, private: Path) -> None:
    print("=" * 60)
    print("Preparing ScienceBench Task 52")
    print("Dataset: aquatic_toxicity")
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    data_dir = raw if raw.exists() else _dataset_dir()
    if not data_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {data_dir}")

    _ensure_dir(public)
    _ensure_dir(private)

    required = [
        data_dir / "Tetrahymena_pyriformis_OCHEM.sdf",
        data_dir / "Tetrahymena_pyriformis_OCHEM_test_ex.sdf",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing dataset files: " + ", ".join(missing))

    for path in required:
        target = public / path.relative_to(data_dir.parent)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    print("✓ Copied aquatic toxicity SDF files")

    sample_df = pd.DataFrame([{"file_name": EXPECTED_FILENAME, "image_base64": ""}])
    sample_df.to_csv(public / "sample_submission.csv", index=False)
    print("✓ Created sample_submission.csv")

    gold_path = _gold_path()
    if not gold_path.exists():
        raise FileNotFoundError(f"Gold image not found: {gold_path}")
    encoded = base64.b64encode(gold_path.read_bytes()).decode("utf-8")
    answer_df = pd.DataFrame([{"file_name": EXPECTED_FILENAME, "image_base64": encoded}])
    answer_df.to_csv(private / "answer.csv", index=False)
    shutil.copy2(gold_path, private / gold_path.name)
    print("✓ Created answer.csv and copied gold image")

    print("Aquatic toxicity visualization task preparation complete")


if __name__ == "__main__":
    raise SystemExit("Use this module via the benchmark preparation tooling.")
