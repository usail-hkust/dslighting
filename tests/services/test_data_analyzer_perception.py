from __future__ import annotations

from pathlib import Path

from dslighting.services.data_analyzer import DataAnalyzer


def test_analyze_data_preserves_overview_then_detail_style(tmp_path: Path) -> None:
    data_dir = tmp_path / "public"
    data_dir.mkdir()
    (data_dir / "match.csv").write_text("id,score\n1,10\n2,20\n", encoding="utf-8")
    (data_dir / "schema.yml").write_text("# Database Schema\n## Table: Match\n- id: INTEGER\n", encoding="utf-8")

    report = DataAnalyzer(cache_enabled=False).analyze_data(data_dir)

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

    report = DataAnalyzer(cache_enabled=False).analyze_data(data_dir)

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

    report = DataAnalyzer(cache_enabled=False).analyze_data(data_dir)

    assert "### Analysis of `schema.yml`" in report
    assert "Kind: schema document" in report
    assert "Detected Tables (2):" in report
    assert "- Country (2 columns)" in report
    assert "- League (3 columns)" in report
