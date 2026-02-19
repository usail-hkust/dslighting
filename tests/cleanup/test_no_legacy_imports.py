from __future__ import annotations

from pathlib import Path

FORBIDDEN_TOKENS = (
    "ErrorFormatter",
    "DSLightingFrameworkError",
    "InvalidConfigError",
    "WorkflowExecutionError",
    "BenchmarkTaskLoadError",
    "LLMError",
    "SandboxError",
    "TaskConfigInvalidError",
    "TaskRegistryNotFoundError",
    "CompetitionContextMissingError",
    "get_default_paths",
    "load_dataset = load_example",
    "create_debug_prompt = create_generic_debug_prompt",
)


def _iter_python_files() -> list[Path]:
    root = Path(__file__).resolve().parents[2] / "dslighting"
    return sorted(root.rglob("*.py"))


def test_no_forbidden_legacy_tokens_in_source() -> None:
    offenders: list[str] = []
    for pyfile in _iter_python_files():
        text = pyfile.read_text(encoding="utf-8")
        for token in FORBIDDEN_TOKENS:
            if token in text:
                offenders.append(f"{pyfile}: {token}")

    assert not offenders, "Found forbidden legacy tokens:\n" + "\n".join(offenders)


def test_no_legacy_exceptions_module_file() -> None:
    legacy_module = Path(__file__).resolve().parents[2] / "dslighting" / "exceptions.py"
    assert not legacy_module.exists(), "dslighting/exceptions.py must not exist"
