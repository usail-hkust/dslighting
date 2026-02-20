import pytest

from dslighting.api.agent import Agent
from dslighting.core.interfaces import AgentResult
from dslighting.error import ConfigurationError


def test_agent_invalid_workflow_raises_cfg_002() -> None:
    with pytest.raises(ConfigurationError) as exc:
        Agent(workflow="unknown-workflow")

    assert exc.value.error_code == "CFG-002"


@pytest.mark.asyncio
async def test_agent_async_run_delegates_to_app_service(monkeypatch) -> None:
    captured = {}

    async def _fake_run(self, **kwargs):
        captured.update(kwargs)
        return AgentResult(success=True, output="ok")

    monkeypatch.setattr("dslighting.core.application.agent_app_service.AgentAppService.run", _fake_run)

    agent = Agent(workflow="aide", model="gpt-4o")
    result = await agent.async_run(task_id="bike-sharing-demand", task="desc", max_iterations=3)

    assert result.success is True
    assert captured["task_id"] == "bike-sharing-demand"
    assert captured["task"] == "desc"
    assert captured["kwargs"]["max_iterations"] == 3


@pytest.mark.asyncio
async def test_agent_run_raises_cfg_003_in_async_context() -> None:
    agent = Agent(workflow="aide", model="gpt-4o")
    with pytest.raises(ConfigurationError) as exc:
        agent.run(task_id="bike-sharing-demand")
    assert exc.value.error_code == "CFG-003"
    assert "async_run" in (exc.value.suggestion or "")


def test_agent_run_keeps_sync_path(monkeypatch) -> None:
    agent = Agent(workflow="aide", model="gpt-4o")

    monkeypatch.setattr("asyncio.get_running_loop", lambda: (_ for _ in ()).throw(RuntimeError("no running event loop")))

    expected = AgentResult(success=True, output="ok")

    def _fake_asyncio_run(coro):
        # close coroutine to avoid warning, then return expected sync value
        coro.close()
        return expected

    monkeypatch.setattr("asyncio.run", _fake_asyncio_run)

    result = agent.run(task_id="bike-sharing-demand")
    assert result is expected
