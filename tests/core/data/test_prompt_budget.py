from __future__ import annotations

from pathlib import Path

from dslighting.core.data.introspection import DataPerceptionRequest, DataPerceptionService


def test_prompt_budget_preserves_schema_and_degraded_artifacts(tmp_path: Path) -> None:
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
    (data_dir / "schema.yml").write_text(
        "# Database Schema\n## Table: Player\n- id: INTEGER\n- player_name: TEXT\n",
        encoding="utf-8",
    )
    for idx in range(4):
        (data_dir / f"table_{idx}.csv").write_text(
            "id,value\n" + "\n".join(f"{row},{row * idx + 1}" for row in range(1, 12)) + "\n",
            encoding="utf-8",
        )

    request = DataPerceptionRequest(data_dir=data_dir, max_report_chars=2200)
    service = DataPerceptionService(request)

    context = service.inspect()
    report = service.render_prompt(context)

    assert "player.csv" in context.detail_artifacts
    assert "schema.yml" in context.detail_artifacts
    assert context.omitted_artifacts
    assert "### Analysis of `player.csv`" in report
    assert "### Analysis of `schema.yml`" in report
    assert "Omitted detail sections due to report budget" in report
    assert len(report) <= request.max_report_chars


def test_prompt_budget_keeps_original_order_for_selected_artifacts(tmp_path: Path) -> None:
    data_dir = tmp_path / "public"
    data_dir.mkdir()
    (data_dir / "first.csv").write_text("id,value\n1,10\n2,20\n", encoding="utf-8")
    (data_dir / "schema.yml").write_text("# Database Schema\n## Table: First\n- id: INTEGER\n", encoding="utf-8")
    (data_dir / "second.csv").write_text("id,value\n1,100\n2,200\n", encoding="utf-8")

    request = DataPerceptionRequest(data_dir=data_dir, max_report_chars=1600)
    service = DataPerceptionService(request)
    report = service.build_report()

    schema_index = report.index("### Analysis of `schema.yml`")
    first_index = report.index("### Analysis of `first.csv`")
    assert first_index < schema_index
