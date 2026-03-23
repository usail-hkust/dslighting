from __future__ import annotations

from abc import ABC, abstractmethod
import contextlib
from dataclasses import replace
import logging
from pathlib import Path
import tempfile
from typing import Any, Mapping, Protocol

from dslighting.config import DSLightingConfig
from dslighting.benchmark.evaluation.models import TaskEvaluationContractRef
from dslighting.benchmark.grading.models import SubmissionArtifactContract
from dslighting.core.tasks.errors import TaskExecutionSpecError
from dslighting.core.tasks.models import ResolvedTaskLayout, TaskExecutionSpec
from dslighting.core.types import TaskDefinition
from dslighting.services.data_analysis_provider import create_data_perception_runtime

logger = logging.getLogger(__name__)


class TaskAdapter(Protocol):
    def build_execution_spec(self, task: TaskDefinition) -> TaskExecutionSpec: ...
    def parse_output(self, output_path: Path) -> Any: ...
    def cleanup(self) -> None: ...


class BaseTaskAdapter(ABC):
    def __init__(self, config: DSLightingConfig) -> None:
        self._config = config
        self.temp_dir = None
        try:
            self.temp_dir = tempfile.TemporaryDirectory()
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to create temporary directory for %s: %s", self.__class__.__name__, exc)
        self.data_perception = self._create_data_perception_runtime(config)

    @staticmethod
    def _create_data_perception_runtime(config: DSLightingConfig):
        try:
            return create_data_perception_runtime(config)
        except ModuleNotFoundError as exc:  # pragma: no cover - dependency-gated
            raise ModuleNotFoundError(
                "Data perception optional dependencies are missing. "
                "Install benchmark/data-analysis dependencies (e.g., numpy/pandas)."
            ) from exc

    @staticmethod
    def _coerce_execution_spec(task: TaskDefinition) -> TaskExecutionSpec | None:
        payload = task.payload if isinstance(task.payload, dict) else {}
        spec = payload.get("execution_spec")
        if isinstance(spec, TaskExecutionSpec):
            return spec
        if isinstance(spec, Mapping):
            submission_contract = None
            contract_payload = spec.get("submission_artifact_contract") or spec.get("submission_contract")
            if isinstance(contract_payload, Mapping):
                submission_contract = SubmissionArtifactContract.from_payload(
                    {"submission_artifact_contract": contract_payload}
                )
            evaluation_contract_ref = None
            ref_payload = spec.get("evaluation_contract_ref")
            if isinstance(ref_payload, Mapping):
                evaluation_contract_ref = TaskEvaluationContractRef.from_payload(
                    {"evaluation_contract_ref": ref_payload}
                )
            return TaskExecutionSpec(
                task_id=str(spec.get("task_id") or task.task_id),
                task_type=str(spec.get("task_type") or task.task_type),
                description_text=str(spec.get("description_text") or ""),
                io_instructions=str(spec.get("io_instructions") or ""),
                agent_visible_dir=Path(spec["agent_visible_dir"]),
                output_path=Path(spec["output_path"]),
                metric_name=str(spec.get("metric_name") or "").strip() or None,
                lower_is_better=spec.get("lower_is_better")
                if isinstance(spec.get("lower_is_better"), bool)
                else None,
                source_id=str(spec.get("source_id") or "") or None,
                engine_id=str(spec.get("engine_id") or "") or None,
                submission_artifact_contract=submission_contract,
                evaluation_contract_ref=evaluation_contract_ref,
            )
        return None

    @staticmethod
    def build_file_submission_spec(layout: ResolvedTaskLayout, perception_runtime) -> TaskExecutionSpec:
        data_report = ""
        submission_contract = layout.evaluation_contract.grading.submission if layout.evaluation_contract.grading else None
        if submission_contract is None:
            raise TaskExecutionSpecError(
                f"Task '{layout.task_id}' does not have an artifact submission contract."
            )
        io_instructions = (
            "All input data files are located in the current working directory (./).\n"
            f"You MUST save the final submission artifact to `{layout.output_path.name}` in the current working directory."
        )
        if perception_runtime is not None:
            data_report = perception_runtime.analyze_data(
                layout.agent_visible_dir,
                task_type=layout.task_type,
                task_id=layout.task_id,
                submission_context=layout.submission_context,
            )
            io_instructions = perception_runtime.generate_io_instructions(
                layout.output_path.name,
                optimization_context=False,
                submission_context=layout.submission_context,
            )
        elif submission_contract.root_kind == "directory":
            required_files = ", ".join(
                f"`{entry.relative_path}`"
                for entry in submission_contract.entries
                if entry.relative_path
            )
            io_instructions = (
                "All input data files are located in the current working directory (./).\n"
                f"You MUST create the submission directory `{layout.output_path.name}` in the current working directory.\n"
                f"The directory must contain: {required_files}."
            )
        submission_contract = submission_contract.with_output_path(layout.output_path)
        lower_is_better = layout.evaluation_contract.evaluation_semantics.objective == "lower_is_better"
        return TaskExecutionSpec(
            task_id=layout.task_id,
            task_type=layout.task_type,
            description_text=f"{layout.description_text}\n\n{data_report}" if data_report else layout.description_text,
            io_instructions=io_instructions,
            agent_visible_dir=layout.agent_visible_dir,
            output_path=layout.output_path,
            metric_name="score",
            lower_is_better=lower_is_better,
            source_id=layout.source_id,
            engine_id=layout.engine_id,
            submission_artifact_contract=submission_contract,
            evaluation_contract_ref=layout.evaluation_contract_ref,
        )

    def cleanup(self) -> None:
        temp_dir = getattr(self, "temp_dir", None)
        if temp_dir:
            try:
                temp_dir.cleanup()
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Error cleaning up %s: %s", self.__class__.__name__, exc)

    def __del__(self) -> None:  # pragma: no cover - best effort
        with contextlib.suppress(Exception):
            self.cleanup()

    @abstractmethod
    def build_execution_spec(self, task: TaskDefinition) -> TaskExecutionSpec:
        raise NotImplementedError

    @abstractmethod
    def parse_output(self, output_path: Path) -> Any:
        raise NotImplementedError


