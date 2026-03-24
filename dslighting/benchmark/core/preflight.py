from __future__ import annotations

import importlib
import logging

logger = logging.getLogger(__name__)

REQUIRED_DEPENDENCIES: list[tuple[str, str]] = [
    ("openpyxl", "Excel (.xlsx) input parsing for DACode benchmark tasks"),
]


def run_preflight_checks() -> None:
    """Warn if optional dependencies required by benchmarks are missing."""
    missing = []
    for module, description in REQUIRED_DEPENDENCIES:
        try:
            importlib.import_module(module)
        except ModuleNotFoundError:
            missing.append((module, description))

    if not missing:
        return

    lines = [
        "Benchmark preflight detected missing optional dependencies:",
    ]
    for module, description in missing:
        lines.append(f"  • {module}: {description}")
    lines.append("Install them via pip or ensure the benchmark venv has them before a long run.")
    logger.warning("\n".join(lines))
