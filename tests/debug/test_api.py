from __future__ import annotations

import logging
import os

import litellm

from dslighting.debug.api import get_debug_session, init_debug
from dslighting.debug.litellm_bridge import DSLightingLiteLLMLogger


def test_init_debug_suppresses_noisy_loggers_and_registers_bridge() -> None:
    logging.getLogger("httpx").setLevel(logging.DEBUG)
    logging.getLogger("httpcore").setLevel(logging.DEBUG)
    logging.getLogger("LiteLLM").setLevel(logging.DEBUG)
    litellm.log_raw_request_response = True

    init_debug(enabled=True, profile="full", console_output=False)

    assert os.environ["LITELLM_LOG"] == "WARNING"
    assert logging.getLogger("httpx").level == logging.WARNING
    assert logging.getLogger("httpcore").level == logging.WARNING
    assert logging.getLogger("LiteLLM").level == logging.WARNING
    assert litellm.log_raw_request_response is False
    assert any(isinstance(callback, DSLightingLiteLLMLogger) for callback in litellm.callbacks)


def test_provider_raw_keeps_litellm_debug_but_suppresses_http_stack() -> None:
    init_debug(enabled=True, profile="provider_raw", console_output=False)

    assert os.environ["LITELLM_LOG"] == "DEBUG"
    assert logging.getLogger("LiteLLM").level == logging.DEBUG
    assert logging.getLogger("httpx").level == logging.WARNING
    assert logging.getLogger("httpcore").level == logging.WARNING
    assert litellm.log_raw_request_response is True
    assert any(
        isinstance(callback, DSLightingLiteLLMLogger) and callback.provider_raw
        for callback in litellm.callbacks
    )

    session = get_debug_session()
    if session is not None:
        import asyncio

        asyncio.run(session.close())
