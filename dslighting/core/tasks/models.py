from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from dslighting.benchmark.evaluation.models import TaskEvaluationContract, TaskEvaluationContractRef
from dslighting.benchmark.grading.models import SubmissionArtifactContract

@dataclass(frozen=True)
class ResolvedTaskLayout:
    task_id: str
    source_id: str
    engine_id: str
    task_type: str
    registry_root: Path
    task_root: Path
    data_root: Path
    agent_visible_dir: Path
    description_text: str
    sample_submission_path: Path | None
    submission_filename: str
    submission_format: str
    submission_context: dict[str, Any]
    output_path: Path
    evaluation_contract: TaskEvaluationContract
    evaluation_contract_ref: TaskEvaluationContractRef


@dataclass(frozen=True)
class TaskExecutionSpec:
    task_id: str
    task_type: str
    description_text: str
    io_instructions: str
    agent_visible_dir: Path
    output_path: Path
    metric_name: str | None = None
    lower_is_better: bool | None = None
    source_id: str | None = None
    engine_id: str | None = None
    submission_artifact_contract: SubmissionArtifactContract | None = None
    evaluation_contract_ref: TaskEvaluationContractRef | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "description_text": self.description_text,
            "io_instructions": self.io_instructions,
            "agent_visible_dir": str(self.agent_visible_dir),
            "output_path": str(self.output_path),
            "metric_name": self.metric_name,
            "lower_is_better": self.lower_is_better,
            "source_id": self.source_id,
            "engine_id": self.engine_id,
            "submission_artifact_contract": (
                self.submission_artifact_contract.to_payload().get("submission_artifact_contract")
                if self.submission_artifact_contract
                else None
            ),
            "evaluation_contract_ref": (
                self.evaluation_contract_ref.to_payload().get("evaluation_contract_ref")
                if self.evaluation_contract_ref
                else None
            ),
        }

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "description": self.description_text,
            "io_instructions": self.io_instructions,
            "agent_visible_data_dir": str(self.agent_visible_dir),
            # Keep the old key only as a transition field for legacy payload readers.
            "public_data_dir": str(self.agent_visible_dir),
            "output_submission_path": str(self.output_path),
            "execution_spec": self.as_dict(),
        }
        if self.metric_name:
            payload["metric_name"] = self.metric_name
        if self.lower_is_better is not None:
            payload["lower_is_better"] = self.lower_is_better
        if self.source_id:
            payload["source_id"] = self.source_id
        if self.engine_id:
            payload["engine_id"] = self.engine_id
        if self.submission_artifact_contract is not None:
            payload.update(self.submission_artifact_contract.to_payload())
        if self.evaluation_contract_ref is not None:
            payload.update(self.evaluation_contract_ref.to_payload())
        return payload
