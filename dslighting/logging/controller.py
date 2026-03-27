"""Lifecycle controller for unified logging configuration."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from dslighting.debug.session import DebugSession

if TYPE_CHECKING:
    from dslighting.logging.config import LoggingConfig


@dataclass
class LoggingController:
    debug_session: DebugSession | None
    installed_handlers: list[logging.Handler] = field(default_factory=list)
    session_path: str | None = None
    target_logger_names: list[str] = field(default_factory=list)
    config: "LoggingConfig | None" = None
    closed: bool = False

    def flush(self) -> None:
        for handler in self.installed_handlers:
            handler.flush()
        if self.debug_session is not None:
            self.debug_session._payload_store.flush()  # type: ignore[attr-defined]

    def close(self) -> None:
        if self.closed:
            return
        self.flush()
        if self.debug_session is not None:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                asyncio.run(self.debug_session.close())
            else:
                loop.create_task(self.debug_session.close())
        for name in self.target_logger_names:
            logger = logging.getLogger(name) if name != "root" else logging.getLogger()
            for handler in list(self.installed_handlers):
                if handler in logger.handlers:
                    logger.removeHandler(handler)
                try:
                    handler.close()
                except Exception:
                    pass
        self.closed = True

    def get_debug_session_path(self) -> str | None:
        return self.session_path

    def get_statistics(self) -> dict[str, float]:
        if self.debug_session is None:
            return {}
        return self.debug_session.get_statistics()

    def print_statistics(self) -> None:
        logger = logging.getLogger("dslighting.debug")
        stats = self.get_statistics()
        if not stats:
            return
        logger.info("=" * 50)
        logger.info("LLM Debug Session Statistics")
        logger.info("=" * 50)
        for key, value in stats.items():
            logger.info("%s: %s", key, value)
        logger.info("=" * 50)
