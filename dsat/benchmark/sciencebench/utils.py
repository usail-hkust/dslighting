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
    """Returns an absolute path to the repository directory."""
    # Module lives at `benchmarks/sciencebench`; repo root is two levels up.
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
    module_path, fn_name = fn_string.rsplit(":", 1)

    # Compat: some configs use `benchmarks.sciencebench...` even when `benchmarks/`
    # is already a top-level package in the current Python path.
    candidate_modules = [module_path]
    if module_path.startswith("benchmarks."):
        candidate_modules.append(module_path[len("benchmarks.") :])

    last_error: Exception | None = None
    for candidate in candidate_modules:
        try:
            module = importlib.import_module(candidate)
            return getattr(module, fn_name)
        except Exception as exc:
            last_error = exc

    # Fallback: some competition modules include hyphens in their directory names
    # (e.g. `...competitions.sciencebench-040-md-rf.grade`), which cannot be
    # imported as a normal Python module. Load them from file path instead.
    from importlib import util as importlib_util

    def _try_load_from_file(module_path_str: str) -> Callable | None:
        if module_path_str.startswith("benchmarks."):
            rel = Path(*module_path_str.split(".")).with_suffix(".py")
            module_file = (get_repo_dir() / rel).resolve()
        else:
            rel = Path("benchmarks") / Path(*module_path_str.split(".")).with_suffix(".py")
            module_file = (get_repo_dir() / rel).resolve()

        if not module_file.exists():
            return None

        unique_name = f"_dsat_sciencebench_filemod_{abs(hash(str(module_file)))}"
        spec = importlib_util.spec_from_file_location(unique_name, str(module_file))
        if spec is None or spec.loader is None:
            return None
        module = importlib_util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        return getattr(module, fn_name)

    for candidate in candidate_modules:
        try:
            loaded = _try_load_from_file(candidate)
            if loaded is not None:
                return loaded
        except Exception as exc:
            last_error = exc

    raise ModuleNotFoundError(f"Failed to import callable '{fn_string}': {last_error}") from last_error
