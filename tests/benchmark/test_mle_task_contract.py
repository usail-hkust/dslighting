from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("py7zr")

from dslighting.benchmark.core.mle_task_contract import MLETaskContractLoader
from dslighting.benchmark.core.source_catalog import BenchmarkSourceDescriptor


def test_mle_task_contract_prefers_prepare_val_sibling_file(tmp_path: Path) -> None:
    vendor_root = tmp_path / "benchmark" / "vendor" / "customx"
    task_dir = vendor_root / "competitions" / "task-a"
    task_dir.mkdir(parents=True)
    (task_dir / "prepare.py").write_text("def prepare(raw, public, private):\n    return public\n", encoding="utf-8")
    (task_dir / "prepare_val.py").write_text(
        "def prepare(raw, public, private):\n    return private\n",
        encoding="utf-8",
    )

    loader = MLETaskContractLoader(
        BenchmarkSourceDescriptor(
            source_id="customx",
            contract_id="mle_task_contract/v1",
            engine_id="mle",
            vendor_root=vendor_root,
            registry_root=vendor_root / "competitions",
        )
    )

    resolved = loader.resolve_callable_ref(
        task_dir,
        "file:vendor/customx/competitions/task-a/prepare.py:prepare",
        mode="validation",
    )

    assert resolved.endswith("prepare_val.py:prepare")
