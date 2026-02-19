from __future__ import annotations

import importlib
import sys


def test_core_import_does_not_pull_runner_or_runtime() -> None:
    # Reset relevant modules to observe import side effects deterministically.
    for name in [
        "dslighting.core",
        "dslighting.runner",
        "dslighting.runtime",
    ]:
        sys.modules.pop(name, None)

    importlib.import_module("dslighting.core")

    assert "dslighting.runner" not in sys.modules
    assert "dslighting.runtime" not in sys.modules
