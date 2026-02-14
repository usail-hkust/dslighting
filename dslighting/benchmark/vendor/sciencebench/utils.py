from __future__ import annotations

import importlib
import logging
import yaml
from logging import Logger
from pathlib import Path
from typing import Any, Callable


def get_logger(name: str) -> Logger:
    """Get a logger instance"""
    return logging.getLogger(name)


def get_module_dir() -> Path:
    """Returns an absolute path to the sciencebench module."""
    path = Path(__file__).parent.resolve()
    assert path.name == "sciencebench", \
        f"Expected the module directory to be `sciencebench`, but got `{path.name}`."
    return path


def get_repo_dir() -> Path:
    """Returns an absolute path to the benchmark package root."""
    # Module lives at `benchmark/vendor/sciencebench`; benchmark root is two levels up.
    return get_module_dir().parent.parent


def load_yaml(path: Path) -> dict:
    """Load a YAML file and return its content as a dictionary."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


def import_fn(fn_string: str) -> Callable:
    """
    Import a function from a string.

    Args:
        fn_string: String in the format 'module.path:function_name'

    Returns:
        The imported function
    """
    if fn_string.startswith("file:"):
        from importlib import util as importlib_util

        rest = fn_string[len("file:") :]
        module_path_str, fn_name = rest.rsplit(":", 1)
        module_path = Path(module_path_str)
        if not module_path.is_absolute():
            module_path = get_repo_dir() / module_path
        module_path = module_path.resolve()

        if not module_path.exists():
            raise ModuleNotFoundError(f"File module not found: {module_path}")

        unique_name = f"_sciencebench_filemod_{abs(hash(str(module_path)))}"
        spec = importlib_util.spec_from_file_location(unique_name, str(module_path))
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {module_path}")
        module = importlib_util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        return getattr(module, fn_name)

    module_path, fn_name = fn_string.rsplit(":", 1)

    try:
        module = importlib.import_module(module_path)
        return getattr(module, fn_name)
    except Exception as exc:
        last_error: Exception | None = exc

    from importlib import util as importlib_util

    parts = module_path.split(".")
    if "benchmark" in parts:
        parts = parts[parts.index("benchmark") + 1 :]
    module_file = (get_repo_dir() / Path(*parts).with_suffix(".py")).resolve()

    if not module_file.exists():
        raise ModuleNotFoundError(f"Failed to import callable '{fn_string}': {last_error}") from last_error

    unique_name = f"_sciencebench_filemod_{abs(hash(str(module_file)))}"
    spec = importlib_util.spec_from_file_location(unique_name, str(module_file))
    if spec is None or spec.loader is None:
        raise ModuleNotFoundError(f"Failed to import callable '{fn_string}': {last_error}") from last_error
    module = importlib_util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return getattr(module, fn_name)
