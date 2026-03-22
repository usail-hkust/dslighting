from __future__ import annotations

from dslighting.services.sandbox import SandboxService
from dslighting.services.workspace import WorkspaceService


def test_run_script_sync_uses_timeout_override(monkeypatch, tmp_path) -> None:
    captured: dict[str, float] = {}

    class _CompletedProcess:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def _fake_run(*args, **kwargs):
        _ = args
        captured["timeout"] = kwargs["timeout"]
        return _CompletedProcess()

    monkeypatch.setattr("dslighting.services.sandbox.subprocess.run", _fake_run)

    workspace = WorkspaceService(run_name="timeout_override", base_dir=str(tmp_path))
    sandbox = SandboxService(workspace=workspace, timeout=123)

    result = sandbox._run_script_sync("print('hello')", timeout=7)
    assert result.success is True
    assert captured["timeout"] == 7.0

    result_default = sandbox._run_script_sync("print('hello')", timeout=None)
    assert result_default.success is True
    assert captured["timeout"] == 123.0
