from __future__ import annotations

import importlib

import dslighting.logging as logging_module


def test_cli_module_configures_logging_via_unified_entrypoint(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake_configure_logging(**kwargs):
        captured["kwargs"] = kwargs
        return object()

    monkeypatch.setattr(logging_module, "configure_logging", _fake_configure_logging)

    import dslighting.cli.__main__ as cli_main

    importlib.reload(cli_main)

    assert captured["kwargs"] == {
        "level": "INFO",
        "format": "%(message)s",
        "force": True,
    }

    monkeypatch.undo()
    importlib.reload(cli_main)
