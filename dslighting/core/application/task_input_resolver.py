"""Resolve user-facing agent inputs into a normalized execution payload."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union

from dslighting.error import TaskError


@dataclass
class ResolvedTaskInput:
    """Normalized input payload for agent execution."""

    task_id: str
    data_dir: Optional[Path] = None
    registry_dir: Optional[Union[str, Path]] = None
    task_description: Optional[str] = None
    output: Optional[Union[str, Path]] = None
    run_kwargs: Dict[str, Any] = field(default_factory=dict)


class TaskInputResolver:
    """Resolve task_id/data/task/output from mixed API inputs."""

    @staticmethod
    def resolve(
        *,
        task_id: Optional[str],
        data: Any,
        task: Optional[str],
        output: Optional[Union[str, Path]],
        description: Optional[str],
        data_dir: Optional[Union[str, Path]],
        registry_dir: Optional[Union[str, Path]],
        run_kwargs: Dict[str, Any],
    ) -> ResolvedTaskInput:
        resolved_task_id = task_id or TaskInputResolver.extract_task_id(data)
        if not resolved_task_id:
            raise TaskError(
                "Cannot determine task_id. Pass `task_id=` explicitly, or provide "
                "a TaskContext/path that includes the competition directory.",
                error_code="TSK-005",
            )

        resolved_data_dir = TaskInputResolver.extract_data_dir(
            data=data,
            data_dir_arg=data_dir,
        )

        return ResolvedTaskInput(
            task_id=resolved_task_id,
            data_dir=resolved_data_dir,
            registry_dir=registry_dir,
            task_description=description or task,
            output=output,
            run_kwargs=run_kwargs,
        )

    @staticmethod
    def extract_task_id(data: Any) -> Optional[str]:
        if data is None:
            return None

        context_task_id = getattr(data, "task_id", None)
        if context_task_id:
            return str(context_task_id)

        if isinstance(data, (str, Path)):
            path = Path(data)
            if path.is_file():
                return path.parent.name
            return path.name

        return None

    @staticmethod
    def extract_data_dir(
        *,
        data: Any,
        data_dir_arg: Optional[Union[str, Path]],
    ) -> Optional[Path]:
        if data_dir_arg is not None:
            return Path(data_dir_arg)

        context_data_dir = getattr(data, "data_dir", None)
        if context_data_dir is not None:
            return Path(context_data_dir)

        if isinstance(data, (str, Path)):
            candidate = Path(data)
            if candidate.is_file():
                return candidate.parent
            if candidate.exists():
                return candidate

        return None

