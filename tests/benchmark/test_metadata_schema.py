from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from dslighting.benchmark.core.base import BaseBenchmark


class _DummyMetadataWriter:
    def __init__(self, tmp_path: Path) -> None:
        self.results_path = tmp_path / "results.csv"
        self.metadata_path = tmp_path / "metadata.json"
        self.mismatches_path = tmp_path / "mismatches.log"

    def _resolve_model_name_for_metadata(self, explicit_model_name=None):  # noqa: ANN001
        return explicit_model_name or "demo-model"


def test_metadata_json_uses_score_and_submissions_schema(tmp_path: Path) -> None:
    dummy = _DummyMetadataWriter(tmp_path)
    df = pd.DataFrame(
        [
            {
                "score": 1.0,
                "cost": 0.0,
                "running_time": 10.0,
                "input_tokens": 100,
                "output_tokens": 20,
                "total_tokens": 120,
                "submission_exists": True,
                "valid_submission": True,
            },
            {
                "score": 0.0,
                "cost": 0.0,
                "running_time": 20.0,
                "input_tokens": 200,
                "output_tokens": 30,
                "total_tokens": 230,
                "submission_exists": True,
                "valid_submission": True,
            },
            {
                "score": None,
                "cost": 0.0,
                "running_time": 30.0,
                "input_tokens": 300,
                "output_tokens": 40,
                "total_tokens": 340,
                "submission_exists": False,
                "valid_submission": False,
            },
        ]
    )

    BaseBenchmark._write_metadata_json(dummy, df, model_name="demo-model")

    payload = json.loads(dummy.metadata_path.read_text(encoding="utf-8"))
    assert "scores" not in payload

    assert payload["score"]["average"] == 0.5
    assert payload["score"]["actual_average"] == pytest.approx(1.0 / 3.0)
    assert payload["score"]["scored_task_count"] == 2
    assert payload["score"]["unscored_task_count"] == 1
    assert payload["score"]["median"] == 0.5
    assert payload["score"]["std"] == pytest.approx(0.70710678)

    assert payload["submissions"]["exists_count"] == 2
    assert payload["submissions"]["exists_rate"] == pytest.approx(2.0 / 3.0)
    assert payload["submissions"]["valid_count"] == 2
    assert payload["submissions"]["valid_rate"] == pytest.approx(2.0 / 3.0)
    assert payload["submissions"]["failed_submission_count"] == 1
    assert payload["submissions"]["failed_submission_rate"] == pytest.approx(1.0 / 3.0)
    assert payload["submissions"]["missing_submission_count"] == 1
    assert payload["submissions"]["missing_submission_rate"] == pytest.approx(1.0 / 3.0)
    assert payload["submissions"]["invalid_submission_count"] == 0
    assert payload["submissions"]["invalid_submission_rate"] == 0.0
