"""Configuration objects for the unified logging entrypoint."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off", ""}
_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def _read_bool_env(name: str) -> bool | None:
    raw = os.getenv(name)
    if raw is None:
        return None
    normalized = raw.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    return None


def _read_text_env(name: str) -> str | None:
    raw = os.getenv(name)
    if raw is None:
        return None
    value = raw.strip()
    return value or None


@dataclass
class LoggingConfig:
    level: str = "INFO"
    format: str = "%(name)s - %(message)s"
    console: bool = True
    file: str | None = None
    trace_llm: bool = False
    trace_tools: bool = False
    trace_sandbox: bool = False
    output_dir: str | None = None
    provider_raw: bool = False
    force: bool = False

    @classmethod
    def from_env(cls) -> "LoggingConfig":
        level = (_read_text_env("DSL_LOG_LEVEL") or "INFO").upper()
        return cls(
            level=level,
            format=_read_text_env("DSL_LOG_FORMAT") or "%(name)s - %(message)s",
            console=True if _read_bool_env("DSL_LOG_CONSOLE") is None else bool(_read_bool_env("DSL_LOG_CONSOLE")),
            file=_read_text_env("DSL_LOG_FILE"),
            trace_llm=bool(_read_bool_env("DSL_TRACE_LLM")),
            trace_tools=bool(_read_bool_env("DSL_TRACE_TOOLS")),
            trace_sandbox=bool(_read_bool_env("DSL_TRACE_SANDBOX")),
            output_dir=_read_text_env("DSL_LOG_OUTPUT_DIR"),
            provider_raw=bool(_read_bool_env("DSL_PROVIDER_RAW")),
            force=False,
        )

    def merge(self, *, override: "LoggingConfig") -> "LoggingConfig":
        merged = LoggingConfig(
            level=override.level,
            format=override.format,
            console=override.console,
            file=override.file,
            trace_llm=override.trace_llm,
            trace_tools=override.trace_tools,
            trace_sandbox=override.trace_sandbox,
            output_dir=override.output_dir,
            provider_raw=override.provider_raw,
            force=override.force,
        )
        return merged

    def normalized_level(self) -> str:
        return self.level.strip().upper()

    def resolved_file(self) -> Path | None:
        if self.file is None:
            return None
        return Path(self.file).expanduser().resolve()

    def resolved_output_dir(self) -> Path | None:
        if self.output_dir is None:
            return None
        return Path(self.output_dir).expanduser().resolve()

    def validate(self) -> None:
        level = self.normalized_level()
        if level not in _LEVELS:
            raise ValueError(f"Unsupported log level: {self.level}")
        if self.provider_raw and not self.trace_llm:
            raise ValueError("provider_raw=True requires trace_llm=True")

