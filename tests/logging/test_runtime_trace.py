from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from dslighting.logging import configure_logging
from dslighting.logging.setup import get_logging_controller
from dslighting.services.workspace import WorkspaceService
from dslighting.tools.base import Tool

pytest.importorskip("nbformat")
from dslighting.services.sandbox import SandboxService


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _cleanup() -> None:
    controller = get_logging_controller()
    if controller is not None:
        controller.close()


def test_tool_trace_emits_structured_events(tmp_path: Path) -> None:
    _cleanup()
    controller = configure_logging(
        console=False,
        trace_tools=True,
        output_dir=str(tmp_path),
        force=True,
    )

    tool = Tool(name="adder", description="Add two numbers", fn=lambda x, y: x + y)
    assert tool(2, 3) == 5
    controller.close()

    session_dir = Path(controller.get_debug_session_path() or "")
    events = _read_jsonl(session_dir / "events.jsonl")
    assert any(event["event_type"] == "tool.call.completed" for event in events)
    assert any(event["tags"].get("tool_name") == "adder" for event in events)


def test_sandbox_trace_emits_structured_events(tmp_path: Path) -> None:
    _cleanup()
    controller = configure_logging(
        console=False,
        trace_sandbox=True,
        output_dir=str(tmp_path / "debug"),
        force=True,
    )

    workspace = WorkspaceService("sandbox_trace_test", base_dir=str(tmp_path / "workspace"))
    sandbox = SandboxService(workspace=workspace, timeout=5)
    result = asyncio.run(sandbox.run_script("print('hello sandbox')"))
    assert result.success is True
    controller.close()

    session_dir = Path(controller.get_debug_session_path() or "")
    events = _read_jsonl(session_dir / "events.jsonl")
    assert any(event["event_type"] == "sandbox.exec.completed" for event in events)
    assert any(event["tags"].get("mode") == "script" for event in events)
