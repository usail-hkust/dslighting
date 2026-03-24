from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from dslighting.benchmark.grading.errors import SubmissionValidationError
from dslighting.benchmark.grading.models import (
    GradingContext,
    GradingRequest,
    ReferenceArtifacts,
    SubmissionArtifact,
)
from dslighting.benchmark.grading.plot_artifact import (
    compare_color_field,
    compare_plot_key,
    grade_plot_submission,
)


def _write_png(path: Path, color: tuple[int, int, int]) -> None:
    Image.new("RGB", (4, 4), color=color).save(path)


def _write_plot_json(path: Path, *, color: object) -> None:
    payload = {
        "type": "bar",
        "color": color,
        "figsize": [8, 6],
        "graph_title": "Example Plot",
        "legend_title": "",
        "labels": [],
        "x_label": "Category",
        "y_label": "Value",
        "xtick_labels": ["A", "B"],
        "ytick_labels": ["0", "1"],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _build_request(tmp_path: Path) -> GradingRequest:
    submission_dir = tmp_path / "submission"
    reference_dir = tmp_path / "reference"
    public_dir = tmp_path / "public"
    raw_dir = tmp_path / "raw"
    for path in (submission_dir, reference_dir, public_dir, raw_dir):
        path.mkdir(parents=True, exist_ok=True)

    return GradingRequest(
        submission=SubmissionArtifact(
            root=submission_dir,
            kind="directory",
            format_hint=None,
            expected_name=submission_dir.name,
        ),
        references=ReferenceArtifacts(
            task_root=tmp_path,
            raw_dir=raw_dir,
            public_dir=public_dir,
            private_dir=reference_dir,
            answers_path=None,
            gold_submission_path=None,
            sample_submission_path=None,
            answers_root=reference_dir,
        ),
        context=GradingContext(
            task_id="plot-test",
            source_id="dacode",
            engine_id="mle",
            mode="test",
            metadata={},
        ),
    )


def test_compare_color_field_accepts_named_color_against_hex() -> None:
    assert compare_color_field(["skyblue"], ["#87ceeb"])


def test_compare_color_field_accepts_rgba_palette_against_hex() -> None:
    result = [[0.12156862745098039, 0.4666666666666667, 0.7058823529411765, 1.0]]
    gold = ["#1f77b4"]
    assert compare_color_field(result, gold)


def test_compare_color_field_accepts_integer_palette_against_repeated_colors() -> None:
    result = [0, 1, 1, 2, 0]
    gold = ["#111111", "#222222", "#222222", "#333333", "#111111"]
    assert compare_color_field(result, gold)


def test_compare_plot_key_handles_unknown_color_strings_without_crashing() -> None:
    result = {"color": ["viridis"]}
    gold = {"color": ["#87ceeb", "#1f77b4"]}
    assert compare_plot_key("color", result, gold) is False


def test_grade_plot_submission_uses_npy_and_json_fallback(tmp_path: Path) -> None:
    request = _build_request(tmp_path)

    submission_dir = request.submission.root
    reference_dir = request.references.private_dir

    _write_png(submission_dir / "result.png", (255, 0, 0))
    _write_png(reference_dir / "result.png", (0, 0, 255))

    np.save(submission_dir / "result.npy", np.array([1.0, 2.0, 3.0]))
    np.save(reference_dir / "result.npy", np.array([1.0, 2.0, 3.0]))

    _write_plot_json(submission_dir / "plot.json", color=["skyblue"])
    _write_plot_json(reference_dir / "plot.json", color=["#87ceeb"])

    assert grade_plot_submission(request) == 1.0


def test_grade_plot_submission_raises_for_missing_plot_json(tmp_path: Path) -> None:
    request = _build_request(tmp_path)

    submission_dir = request.submission.root
    reference_dir = request.references.private_dir

    _write_png(submission_dir / "result.png", (255, 0, 0))
    _write_png(reference_dir / "result.png", (0, 0, 255))
    np.save(submission_dir / "result.npy", np.array([1.0, 2.0, 3.0]))
    np.save(reference_dir / "result.npy", np.array([1.0, 2.0, 3.0]))
    _write_plot_json(reference_dir / "plot.json", color=["#87ceeb"])

    with pytest.raises(SubmissionValidationError):
        grade_plot_submission(request)
