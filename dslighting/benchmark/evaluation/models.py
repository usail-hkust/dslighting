from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Literal, Mapping

from dslighting.benchmark.evaluation.outcome import EvaluationOutcome
from dslighting.benchmark.grading.models import TaskGradingContract


@dataclass(frozen=True)
class TaskJudgeContract:
    task_id: str
    source_id: str
    engine_id: str
    api_version: str
    rubric_path: Path | None
    reference_artifacts_dir: Path | None
    judge_metadata: Mapping[str, Any]
    judge_fn: Callable[..., "EvaluationOutcome | Awaitable[EvaluationOutcome]"] | None = None


@dataclass(frozen=True)
class EvaluationSemantics:
    objective: Literal["higher_is_better", "lower_is_better"]
    leaderboard_path: Path | None


@dataclass(frozen=True)
class TaskEvaluationContract:
    task_id: str
    source_id: str
    engine_id: str
    evaluation_mode: Literal["artifact_submission", "judge_based"]
    api_version: str
    evaluation_semantics: EvaluationSemantics
    grading: TaskGradingContract | None
    judging: TaskJudgeContract | None


@dataclass(frozen=True)
class TaskEvaluationContractRef:
    task_id: str
    source_id: str
    engine_id: str
    evaluation_mode: str
    api_version: str
    registry_root: Path | None
    data_root: Path | None
    mode: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "evaluation_contract_ref": {
                "task_id": self.task_id,
                "source_id": self.source_id,
                "engine_id": self.engine_id,
                "evaluation_mode": self.evaluation_mode,
                "api_version": self.api_version,
                "registry_root": str(self.registry_root) if self.registry_root else "",
                "data_root": str(self.data_root) if self.data_root else "",
                "mode": self.mode,
            }
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "TaskEvaluationContractRef | None":
        nested = payload.get("evaluation_contract_ref")
        if not isinstance(nested, Mapping):
            return None
        task_id = str(nested.get("task_id") or "").strip()
        if not task_id:
            return None
        registry_value = str(nested.get("registry_root") or "").strip()
        data_value = str(nested.get("data_root") or "").strip()
        return cls(
            task_id=task_id,
            source_id=str(nested.get("source_id") or "").strip(),
            engine_id=str(nested.get("engine_id") or "").strip(),
            evaluation_mode=str(nested.get("evaluation_mode") or "").strip(),
            api_version=str(nested.get("api_version") or "").strip(),
            registry_root=Path(registry_value) if registry_value else None,
            data_root=Path(data_value) if data_value else None,
            mode=str(nested.get("mode") or "test").strip() or "test",
        )
