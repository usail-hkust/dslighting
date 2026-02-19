from pathlib import Path

import pytest

from dslighting.core.application.task_input_resolver import TaskInputResolver
from dslighting.error import TaskError


class _Ctx:
    def __init__(self, task_id: str, data_dir: str):
        self.task_id = task_id
        self.data_dir = data_dir


def test_resolve_from_context_and_description_override(tmp_path: Path) -> None:
    ctx = _Ctx(task_id="bike-sharing-demand", data_dir=str(tmp_path))
    resolved = TaskInputResolver.resolve(
        task_id=None,
        data=ctx,
        task="fallback task",
        output="submission.csv",
        description="explicit description",
        data_dir=None,
        registry_dir=None,
        run_kwargs={"max_iterations": 3},
    )

    assert resolved.task_id == "bike-sharing-demand"
    assert resolved.data_dir == tmp_path
    assert resolved.task_description == "explicit description"
    assert resolved.run_kwargs == {"max_iterations": 3}


def test_resolve_task_id_from_file_path(tmp_path: Path) -> None:
    comp_dir = tmp_path / "my-comp"
    comp_dir.mkdir()
    file_path = comp_dir / "train.csv"
    file_path.write_text("x,y\n1,2\n")

    resolved = TaskInputResolver.resolve(
        task_id=None,
        data=file_path,
        task=None,
        output=None,
        description=None,
        data_dir=None,
        registry_dir=None,
        run_kwargs={},
    )

    assert resolved.task_id == "my-comp"
    assert resolved.data_dir == comp_dir


def test_resolve_missing_task_id_raises() -> None:
    with pytest.raises(TaskError) as exc:
        TaskInputResolver.resolve(
            task_id=None,
            data=None,
            task="some task",
            output=None,
            description=None,
            data_dir=None,
            registry_dir=None,
            run_kwargs={},
        )

    assert exc.value.error_code == "TSK-005"
