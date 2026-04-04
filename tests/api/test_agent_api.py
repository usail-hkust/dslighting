import pytest

pytest.importorskip("pandas")

from dslighting.api.agent import Agent
from dslighting.core.interfaces import AgentResult


def test_agent_run_passes_inputs_to_async_run(monkeypatch, tmp_path):
    task_dir = tmp_path / "bike-sharing-demand"
    task_dir.mkdir()

    captured = {}

    async def fake_async_run(self, task_id=None, data=None, task=None, output=None, **kwargs):
        captured["task_id"] = task_id
        captured["data"] = data
        captured["task"] = task
        return AgentResult(success=True, output="ok")

    monkeypatch.setattr(Agent, "async_run", fake_async_run)

    agent = Agent(workflow="aide")
    result = agent.run(data=task_dir, task="predict demand")

    assert result.success is True
    assert captured["task_id"] is None
    assert captured["data"] == task_dir
    assert captured["task"] == "predict demand"