class FileSubmissionTaskAdapter(BaseTaskAdapter):
    def build_execution_spec(self, task: TaskDefinition) -> TaskExecutionSpec:
        existing = self._coerce_execution_spec(task)
        if existing is not None:
            return existing

        payload = task.payload if isinstance(task.payload, dict) else {}
        description = str(payload.get("description") or "").strip()
        data_dir_value = (
            payload.get("agent_visible_data_dir")
            or payload.get("public_data_dir")
        )
        output_value = payload.get("output_submission_path")
        if not description or not data_dir_value or not output_value:
            raise TaskExecutionSpecError(
                "File submission task payload is missing required keys: "
                "'description', 'agent_visible_data_dir/public_data_dir', 'output_submission_path'."
            )

        data_dir = Path(str(data_dir_value))
        if not data_dir.exists() or not data_dir.is_dir():
            raise FileNotFoundError(f"Agent-visible data directory not found: {data_dir}")

        submission_contract = SubmissionArtifactContract.from_payload(payload)
        submission_context = submission_contract.to_payload() if submission_contract else {"output_submission_path": str(output_value)}
        evaluation_contract_ref = TaskEvaluationContractRef.from_payload(payload)
        data_report = ""
        if self.data_perception is not None:
            data_report = self.data_perception.analyze_data(
                data_dir,
                task_type="kaggle",
                task_id=task.task_id,
                submission_context=submission_context,
            )
        io_instructions = str(payload.get("io_instructions") or "").strip()
        if not io_instructions:
            if self.data_perception is not None:
                io_instructions = self.data_perception.generate_io_instructions(
                    Path(output_value).name,
                    optimization_context=False,
                    submission_context=submission_context,
                )
            elif submission_contract is not None and submission_contract.root_kind == "directory":
                required_files = ", ".join(
                    f"`{entry.relative_path}`"
                    for entry in submission_contract.entries
                    if entry.relative_path
                )
                io_instructions = (
                    "All input data files are in the current working directory.\n"
                    f"Create the submission directory `{Path(output_value).name}` in the current working directory.\n"
                    f"The directory must contain: {required_files}."
                )
            else:
                io_instructions = (
                    "All input data files are in the current working directory.\n"
                    f"Save the final submission artifact to `{Path(output_value).name}` in the current working directory."
                )
        return TaskExecutionSpec(
            task_id=task.task_id,
            task_type=task.task_type,
            description_text=f"{description}\n\n{data_report}" if data_report else description,
            io_instructions=io_instructions,
            agent_visible_dir=data_dir,
            output_path=Path(str(output_value)),
            metric_name=str(payload.get("metric_name") or "").strip() or None,
            lower_is_better=payload.get("lower_is_better")
            if isinstance(payload.get("lower_is_better"), bool)
            else None,
            source_id=str(payload.get("source_id") or "") or None,
            engine_id=str(payload.get("engine_id") or "") or None,
            submission_artifact_contract=submission_contract,
            evaluation_contract_ref=evaluation_contract_ref,
        )

    def parse_output(self, output_path: Path) -> Path:
        if not output_path.exists():
            logger.warning("Agent did not produce the required submission file at: %s", output_path)
        return output_path


