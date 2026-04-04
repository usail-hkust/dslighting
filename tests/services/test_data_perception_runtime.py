"""Tests for DataPerceptionRuntime: task scoping and report structure.

Migrated from test_data_analyzer_task_scope.py and test_data_analyzer_perception.py.
The DataPerceptionRuntime replaces the old DataAnalyzer; these tests verify that
the behavior under test (different data_dir scopes produce different reports,
cache hit/miss mechanics, report structure) is preserved.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dslighting.benchmark.grading.models import (
    SubmissionArtifactContract,
    SubmissionEntrySpec,
    SubmissionValidationSpec,
)
from dslighting.core.data.perception.cache import DataPerceptionCache
from dslighting.core.data.perception.runtime import DataPerceptionRuntime


def _write_minimal_dataset(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "train.csv").write_text("id,value\n1,10\n2,20\n", encoding="utf-8")
    (data_dir / "sample_submission.csv").write_text(
        "id,answer\n1,@placeholder[0.00]\n", encoding="utf-8"
    )


@pytest.fixture(autouse=True)
def _clear_cache():
    DataPerceptionCache._clear_in_memory_cache_for_tests()
    yield
    DataPerceptionCache._clear_in_memory_cache_for_tests()


# ----------------------------------------------------------------------
# Report structure tests (migrated from test_data_analyzer_perception.py)
# ----------------------------------------------------------------------


def test_analyze_data_preserves_overview_then_detail_style(tmp_path: Path) -> None:
    data_dir = tmp_path / "public"
    data_dir.mkdir()
    (data_dir / "match.csv").write_text("id,score\n1,10\n2,20\n", encoding="utf-8")
    (data_dir / "schema.yml").write_text("# Database Schema\n## Table: Match\n- id: INTEGER\n", encoding="utf-8")

    runtime = DataPerceptionRuntime(cache_enabled=False)
    report = runtime.analyze_data(data_dir)

    assert "--- COMPREHENSIVE DATA REPORT ---" in report
    assert "## Directory Structure (Current Working Directory)" in report
    assert "## Data Inventory Summary" in report
    assert "## Data Schema Analysis" in report
    assert "### Analysis of `match.csv`" in report
    assert "### Analysis of `schema.yml`" in report


def test_analyze_data_reports_malformed_csv_with_fallback_summary(tmp_path: Path) -> None:
    data_dir = tmp_path / "public"
    data_dir.mkdir()
    (data_dir / "player.csv").write_text(
        "\n".join(
            [
                "height,id,birthday,player_fifa_id,player_id,weight,player_name",
                "182.88,1,1992-02-29 00:00:00,218353,505942,187,Aaron Appindangoye",
                "0, f, 22, nan, df, a, 161, 11",
                "185.42,22,1986-10-22 00:00:00,202425,245653,161,Abdelfettah Boukhriss",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    runtime = DataPerceptionRuntime(cache_enabled=False)
    report = runtime.analyze_data(data_dir)

    assert "### Analysis of `player.csv`" in report
    assert "Strict Parse: failed" in report
    assert "Tolerant Parse: succeeded with skipped malformed rows" in report
    assert "Malformed Row Examples:" in report
    assert "line 3: expected 7 fields, saw 8" in report
    assert "player_name" in report


def test_analyze_data_reports_schema_documents_in_detail_section(tmp_path: Path) -> None:
    data_dir = tmp_path / "public"
    data_dir.mkdir()
    (data_dir / "schema.yml").write_text(
        "\n".join(
            [
                "# Database Schema",
                "",
                "## Table: Country",
                "- id: INTEGER PRIMARY KEY",
                "- name: TEXT",
                "",
                "## Table: League",
                "- id: INTEGER PRIMARY KEY",
                "- country_id: INTEGER",
                "- name: TEXT",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    runtime = DataPerceptionRuntime(cache_enabled=False)
    report = runtime.analyze_data(data_dir)

    assert "### Analysis of `schema.yml`" in report
    assert "Kind: schema document" in report
    assert "Detected Tables (2):" in report
    assert "- Country (2 columns)" in report
    assert "- League (3 columns)" in report


def test_generate_io_instructions_supports_directory_submission_contract(tmp_path: Path) -> None:
    contract = SubmissionArtifactContract(
        sample_submission_path=None,
        output_submission_path=tmp_path / "submission_bundle_demo",
        submission_filename="submission_bundle_demo",
        submission_format="",
        validation=SubmissionValidationSpec(
            expected_kind="directory",
            expected_name="submission_bundle_demo",
            required_children=("before.csv", "after.csv"),
        ),
        entries=(
            SubmissionEntrySpec(
                relative_path="before.csv",
                format="csv",
                sample_path=tmp_path / "sample_before.csv",
                description="before epoch matrix",
            ),
            SubmissionEntrySpec(
                relative_path="after.csv",
                format="csv",
                sample_path=tmp_path / "sample_after.csv",
                description="after epoch matrix",
            ),
        ),
    )

    runtime = DataPerceptionRuntime(cache_enabled=False)
    instructions = runtime.generate_io_instructions(
        contract.output_submission_path.name,
        submission_context=contract.to_payload(),
    )

    assert "Required output directory name" in instructions
    assert "`before.csv`" in instructions
    assert "sample: sample_before.csv" in instructions
    assert "Missing any required file will make the submission invalid." in instructions


# ----------------------------------------------------------------------
# Task-scoping tests (migrated from test_data_analyzer_task_scope.py)
# ----------------------------------------------------------------------


def test_task_scoped_cache_distinguishes_analysis_root(tmp_path: Path) -> None:
    """Root-level analyze_data includes files from subdirs; public-only does not."""
    task_root = tmp_path / "dacode-di-text-001"
    public_dir = task_root / "prepared" / "public"
    private_dir = task_root / "prepared" / "private"
    raw_dir = task_root / "raw"
    public_dir.mkdir(parents=True)
    private_dir.mkdir(parents=True)
    raw_dir.mkdir(parents=True)

    (task_root / "config.yaml").write_text("id: dacode-di-text-001\n", encoding="utf-8")
    (task_root / "leaderboard.csv").write_text("team_name,score\n", encoding="utf-8")
    (raw_dir / "world-data-2023.csv").write_text("Country,Population Density\nA,1\n", encoding="utf-8")
    (public_dir / "sample_submission.csv").write_text(
        "highest country,lowest country\n", encoding="utf-8"
    )
    (private_dir / "answer.csv").write_text(
        "highest country,lowest country\nA,B\n", encoding="utf-8"
    )

    runtime = DataPerceptionRuntime()
    submission_context = {
        "sample_submission_path": str(public_dir / "sample_submission.csv"),
        "submission_filename": "sample_submission.csv",
        "submission_format": ".csv",
        "output_submission_path": "submission.csv",
    }

    root_report = runtime.analyze_data(
        task_root,
        task_type="kaggle",
        task_id="dacode-di-text-001",
        submission_context=submission_context,
    )
    public_report = runtime.analyze_data(
        public_dir,
        task_type="kaggle",
        task_id="dacode-di-text-001",
        submission_context=submission_context,
    )

    assert "config.yaml" in root_report
    assert "world-data-2023.csv" in root_report
    assert "config.yaml" not in public_report
    assert "world-data-2023.csv" not in public_report
    assert "sample_submission.csv" in public_report
