"""dslighting.tools.dsflow.core.task_helpers

Task and configuration helpers for DSFlow.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

from dslighting.config import DSFlowConfig
from dslighting.core.data.perception import DataPerceptionRuntime
from dslighting.tools.dsflow.core.models import TaskContext as _TaskContext


class TaskHelpers:
    def _progress_enabled(self) -> bool:
        return bool(getattr(self.dsflow_config, "progress_enabled", True))

    @staticmethod
    def _load_dsflow_config(agent_config: Dict[str, Any]) -> DSFlowConfig:
        """
        Load DSFlow config from `agent_config["dsflow"]`.

        Backward compatible: if `dsflow` is missing, seed from `agent_config["optimizer"]`
        (AFlow-style keys) and fill the rest with DSFlow defaults.
        """
        payload = agent_config.get("dsflow")
        if isinstance(payload, dict):
            return DSFlowConfig.model_validate(payload)

        legacy = agent_config.get("optimizer", {})
        if not isinstance(legacy, dict):
            legacy = {}
        merged = DSFlowConfig().model_dump()
        for key in ("max_rounds", "top_k_selection"):
            if key in legacy:
                merged[key] = legacy[key]
        return DSFlowConfig.model_validate(merged)

    def _prepare_tasks(self, competition_ids: list[str]) -> list[_TaskContext]:
        analyzer = self.data_perception or DataPerceptionRuntime()
        tasks: list[_TaskContext] = []
        for competition_id in competition_ids:
            raw_description, data_dir = self._get_problem_description_and_data_dir(competition_id)
            base_report = analyzer.analyze_data(data_dir, task_type="kaggle")
            tasks.append(
                _TaskContext(
                    competition_id=competition_id,
                    raw_description=raw_description,
                    data_dir=data_dir,
                    base_report=base_report,
                )
            )
        return tasks

    @staticmethod
    def _infer_task_types(tasks: list[_TaskContext]) -> set[str]:
        types: set[str] = set()
        for task in tasks:
            text = f"{task.raw_description}\n{task.base_report}".lower()
            if "train.csv" in text and "test.csv" in text:
                types.add("tabular")
            if re.search(r"\\.(jpg|jpeg|png|gif|bmp|tif|tiff)\\b", text):
                types.add("vision")
            if re.search(r"\\.(mp3|wav|flac|ogg)\\b", text):
                types.add("audio")
            if re.search(r"\\b(text|nlp|token|sentence)\\b", text):
                types.add("nlp")
        return types

    def _get_problem_description_and_data_dir(self, competition_id: str) -> tuple[str, Path]:
        from dslighting.tools.dsflow.runtime import get_problem_description_and_data_dir

        return get_problem_description_and_data_dir(
            benchmark=self.benchmark,
            competition_id=competition_id,
            workflow_file=Path(__file__),
        )
