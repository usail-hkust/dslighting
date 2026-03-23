from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dslighting.benchmark.grading.errors import SubmissionValidationError
from dslighting.benchmark.grading.models import GradingRequest


def require_submission_file(request: GradingRequest) -> Path:
    path = request.submission.root
    if request.submission.kind != "file" or not path.is_file():
        raise SubmissionValidationError(f"Expected a submission file, got: {path}")
    return path


def require_submission_dir(request: GradingRequest) -> Path:
    path = request.submission.root
    if request.submission.kind != "directory" or not path.is_dir():
        raise SubmissionValidationError(f"Expected a submission directory, got: {path}")
    return path


def read_submission_csv(request: GradingRequest, **kwargs: Any) -> pd.DataFrame:
    return pd.read_csv(require_submission_file(request), **kwargs)


def read_answers_csv(request: GradingRequest, **kwargs: Any) -> pd.DataFrame:
    if request.references.answers_path is None:
        raise SubmissionValidationError("No single answers_path configured for this task.")
    return pd.read_csv(request.references.answers_path, **kwargs)


def read_private_csv(request: GradingRequest, name: str, **kwargs: Any) -> pd.DataFrame:
    return pd.read_csv(request.references.private_dir / name, **kwargs)


def iter_submission_entries(request: GradingRequest) -> list[Path]:
    root = require_submission_dir(request)
    if request.submission.entries:
        return [root / entry.relative_path for entry in request.submission.entries]
    return sorted(child for child in root.iterdir())


def submission_child_path(request: GradingRequest, name: str) -> Path:
    path = require_submission_dir(request) / name
    if not path.exists():
        raise SubmissionValidationError(f"Expected submission child '{name}' not found in {request.submission.root}")
    return path


def reference_child_path(request: GradingRequest, name: str) -> Path:
    base = request.references.answers_root or request.references.private_dir
    path = base / name
    if not path.exists():
        raise SubmissionValidationError(f"Expected reference child '{name}' not found in {base}")
    return path


def read_submission_child_csv(request: GradingRequest, name: str, **kwargs: Any) -> pd.DataFrame:
    return pd.read_csv(submission_child_path(request, name), **kwargs)


def read_submission_child_json(request: GradingRequest, name: str) -> Any:
    with open(submission_child_path(request, name), "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_reference_child_csv(request: GradingRequest, name: str, **kwargs: Any) -> pd.DataFrame:
    return pd.read_csv(reference_child_path(request, name), **kwargs)


def read_reference_child_json(request: GradingRequest, name: str) -> Any:
    with open(reference_child_path(request, name), "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_artifact(path: Path) -> Any:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix == ".jsonl":
        records: list[Any] = []
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records
    if suffix == ".npy":
        return np.load(path, allow_pickle=True)
    return path
