from __future__ import annotations

import pytest

pytest.importorskip("nbformat")

from dslighting.config import DSLightingConfig
from dslighting.core.types import TaskDefinition
from dslighting.runner import RuntimeConfigParser


def test_runtime_config_parser_applies_metric_semantics_to_agent_context() -> None:
    task = TaskDefinition(
        task_id="metric-task",
        task_type="kaggle",
        payload={
            "description": "predict something",
            "io_instructions": "write submission.csv",
            "metric_name": "score",
            "lower_is_better": False,
        },
    )
    config = DSLightingConfig()

    parser = RuntimeConfigParser(task, config)
    updated = parser.apply_agent_task_context()

    assert updated.agent.task_context["metric_name"] == "score"
    assert updated.agent.task_context["lower_is_better"] is False
