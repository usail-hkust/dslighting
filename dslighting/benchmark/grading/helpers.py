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
    return pd.read_csv(request.references.answers_path, **kwargs)


def read_private_csv(request: GradingRequest, name: str, **kwargs: Any) -> pd.DataFrame:
    return pd.read_csv(request.references.private_dir / name, **kwargs)


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
