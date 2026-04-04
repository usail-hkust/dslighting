"""Regression tests for workflows command in dslighting.cli.__main__."""

from types import SimpleNamespace

from dslighting.cli import __main__ as cli_main
from dslighting.workflows import presets


def test_get_workflow_info_includes_name_for_available_workflows(monkeypatch):
    """_get_workflow_info should return entries with a stable workflow name key."""
    dummy_workflow = object()
    for attr in (
        "AIDE",
        "AutoKaggle",
        "DataInterpreter",
        "AutoMind",
        "DSAgent",
        "DeepAnalyze",
        "ReAct",
    ):
        monkeypatch.setattr(presets, attr, dummy_workflow, raising=False)

    workflows = cli_main._get_workflow_info()

    assert workflows
    assert all("name" in wf and wf["name"] for wf in workflows)


def test_cmd_workflows_runs_without_keyerror(monkeypatch, capsys):
    """cmd_workflows should keep printing the same name-based header line."""
    monkeypatch.setattr(
        cli_main,
        "_get_workflow_info",
        lambda: [
            {
                "name": "aide",
                "full_name": "AIDE (Adaptive Iteration & Debugging Enhancement)",
                "description": "Self-improving code with iterative debugging",
                "use_cases": ["Kaggle competitions (simple)"],
                "default_model": "gpt-4o",
                "unique_params": None,
            }
        ],
    )

    result = cli_main.cmd_workflows(SimpleNamespace())
    captured = capsys.readouterr()

    assert result == 0
    assert "1. AIDE" in captured.out
