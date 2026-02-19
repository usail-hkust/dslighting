from __future__ import annotations

import ast
from pathlib import Path

import dslighting.utils.constants as constants
import dslighting.utils.defaults as defaults

SINGLE_SOURCE_NAMES = (
    "DEFAULT_TOTAL_STEPS",
    "DEFAULT_DEBUG_PROBABILITY",
    "DEFAULT_SUCCESS_THRESHOLD",
    "DEFAULT_MAX_ROUNDS",
    "DEFAULT_MAX_INFLIGHT_NODES",
    "DEFAULT_CACHE_TTL_SECONDS",
)


def test_selected_defaults_values_match_defaults_module() -> None:
    for name in SINGLE_SOURCE_NAMES:
        assert getattr(constants, name) == getattr(defaults, name)


def test_constants_module_does_not_redefine_selected_defaults() -> None:
    constants_path = Path("dslighting/utils/constants.py")
    module = ast.parse(constants_path.read_text(encoding="utf-8"))

    assigned_names: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned_names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            assigned_names.add(node.target.id)

    overlap = sorted(set(SINGLE_SOURCE_NAMES) & assigned_names)
    assert not overlap, f"constants.py redefines defaults: {overlap}"
