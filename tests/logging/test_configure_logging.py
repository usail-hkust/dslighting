from __future__ import annotations

import logging
from pathlib import Path

import pytest

import dslighting
from dslighting.logging import configure_logging
from dslighting.logging.setup import get_logging_controller


@pytest.fixture(autouse=True)
def _cleanup_logging_controller() -> None:
    controller = get_logging_controller()
    if controller is not None:
        controller.close()
    yield
    controller = get_logging_controller()
    if controller is not None:
        controller.close()


def test_configure_logging_exported_from_root() -> None:
    assert dslighting.configure_logging is configure_logging


def test_configure_logging_rejects_provider_raw_without_llm_trace() -> None:
    with pytest.raises(ValueError, match="provider_raw=True requires trace_llm=True"):
        configure_logging(provider_raw=True)


def test_configure_logging_creates_debug_session_dir(tmp_path: Path) -> None:
    controller = configure_logging(
        level="INFO",
        console=False,
        trace_llm=True,
        output_dir=str(tmp_path),
        force=True,
    )

    session_path = controller.get_debug_session_path()
    assert session_path is not None
    assert Path(session_path).exists()
    assert Path(session_path).parent == tmp_path.resolve()


def test_configure_logging_warns_and_reuses_existing_controller(caplog: pytest.LogCaptureFixture) -> None:
    first = configure_logging(level="INFO", console=False, force=True)

    with caplog.at_level(logging.WARNING):
        second = configure_logging(level="DEBUG")

    assert second is first
    assert "reusing current configuration" in caplog.text


def test_configure_logging_installs_file_handler(tmp_path: Path) -> None:
    log_file = tmp_path / "runtime.log"
    controller = configure_logging(
        level="INFO",
        console=False,
        file=str(log_file),
        force=True,
    )
    logging.getLogger().info("hello from unified logging")
    controller.flush()

    assert log_file.exists()
    assert "hello from unified logging" in log_file.read_text(encoding="utf-8")
