"""Standard library logging setup helpers."""

from __future__ import annotations

import logging
from pathlib import Path

from dslighting.logging.config import LoggingConfig


def install_stdlib_handlers(config: LoggingConfig) -> tuple[list[logging.Handler], list[str]]:
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.normalized_level()))

    handlers: list[logging.Handler] = []
    if config.console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, config.normalized_level()))
        console_handler.setFormatter(logging.Formatter(config.format))
        root_logger.addHandler(console_handler)
        handlers.append(console_handler)

    file_path = config.resolved_file()
    if file_path is not None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(Path(file_path))
        file_handler.setLevel(getattr(logging, config.normalized_level()))
        file_handler.setFormatter(logging.Formatter(config.format))
        root_logger.addHandler(file_handler)
        handlers.append(file_handler)

    return handlers, ["root"]

