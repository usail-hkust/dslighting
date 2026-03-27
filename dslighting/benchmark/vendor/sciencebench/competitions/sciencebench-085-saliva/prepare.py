"""
Data preparation for ScienceBench task 85 (BiopSyKit saliva analysis).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

DATASET_NAME = "saliva_data"
PRED_FILENAME = "saliva_pred.json"
GOLD_FILENAME = "biopsykit_saliva_gold.json"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _dataset_dir() -> Path:
    return _repo_root() / "ScienceAgent-bench" / "benchmark" / "datasets" / DATASET_NAME


def _gold_path() -> Path:
    return _repo_root() / "ScienceAgent-bench" / "benchmark" / "eval_programs" / "gold_results" / GOLD_FILENAME


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _copy_dataset(src: Path, public: Path) -> None:
    dest_root = public / DATASET_NAME
    copied = 0
    for item in src.rglob("*"):
        if not item.is_file():
            continue
        rel = item.relative_to(src)
        target = dest_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        copied += 1
    print(f"✓ Copied {copied} dataset file(s) to {dest_root}")


def _placeholder_like(gold: dict) -> dict:
    def _convert(value):
        if isinstance(value, dict):
            return {k: _convert(v) for k, v in value.items()}
        if isinstance(value, float):
            return 0.0
        return value

    return {subject: _convert(payload) for subject, payload in gold.items()}


def prepare(raw: Path, public: Path, private: Path) -> None:
    print("=" * 60)
    print("Preparing ScienceBench Task 85")
    print("Dataset:", DATASET_NAME)
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    source_dir = raw if raw.exists() else _dataset_dir()
    if not source_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {source_dir}")

    gold_path = _gold_path()
    if not gold_path.exists():
        raise FileNotFoundError(f"Gold JSON not found: {gold_path}")

    _ensure_dir(public)
    _ensure_dir(private)

    _copy_dataset(source_dir, public)

    with gold_path.open("r", encoding="utf-8") as handle:
        gold_dict = json.load(handle)

    sample_dict = _placeholder_like(gold_dict)
    sample_path = public / "sample_submission.json"
    sample_path.write_text(json.dumps(sample_dict, indent=2), encoding="utf-8")
    print("✓ Created sample_submission.json")

    private_answer = private / "answer.json"
    private_answer.write_text(json.dumps(gold_dict, indent=2), encoding="utf-8")
    print("✓ Stored gold JSON for reference")

    shutil.copy2(gold_path, private / gold_path.name)
    print("✓ Copied gold JSON file")

    instructions = (
        f"Expected output path: pred_results/{PRED_FILENAME}\n"
        "Format: nested JSON with subject keys mapping to statistics.\n"
        "Numeric fields should be floats.\n"
    )
    (private / "metadata.txt").write_text(instructions, encoding="utf-8")
    print("✓ Wrote metadata.txt")

    print("Data preparation completed.")
