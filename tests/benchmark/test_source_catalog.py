from __future__ import annotations

from pathlib import Path

import yaml

from dslighting.benchmark.core.source_catalog import BenchmarkSourceCatalog


def _write_task_contract(registry_root: Path, task_id: str) -> None:
    task_dir = registry_root / task_id
    task_dir.mkdir(parents=True)
    (task_dir / "prepare.py").write_text(
        "def prepare(raw, public, private):\n    return public\n\n"
        "def prepare_val(raw, public, private):\n    return public\n",
        encoding="utf-8",
    )
    (task_dir / "grade.py").write_text(
        "def grade(submission, answers):\n    return 1.0\n",
        encoding="utf-8",
    )
    (task_dir / "description.md").write_text("Synthetic task description", encoding="utf-8")
    (task_dir / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "id": task_id,
                "name": "Synthetic task",
                "competition_type": "tabular",
                "description": f"vendor/customx/competitions/{task_id}/description.md",
                "preparer": f"file:vendor/customx/competitions/{task_id}/prepare.py:prepare",
                "grader": {
                    "name": "StandardGrader",
                    "grade_fn": f"file:vendor/customx/competitions/{task_id}/grade.py:grade",
                },
                "dataset": {
                    "answers": f"{task_id}/prepared/private/answers.csv",
                    "sample_submission": f"{task_id}/prepared/public/sample_submission.csv",
                },
            }
        ),
        encoding="utf-8",
    )


def test_source_catalog_resolves_manifest_defined_source_without_task_prefix(tmp_path: Path) -> None:
    vendor_root = tmp_path / "benchmark" / "vendor" / "customx"
    registry_root = vendor_root / "competitions"
    registry_root.mkdir(parents=True)
    (vendor_root / "benchmark.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "source_id": "customx",
                "contract_id": "mle_task_contract/v1",
                "engine_id": "mle",
                "registry_root": "competitions",
                "default_data_env_var": "DSLIGHTING_CUSTOMX_DATA",
            }
        ),
        encoding="utf-8",
    )
    _write_task_contract(registry_root, "plain-task")

    catalog = BenchmarkSourceCatalog()
    resolved = catalog.resolve_task("plain-task", search_hints=[tmp_path])

    assert resolved.descriptor.source_id == "customx"
    assert resolved.registry_root == registry_root.resolve()
    assert resolved.task_dir == (registry_root / "plain-task").resolve()


def test_source_catalog_discovers_legacy_registry_root_without_manifest(tmp_path: Path) -> None:
    registry_root = tmp_path / "benchmark" / "vendor" / "legacybench" / "competitions"
    registry_root.mkdir(parents=True)
    _write_task_contract(registry_root, "legacy-task")

    catalog = BenchmarkSourceCatalog()
    resolved = catalog.resolve_task("legacy-task", search_hints=[tmp_path])

    assert resolved.registry_root == registry_root.resolve()
    assert resolved.descriptor.contract_id == "mle_task_contract/v1"
    assert resolved.descriptor.engine_id == "mle"
