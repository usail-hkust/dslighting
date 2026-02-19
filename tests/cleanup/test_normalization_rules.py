from __future__ import annotations

import ast
from pathlib import Path

from dslighting.checkpoint.checkpoint import CheckpointError
from dslighting.error.exceptions import DSLightingError


TARGET_ABSTRACT_FILES = (
    Path("dslighting/state/base.py"),
    Path("dslighting/checkpoint/checkpoint.py"),
)


def _has_abstract_decorator(func: ast.FunctionDef) -> bool:
    for deco in func.decorator_list:
        if isinstance(deco, ast.Name) and deco.id == "abstractmethod":
            return True
        if isinstance(deco, ast.Attribute) and deco.attr == "abstractmethod":
            return True
    return False


def test_abstract_methods_do_not_use_pass_body() -> None:
    offenders: list[str] = []

    for relpath in TARGET_ABSTRACT_FILES:
        source = relpath.read_text(encoding="utf-8")
        module = ast.parse(source)
        for node in ast.walk(module):
            if isinstance(node, ast.FunctionDef) and _has_abstract_decorator(node):
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    offenders.append(f"{relpath}:{node.lineno} {node.name}")

    assert not offenders, "Abstract methods must not use pass:\n" + "\n".join(offenders)


def test_dslighting_error_code_fallback_none_only() -> None:
    default_error = DSLightingError(message="x", error_code=None)
    assert default_error.error_code == "DSL-000"

    empty_error = DSLightingError(message="x", error_code="")
    assert empty_error.error_code == ""

    custom_error = DSLightingError(message="x", error_code="CFG-999")
    assert custom_error.error_code == "CFG-999"


def test_checkpoint_error_code_fallback_none_only() -> None:
    default_error = CheckpointError(message="x", error_code=None)
    assert default_error.error_code == "CHK-000"

    empty_error = CheckpointError(message="x", error_code="")
    assert empty_error.error_code == ""

    custom_error = CheckpointError(message="x", error_code="CHK-999")
    assert custom_error.error_code == "CHK-999"
