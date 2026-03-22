from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("diskcache")

from dslighting.services.data_analyzer import DataAnalyzer


def test_task_scoped_cache_distinguishes_analysis_root(tmp_path: Path) -> None:
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
    (public_dir / "sample_submission.csv").write_text("highest country,lowest country\n", encoding="utf-8")
    (private_dir / "answer.csv").write_text("highest country,lowest country\nA,B\n", encoding="utf-8")

    analyzer = DataAnalyzer()
    submission_context = {
        "sample_submission_path": str(public_dir / "sample_submission.csv"),
        "submission_filename": "sample_submission.csv",
        "submission_format": ".csv",
        "output_submission_path": "submission.csv",
    }

    root_report = analyzer.analyze_data(
        task_root,
        task_type="kaggle",
        task_id="dacode-di-text-001",
        submission_context=submission_context,
    )
    public_report = analyzer.analyze_data(
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
