from __future__ import annotations

import warnings

import pytest

import dslighting.utils as utils
from dslighting.debug.compat import init_debug_logger


def test_legacy_init_debug_logger_not_exported_from_utils_root() -> None:
    assert "init_debug_logger" not in utils.__all__
    assert not hasattr(utils, "init_debug_logger")


def test_legacy_init_debug_logger_warns_on_use() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        logger = init_debug_logger(enabled=False)

    assert logger is not None
    assert any(item.category is DeprecationWarning for item in caught)
