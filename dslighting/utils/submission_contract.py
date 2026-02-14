"""Utilities for unified submission-format contract detection.

This module centralizes submission-template discovery and @tag[...] contract
extraction so all workflows can reuse one consistent rule set.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

import numpy as np
import pandas as pd

TAG_PATTERN = re.compile(r"@([A-Za-z_][A-Za-z0-9_]*)\[([^\]]*)\]")
SUPPORTED_SUBMISSION_SUFFIXES = {
    ".csv",
    ".tsv",
    ".npy",
    ".jsonl",
    ".parquet",
    ".txt",
}


def _resolve_submission_path(raw_path: str, data_dir: Path) -> Optional[Path]:
    value = (raw_path or "").strip()
    if not value:
        return None

    candidate = Path(value).expanduser()
    candidates = [candidate]
    if not candidate.is_absolute():
        candidates.extend([
            data_dir / candidate,
            data_dir / candidate.name,
        ])

    for path_candidate in candidates:
        try:
            resolved = path_candidate.resolve()
        except Exception:
            resolved = path_candidate
        if resolved.exists() and resolved.is_file():
            return resolved
    return None


def find_sample_submission_file(
    data_dir: Path,
    *,
    sample_submission_path: str = "",
    submission_filename: str = "",
) -> Optional[Path]:
    """Locate sample submission file with metadata-first fallback heuristics."""
    explicit_path = _resolve_submission_path(sample_submission_path, data_dir)
    if explicit_path:
        return explicit_path

    preferred_name = (submission_filename or "").strip()
    if preferred_name:
        candidate = _resolve_submission_path(preferred_name, data_dir)
        if candidate:
            return candidate

    try:
        files = sorted((p for p in data_dir.iterdir() if p.is_file()), key=lambda p: p.name.lower())
    except Exception:
        return None

    def pick(predicate, *, allow_any_suffix: bool) -> Optional[Path]:
        for file in files:
            if not allow_any_suffix and file.suffix.lower() not in SUPPORTED_SUBMISSION_SUFFIXES:
                continue
            if predicate(file.name.lower()):
                return file
        return None

    name_predicates = [
        lambda name: "sample" in name and "submission" in name,
        lambda name: name.startswith("sample"),
        lambda name: "submission" in name,
        lambda name: "sample" in name,
        lambda name: "pred" in name,
    ]

    for allow_any_suffix in (False, True):
        for predicate in name_predicates:
            candidate = pick(predicate, allow_any_suffix=allow_any_suffix)
            if candidate:
                return candidate

    supported_files = [f for f in files if f.suffix.lower() in SUPPORTED_SUBMISSION_SUFFIXES]
    if len(supported_files) == 1:
        return supported_files[0]

    return None


def _extract_candidate_answer_values(sample_submission_file: Path) -> List[str]:
    suffix = sample_submission_file.suffix.lower()

    if suffix in {".csv", ".tsv"}:
        sep = "\t" if suffix == ".tsv" else ","
        df = pd.read_csv(sample_submission_file, sep=sep, nrows=2000)
        if df.empty:
            return []

        answer_column = None
        for col in df.columns:
            if str(col).strip().lower() == "answer":
                answer_column = col
                break

        if answer_column is not None:
            return [str(v).strip() for v in df[answer_column].dropna().tolist()[:50] if str(v).strip()]

        values: List[str] = []
        for _, row in df.head(50).iterrows():
            for value in row.tolist():
                text = str(value).strip()
                if text:
                    values.append(text)
        return values

    if suffix == ".jsonl":
        values = []
        with open(sample_submission_file, "r", encoding="utf-8", errors="ignore") as f:
            for _ in range(50):
                line = f.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                values.append(line)
                try:
                    parsed = json.loads(line)
                    if isinstance(parsed, dict):
                        answer_val = parsed.get("answer")
                        if answer_val is not None:
                            values.append(str(answer_val).strip())
                except json.JSONDecodeError:
                    pass
        return [v for v in values if v]

    if suffix == ".txt":
        return [line.strip() for line in sample_submission_file.read_text(encoding="utf-8", errors="ignore").splitlines()[:50] if line.strip()]

    if suffix == ".parquet":
        df = pd.read_parquet(sample_submission_file).head(50)
        if df.empty:
            return []
        answer_column = None
        for col in df.columns:
            if str(col).strip().lower() == "answer":
                answer_column = col
                break
        if answer_column is not None:
            return [str(v).strip() for v in df[answer_column].dropna().tolist()[:50] if str(v).strip()]
        values: List[str] = []
        for _, row in df.iterrows():
            for value in row.tolist():
                text = str(value).strip()
                if text:
                    values.append(text)
        return values

    if suffix == ".npy":
        try:
            arr = np.load(sample_submission_file, mmap_mode="r", allow_pickle=False)
        except ValueError:
            arr = np.load(sample_submission_file, mmap_mode="r", allow_pickle=True)
        preview = arr.reshape(-1)[:20].tolist() if getattr(arr, "size", 0) else []
        return [str(v).strip() for v in preview if str(v).strip()]

    return []


def extract_submission_tag_contract(sample_submission_file: Optional[Path]) -> Dict[str, Any]:
    """Extract tagged-answer contract from sample submission values.

    Returns a normalized dictionary used by TaskContext/DataAnalyzer prompts.
    """
    if sample_submission_file is None:
        return {
            "sample_submission_file": "",
            "tag_wrapper_required": False,
            "required_tags": [],
            "forbidden_tags": [],
            "tag_example": "",
        }

    try:
        values = _extract_candidate_answer_values(sample_submission_file)
    except Exception:
        values = []

    ordered_tags: List[str] = []
    seen = set()
    placeholder_detected = False
    tag_example = ""

    for value in values:
        matches = TAG_PATTERN.findall(value)
        if matches and not tag_example:
            tag_example = value
        for tag_key, _ in matches:
            lowered = tag_key.lower()
            if lowered == "placeholder":
                placeholder_detected = True
                continue
            if lowered not in seen:
                seen.add(lowered)
                ordered_tags.append(tag_key)

    # Even if only placeholder tags are present, this still means tagged syntax
    # is part of the template contract and must be preserved.
    tag_wrapper_required = bool(ordered_tags or placeholder_detected)
    forbidden_tags = ["placeholder"] if tag_wrapper_required or placeholder_detected else []

    return {
        "sample_submission_file": str(sample_submission_file),
        "tag_wrapper_required": tag_wrapper_required,
        "required_tags": ordered_tags,
        "forbidden_tags": forbidden_tags,
        "tag_example": tag_example,
    }


def normalize_submission_tag_contract(raw_contract: Any) -> Dict[str, Any]:
    """Normalize an externally provided submission contract payload."""
    if not isinstance(raw_contract, Mapping):
        return {}

    required_tags = raw_contract.get("required_tags")
    if not isinstance(required_tags, list):
        required_tags = []
    required_tags = [str(tag).strip() for tag in required_tags if str(tag).strip()]

    forbidden_tags = raw_contract.get("forbidden_tags")
    if not isinstance(forbidden_tags, list):
        forbidden_tags = []
    forbidden_tags = [str(tag).strip() for tag in forbidden_tags if str(tag).strip()]

    return {
        "sample_submission_file": str(raw_contract.get("sample_submission_file", "") or ""),
        "tag_wrapper_required": bool(raw_contract.get("tag_wrapper_required", False)),
        "required_tags": required_tags,
        "forbidden_tags": forbidden_tags,
        "tag_example": str(raw_contract.get("tag_example", "") or ""),
    }


def build_tag_contract_reminder(contract: Mapping[str, Any]) -> str:
    """Build a standardized reminder block when @tag[...] is required."""
    if not isinstance(contract, Mapping):
        return ""

    if not bool(contract.get("tag_wrapper_required", False)):
        return ""

    required_tags = contract.get("required_tags") or []
    tag_list = ", ".join(str(tag) for tag in required_tags) if required_tags else "(detected from template)"
    sample_name = Path(str(contract.get("sample_submission_file") or "sample_submission")).name
    example = str(contract.get("tag_example") or "").strip()

    lines = [
        "**UNIFIED TAGGED SUBMISSION CONTRACT (MANDATORY):**",
        f"- Template source: `{sample_name}`",
        "- The submission answer MUST preserve `@tag[...]` wrappers.",
        f"- Required tag keys: `{tag_list}`",
        "- Forbidden placeholder tags: `@placeholder[...]`",
        "- Do NOT output bare values when tagged format is required.",
    ]
    if example:
        lines.append(f"- Template example: `{example}`")

    return "\n".join(lines)


__all__ = [
    "TAG_PATTERN",
    "find_sample_submission_file",
    "extract_submission_tag_contract",
    "normalize_submission_tag_contract",
    "build_tag_contract_reminder",
]