class QATaskAdapter(BaseTaskAdapter):
    def build_execution_spec(self, task: TaskDefinition) -> TaskExecutionSpec:
        existing = self._coerce_execution_spec(task)
        if existing is not None:
            return existing
        if not self.temp_dir:
            raise RuntimeError("Temporary directory not available for QATaskAdapter.")

        payload = task.payload if isinstance(task.payload, dict) else {}
        question = str(payload.get("question") or "").strip()
        if not question:
            raise TaskExecutionSpecError("QA task payload is missing required key: 'question'.")

        data_dir = Path(self.temp_dir.name)
        problem_file = data_dir / "problem.txt"
        problem_file.write_text(question, encoding="utf-8")
        output_path = data_dir / "answer.txt"
        core_instruction = (
            "Your task is to answer the question found in `problem.txt`. "
            "Write ONLY the final answer into the required output file."
        )
        data_report = (
            self.data_perception.analyze_data(data_dir, task_type="qa", task_id=task.task_id)
            if self.data_perception
            else ""
        )
        io_instructions = (
            self.data_perception.generate_io_instructions(
                output_path.name,
                optimization_context=False,
            )
            if self.data_perception
            else f"Write ONLY the final answer into `{output_path.name}`."
        )
        return TaskExecutionSpec(
            task_id=task.task_id,
            task_type=task.task_type,
            description_text=f"{core_instruction}\n{data_report}" if data_report else core_instruction,
            io_instructions=io_instructions,
            agent_visible_dir=data_dir,
            output_path=output_path,
        )

    def parse_output(self, output_path: Path) -> str:
        if not output_path.exists() or not output_path.is_file():
            logger.warning("Agent did not produce the answer file for QA task at: %s", output_path)
            return "[ERROR] Agent did not produce an answer file."
        try:
            return output_path.read_text(encoding="utf-8").strip()
        except Exception as exc:
            logger.error("Failed to parse QA answer file '%s': %s", output_path, exc)
            return f"[ERROR] Failed to parse answer file: {exc}"


