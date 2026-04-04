from __future__ import annotations

from pathlib import Path

from dslighting.core.data.perception import DataPerceptionRequest, DataPerceptionService


def test_data_perception_service_builds_structured_context(tmp_path: Path) -> None:
    data_dir = tmp_path / "public"
    data_dir.mkdir()
    (data_dir / "player.csv").write_text(
        "height,id,birthday,player_fifa_id,player_id,weight,player_name\n"
        "182.88,1,1992-02-29 00:00:00,218353,505942,187,Aaron Appindangoye\n"
        "0, f, 22, nan, df, a, 161, 11\n",
        encoding="utf-8",
    )
    (data_dir / "schema.yml").write_text(
        "# Database Schema\n## Table: Player\n- id: INTEGER\n- player_name: TEXT\n",
        encoding="utf-8",
    )

    service = DataPerceptionService(DataPerceptionRequest(data_dir=data_dir))
    context = service.inspect()

    assert context.inventory.counts["total"] == 2
    assert "player.csv" in context.detail_artifacts
    assert "schema.yml" in context.detail_artifacts
    assert any(summary.descriptor.kind == "tabular" for summary in context.summaries)
    assert any(summary.descriptor.kind == "document" for summary in context.summaries)


def test_data_perception_service_renders_existing_prompt_style(tmp_path: Path) -> None:
    data_dir = tmp_path / "public"
    data_dir.mkdir()
    (data_dir / "match.csv").write_text("id,score\n1,10\n2,20\n", encoding="utf-8")
    (data_dir / "schema.yml").write_text("# Database Schema\n## Table: Match\n- id: INTEGER\n", encoding="utf-8")

    service = DataPerceptionService(DataPerceptionRequest(data_dir=data_dir))
    report = service.build_report()

    assert "--- COMPREHENSIVE DATA REPORT ---" in report
    assert "## Directory Structure (Current Working Directory)" in report
    assert "## Data Inventory Summary" in report
    assert "## Data Schema Analysis" in report
    assert "### Analysis of `match.csv`" in report
    assert "### Analysis of `schema.yml`" in report
