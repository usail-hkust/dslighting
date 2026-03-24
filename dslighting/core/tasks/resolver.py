from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import yaml

from dslighting.benchmark.core.source_catalog import get_benchmark_source_catalog
from dslighting.benchmark.evaluation.contract_builder import build_task_evaluation_contract
from dslighting.core.tasks.errors import TaskLayoutResolutionError
from dslighting.core.tasks.models import ResolvedTaskLayout
from dslighting.core.tasks.output_artifact import resolve_output_artifact_path_for_competition


class TaskResolver:
    """Resolve task registry/data layout into a single execution-safe view."""

    def __init__(self) -> None:
        self._catalog = get_benchmark_source_catalog()

    @staticmethod
    def _normalize_path(value: str | Path | None) -> Path | None:
        if value is None:
            return None
        return Path(value).expanduser().resolve()

    @staticmethod
    def _is_task_root(task_id: str, path: Path) -> bool:
        return path.name == task_id and (path / "config.yaml").exists()

    @staticmethod
    def _infer_registry_hint(task_id: str, data_path: Path | None) -> Path | None:
        if data_path is None:
            return None

        if TaskResolver._is_task_root(task_id, data_path):
            return data_path.parent

        candidate = data_path / task_id / "config.yaml"
        if candidate.exists():
            return data_path

        if data_path.name in {"public", "public_val"} and data_path.parent.name in {"prepared", "prepared_val"}:
            task_root = data_path.parent.parent
            if TaskResolver._is_task_root(task_id, task_root):
                return task_root.parent

        return None

    @staticmethod
    def _infer_data_root(task_id: str, data_path: Path | None) -> Path:
        if data_path is None:
            raise TaskLayoutResolutionError(
                f"Cannot infer data root for task '{task_id}'. "
                "Pass `data=` as a registry root, task root, or prepared/public path."
            )

        if data_path.name in {"public", "public_val"} and data_path.parent.name in {"prepared", "prepared_val"}:
            return data_path.parent.parent.parent
        if data_path.name == task_id and (data_path / "prepared").exists():
            return data_path.parent
        if (data_path / task_id / "prepared").exists():
            return data_path
        return data_path

    @staticmethod
    def _build_layout_error(task_id: str, data_path: Path | None, registry_dir: Path | None) -> TaskLayoutResolutionError:
        data_display = str(data_path) if data_path is not None else "None"
        registry_display = str(registry_dir) if registry_dir is not None else "None"
        return TaskLayoutResolutionError(
            f"Cannot resolve task layout for task '{task_id}' from:\n"
            f"  data={data_display}\n"
            f"  registry_dir={registry_display}\n\n"
            "Accepted path shapes are:\n"
            "1. registry root:\n"
            f"   <path>/{task_id}/config.yaml\n"
            "2. task root:\n"
            f"   <path>/config.yaml where directory name == '{task_id}'\n"
            "3. public dir:\n"
            f"   <path>/{task_id}/prepared/public\n\n"
            "If registry files and dataset are stored separately, pass `registry_dir=` explicitly."
        )

    @staticmethod
    def _load_task_config(task_root: Path) -> dict[str, Any]:
        config_path = task_root / "config.yaml"
        with open(config_path, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    def resolve(
        self,
        *,
        task_id: str,
        data: str | Path | None = None,
        registry_dir: str | Path | None = None,
        data_view: str = "public",
    ) -> ResolvedTaskLayout:
        data_path = self._normalize_path(data)
        explicit_registry = self._normalize_path(registry_dir)
        inferred_registry = explicit_registry or self._infer_registry_hint(task_id, data_path)
        search_hints = [hint for hint in (data_path, explicit_registry, Path.cwd()) if hint is not None]

        try:
            resolved_source = self._catalog.resolve_task(
                task_id,
                registry_dir=inferred_registry,
                search_hints=search_hints,
            )
        except Exception as exc:
            raise self._build_layout_error(task_id, data_path, explicit_registry) from exc

        task_root = resolved_source.task_dir.resolve() if resolved_source.task_dir else (resolved_source.registry_root / task_id).resolve()
        config = self._load_task_config(task_root)
        task_type = str(config.get("task_type") or "kaggle").strip() or "kaggle"

        data_root = self._infer_data_root(task_id, data_path or task_root)
        registry = self._catalog.build_registry(resolved_source.descriptor, data_root=data_root)
        competition = registry.get_competition(task_id)

        if task_type == "open_ended":
            agent_visible_dir = competition.raw_dir.resolve()
        elif data_view == "raw":
            agent_visible_dir = competition.raw_dir.resolve()
        else:
            agent_visible_dir = competition.public_dir.resolve()

        if not agent_visible_dir.exists():
            raise TaskLayoutResolutionError(
                f"Agent-visible directory not found for task '{task_id}': {agent_visible_dir}\n"
                "Pass a valid prepared dataset or ensure the benchmark data is prepared."
            )

        preferred_submission_name = getattr(competition, "submission_filename", None)
        sample_submission_path = getattr(competition, "sample_submission", None)
        output_path = resolve_output_artifact_path_for_competition(
            task_id=task_id,
            competition=competition,
            unique_suffix=uuid.uuid4().hex[:6],
        )

        submission_filename = preferred_submission_name or (
            sample_submission_path.name if isinstance(sample_submission_path, Path) else ""
        )
        submission_format = output_path.suffix.lower()
        evaluation_contract, evaluation_contract_ref = build_task_evaluation_contract(
            competition=competition,
            source_id=resolved_source.descriptor.source_id,
            engine_id=resolved_source.descriptor.engine_id,
            registry_root=resolved_source.registry_root.resolve(),
            data_root=data_root.resolve(),
            mode="test",
            output_submission_path=output_path,
            evaluation_mode="judge_based" if task_type == "open_ended" else "artifact_submission",
        )
        submission_context = {
            "sample_submission_path": str(sample_submission_path) if isinstance(sample_submission_path, Path) else "",
            "submission_filename": submission_filename,
            "submission_format": submission_format,
            "output_submission_path": str(output_path),
        }
        if evaluation_contract.grading is not None:
            submission_context.update(evaluation_contract.grading.submission.to_payload())

        return ResolvedTaskLayout(
            task_id=task_id,
            source_id=resolved_source.descriptor.source_id,
            engine_id=resolved_source.descriptor.engine_id,
            task_type=task_type,
            registry_root=resolved_source.registry_root.resolve(),
            task_root=task_root.resolve(),
            data_root=data_root.resolve(),
            agent_visible_dir=agent_visible_dir,
            description_text=str(competition.description),
            sample_submission_path=sample_submission_path.resolve() if isinstance(sample_submission_path, Path) else None,
            submission_filename=submission_filename,
            submission_format=submission_format,
            submission_context=submission_context,
            output_path=output_path,
            evaluation_contract=evaluation_contract,
            evaluation_contract_ref=evaluation_contract_ref,
        )
