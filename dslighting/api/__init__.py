"""Layered API namespace for DSLighting.

Preferred import paths:
    - Stable public API: ``dslighting.api.public``
    - Evolutionary internal API: ``dslighting.api.internal``

Legacy imports from ``dslighting.api`` are preserved for compatibility in this
phase and emit deprecation warnings.
"""

from importlib import import_module
from typing import Dict, Set, Tuple
import warnings

_LEGACY_EXPORTS: Dict[str, Tuple[str, str, str]] = {
    # Stable API names (use dslighting.api.public)
    "Agent": ("dslighting.api.public", "Agent", "dslighting.api.public"),
    "AgentResult": ("dslighting.api.public", "AgentResult", "dslighting.api.public"),
    "DataLoader": ("dslighting.api.public", "DataLoader", "dslighting.api.public"),
    "TaskContext": ("dslighting.api.public", "TaskContext", "dslighting.api.public"),
    "run_agent": ("dslighting.api.public", "run_agent", "dslighting.api.public"),
    "load_data": ("dslighting.api.public", "load_data", "dslighting.api.public"),
    "setup": ("dslighting.api.public", "setup", "dslighting.api.public"),
    "DSBenchmark": ("dslighting.api.public", "DSBenchmark", "dslighting.api.public"),
    "AgentSettingsConfig": ("dslighting.api.public", "AgentSettingsConfig", "dslighting.api.public"),
    "RuntimeConfig": ("dslighting.api.public", "RuntimeConfig", "dslighting.api.public"),
    # Internal/evolutionary API names (use dslighting.api.internal)
    "TaskLoader": ("dslighting.api.internal", "TaskLoader", "dslighting.api.internal"),
}

_WARNED_LEGACY_NAMES: Set[str] = set()


def __getattr__(name: str):
    if name in ("public", "internal"):
        module = import_module(f"dslighting.api.{name}")
        globals()[name] = module
        return module

    if name not in _LEGACY_EXPORTS:
        raise AttributeError(f"module 'dslighting.api' has no attribute '{name}'")

    module_name, attr_name, recommended_module = _LEGACY_EXPORTS[name]

    if name not in _WARNED_LEGACY_NAMES:
        warnings.warn(
            (
                f"`dslighting.api.{name}` is deprecated and will move out of this "
                f"compatibility layer in a future release. "
                f"Import `{name}` from `{recommended_module}` instead."
            ),
            DeprecationWarning,
            stacklevel=2,
        )
        _WARNED_LEGACY_NAMES.add(name)

    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(
        list(globals().keys())
        + list(_LEGACY_EXPORTS.keys())
        + ["public", "internal"]
    )


__all__ = [
    "public",
    "internal",
    "Agent",
    "AgentResult",
    "DataLoader",
    "TaskContext",
    "run_agent",
    "load_data",
    "setup",
    "DSBenchmark",
    "AgentSettingsConfig",
    "RuntimeConfig",
    "TaskLoader",
]