class DataScienceTaskAdapter(BaseTaskAdapter):
    def build_execution_spec(self, task: TaskDefinition) -> TaskExecutionSpec:
        existing = self._coerce_execution_spec(task)
        if existing is not None:
            return existing

        payload = task.payload if isinstance(task.payload, dict) else {}
        prompt = str(payload.get("prompt") or "").strip()
        input_dir = str(payload.get("input_dir") or "").strip()
        output_dir = str(payload.get("output_dir") or "").strip()
        if not prompt:
            raise TaskExecutionSpecError("Data science task payload is missing required key: 'prompt'.")

        if input_dir and Path(input_dir).exists():
            data_dir = Path(input_dir)
        elif self.temp_dir:
            data_dir = Path(self.temp_dir.name)
        else:
            raise RuntimeError("No data directory available for DataScienceTaskAdapter.")

        output_path = (Path(output_dir) / "output.csv") if output_dir else (data_dir / "output.csv")
        description_text = prompt
        if self.data_perception is not None:
            try:
                data_report = self.data_perception.analyze_data(
                    data_dir,
                    task_type="datasci",
                    task_id=task.task_id,
                )
                description_text = f"{prompt}\n\n{data_report}"
            except Exception as exc:  # pragma: no cover - best effort
                logger.debug("Data analysis skipped: %s", exc)

        io_instructions = (
            "All input data files are in the current working directory.\n"
            "Save all output files to the current working directory.\n"
            "Follow the task instructions carefully and generate the required output files."
        )
        return TaskExecutionSpec(
            task_id=task.task_id,
            task_type=task.task_type,
            description_text=description_text,
            io_instructions=io_instructions,
            agent_visible_dir=data_dir,
            output_path=output_path,
        )

    def parse_output(self, output_path: Path) -> Path:
        return output_path.parent if output_path.parent.exists() else output_path


class OpenEndedTaskAdapter(BaseTaskAdapter):
    def build_execution_spec(self, task: TaskDefinition) -> TaskExecutionSpec:
        existing = self._coerce_execution_spec(task)
        if existing is not None:
            return existing
        if not self.temp_dir:
            raise RuntimeError("Temporary directory not available for OpenEndedTaskAdapter.")

        payload = task.payload if isinstance(task.payload, dict) else {}
        raw_dir_str = str(payload.get("raw_data_dir") or "").strip()
        description_file = str(payload.get("description_file") or "").strip()
        rubric_file = str(payload.get("rubric_file") or "").strip()

        data_dir = Path(self.temp_dir.name)
        if raw_dir_str:
            raw_dir = Path(raw_dir_str)
            if raw_dir.exists():
                import shutil

                for file in raw_dir.iterdir():
                    if file.is_file() and file.suffix in [".csv", ".json", ".txt", ".xlsx", ".parquet"]:
                        if file.name not in ["description.md", "rubric.md"]:
                            shutil.copy2(file, data_dir / file.name)

        description = str(payload.get("description") or "")
        rubric = str(payload.get("rubric") or "")
        if description_file and Path(description_file).exists():
            description = Path(description_file).read_text(encoding="utf-8")
        if rubric_file and Path(rubric_file).exists():
            rubric = Path(rubric_file).read_text(encoding="utf-8")
        if not description:
            raise TaskExecutionSpecError("Open-ended task payload is missing required key: 'description'.")

        output_path = data_dir / "artifacts"
        task_description_section = f"## Task Description\n\n{description}\n"
        if rubric:
            task_description_section += f"\n## Evaluation Criteria\n\n{rubric}\n"
        data_report = (
            self.data_perception.analyze_data(data_dir, task_type="datasci", task_id=task.task_id)
            if self.data_perception
            else ""
        )
        full_description = task_description_section
        if data_report:
            full_description = f"{full_description}\n\n{data_report}"
        full_description = (
            f"{full_description}\n\n"
            "## CRITICAL OUTPUT INSTRUCTIONS\n\n"
            "**YOU MUST CREATE AN `artifacts/` DIRECTORY AND SAVE ALL OUTPUTS THERE.**\n"
        )
        io_instructions = (
            "Create the `artifacts/` directory at the beginning of your code.\n"
            "Save all generated files to this directory.\n"
            "Do NOT save files to the current directory - use the artifacts/ subdirectory."
        )
        return TaskExecutionSpec(
            task_id=task.task_id,
            task_type=task.task_type,
            description_text=full_description,
            io_instructions=io_instructions,
            agent_visible_dir=data_dir,
            output_path=output_path,
        )

    def parse_output(self, output_path: Path) -> Path:
        if not output_path.exists():
            logger.warning("Open-ended task did not create artifacts directory at: %s", output_path)
            return output_path.parent
        return output_path
