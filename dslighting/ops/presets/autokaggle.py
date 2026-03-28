import csv
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from dslighting.core.visualization_policy import (
    VisualizationPolicy,
    find_blocked_display_usage,
)
from dslighting.ops.base import Operator
from dslighting.services.llm import LLMService
from dslighting.services.sandbox import SandboxService
from dslighting.state.autokaggle import AutoKaggleState, PhaseMemory
from dslighting.core.types import TaskContract
from dslighting.prompts.workflows.autokaggle import (
    get_deconstructor_prompt,
    get_phase_planner_prompt,
    get_step_planner_prompt,
    get_developer_prompt,
    get_validator_prompt,
    get_reviewer_prompt,
    get_summarizer_prompt,
)
from dslighting.core.types import StepPlan, ReviewResponse

logger = logging.getLogger(__name__)


class PhasePlanningResponse(BaseModel):
    """Response model for phase planning."""
    phases: List[str]


class ValidationResponse(BaseModel):
    """Response model for file validation."""
    passed: bool
    reason: str = ""


class TaskDeconstructionOperator(Operator):
    """Parses the natural language description into a structured TaskContract."""

    async def __call__(self, description: str) -> TaskContract:
        logger.info("Deconstructing task description into a structured contract...")
        prompt = get_deconstructor_prompt(description, TaskContract.model_json_schema())
        contract = await self.llm_service.call_with_json(prompt, output_model=TaskContract)
        logger.info(f"Task deconstructed. Goal: {contract.task_goal}")
        return contract


class AutoKagglePlannerOperator(Operator):
    """Handles high-level phase planning and low-level step planning."""

    async def __call__(self, *args, **kwargs) -> Any:
        """
        Main entry point for the planner operator.
        Can be called with different arguments for different planning tasks.
        """
        if len(args) == 1 and isinstance(args[0], TaskContract):
            # Called for phase planning
            return await self.plan_phases(args[0])
        elif len(args) == 2 and isinstance(args[0], AutoKaggleState) and isinstance(args[1], str):
            # Called for step planning
            return await self.plan_step_details(args[0], args[1])
        else:
            raise ValueError(f"AutoKagglePlannerOperator called with unexpected arguments: {args}, {kwargs}")

    async def plan_phases(self, contract: TaskContract) -> List[str]:
        logger.info("Planning dynamic phases for the workflow...")
        prompt = get_phase_planner_prompt(contract)
        response = await self.llm_service.call_with_json(prompt, output_model=PhasePlanningResponse)
        phases = response.phases
        logger.info(f"Dynamic phases planned: {phases}")
        return phases

    async def plan_step_details(self, state: AutoKaggleState, phase_goal: str) -> StepPlan:
        logger.info(f"Planning detailed steps for phase: '{phase_goal}'...")
        prompt = get_step_planner_prompt(state, phase_goal)
        step_plan = await self.llm_service.call_with_json(prompt, output_model=StepPlan)
        return step_plan


class DynamicValidationOperator(Operator):
    """Dynamically validates generated files against the TaskContract."""

    _TAG_PATTERN = re.compile(r"@([A-Za-z_][A-Za-z0-9_]*)\[([^\]]*)\]")
    _REQUIRED_CSV_COLUMNS = ("id", "answer")

    def _find_sample_submission_csv(self, contract: TaskContract, workspace_dir: Path) -> Optional[Path]:
        """Locate sample submission CSV in workspace using metadata-first heuristics."""
        candidates: List[Path] = []
        for input_file in contract.input_files:
            candidate = workspace_dir / input_file.filename
            if candidate.exists() and candidate.is_file() and candidate.suffix.lower() == ".csv":
                candidates.append(candidate)

        for candidate in candidates:
            lowered = candidate.name.lower()
            if "sample" in lowered and "submission" in lowered:
                return candidate

        direct_name = workspace_dir / "sample_submission.csv"
        if direct_name.exists() and direct_name.is_file():
            return direct_name

        try:
            root_files = sorted((p for p in workspace_dir.iterdir() if p.is_file()), key=lambda p: p.name.lower())
        except Exception:
            root_files = []

        for file_path in root_files:
            lowered = file_path.name.lower()
            if file_path.suffix.lower() == ".csv" and "sample" in lowered and "submission" in lowered:
                return file_path

        return None

    def _load_csv(self, file_path: Path) -> Dict[str, Any]:
        """
        Deterministically parse a CSV file.
        Returns: {"ok": bool, "columns": List[str], "rows": List[Dict[str, str]], "errors": List[str]}
        """
        result: Dict[str, Any] = {"ok": False, "columns": [], "rows": [], "errors": []}
        try:
            with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                fieldnames = [str(name).strip() for name in (reader.fieldnames or []) if name is not None]
                if not fieldnames:
                    result["errors"].append("CSV is missing a header row.")
                    return result

                rows: List[Dict[str, str]] = []
                for raw_row in reader:
                    normalized_row: Dict[str, str] = {}
                    for key in fieldnames:
                        value = raw_row.get(key)
                        normalized_row[key] = "" if value is None else str(value).strip()
                    rows.append(normalized_row)

                result["ok"] = True
                result["columns"] = fieldnames
                result["rows"] = rows
                return result
        except Exception as exc:
            result["errors"].append(f"File is not parseable as CSV: {exc}")
            return result

    def _find_column(self, columns: List[str], expected_name: str) -> Optional[str]:
        expected = expected_name.lower()
        for column in columns:
            if column.strip().lower() == expected:
                return column
        return None

    def _template_requires_tag_wrappers(self, sample_template: Dict[str, Any]) -> bool:
        if not sample_template.get("ok"):
            return False
        answer_column = self._find_column(sample_template.get("columns", []), "answer")
        if not answer_column:
            return False
        for row in sample_template.get("rows", []):
            value = str(row.get(answer_column, "")).strip()
            if self._TAG_PATTERN.search(value):
                return True
        return False

    def _run_csv_format_checks(
        self,
        *,
        submission_path: Path,
        sample_template: Optional[Dict[str, Any]],
        sample_template_path: Optional[Path],
        sample_template_error: Optional[str],
    ) -> Dict[str, Any]:
        errors: List[str] = []
        submission_csv = self._load_csv(submission_path)
        if not submission_csv.get("ok"):
            errors.extend(str(err) for err in submission_csv.get("errors", []))
            return {"passed": False, "errors": errors}

        columns = submission_csv.get("columns", [])
        missing_columns = [col for col in self._REQUIRED_CSV_COLUMNS if self._find_column(columns, col) is None]
        if missing_columns:
            errors.append(f"Missing required CSV columns: {missing_columns}")

        id_column = self._find_column(columns, "id")
        answer_column = self._find_column(columns, "answer")

        if sample_template_path is not None and sample_template_error:
            errors.append(sample_template_error)

        if sample_template and sample_template.get("ok"):
            template_columns = sample_template.get("columns", [])
            template_id_column = self._find_column(template_columns, "id")
            if template_id_column is None:
                errors.append("sample_submission CSV is missing required 'id' column.")
            elif id_column:
                expected_ids = [str(row.get(template_id_column, "")).strip() for row in sample_template.get("rows", [])]
                actual_ids = [str(row.get(id_column, "")).strip() for row in submission_csv.get("rows", [])]

                if len(actual_ids) != len(expected_ids):
                    errors.append(
                        f"id row count mismatch against sample_submission ({len(actual_ids)} != {len(expected_ids)})."
                    )
                if set(actual_ids) != set(expected_ids):
                    errors.append("id values do not match sample_submission id set.")
                if actual_ids != expected_ids:
                    errors.append("id values do not match sample_submission id order.")

            if self._template_requires_tag_wrappers(sample_template):
                if not answer_column:
                    errors.append("Missing required 'answer' column for tagged-answer validation.")
                else:
                    for row_index, row in enumerate(submission_csv.get("rows", []), start=1):
                        answer_value = str(row.get(answer_column, "")).strip()
                        tags = self._TAG_PATTERN.findall(answer_value)

                        if not tags:
                            errors.append(f"Row {row_index}: missing required @tag[...] wrapper in answer.")
                            continue

                        tag_keys_lower: List[str] = []
                        duplicate_keys: List[str] = []
                        seen_keys = set()
                        for key, _ in tags:
                            lowered_key = key.lower()
                            tag_keys_lower.append(lowered_key)
                            if lowered_key in seen_keys and lowered_key not in duplicate_keys:
                                duplicate_keys.append(lowered_key)
                            seen_keys.add(lowered_key)

                        if "placeholder" in tag_keys_lower:
                            errors.append(f"Row {row_index}: forbidden tag @placeholder[...] detected.")
                        if duplicate_keys:
                            errors.append(f"Row {row_index}: duplicate tag keys detected: {sorted(duplicate_keys)}")

        return {"passed": not errors, "errors": errors}

    async def __call__(self, contract: TaskContract, workspace_dir: Path) -> Dict[str, Any]:
        logger.info("Performing dynamic validation of output files...")
        results: Dict[str, Dict[str, Any]] = {}
        format_file_results: Dict[str, Dict[str, Any]] = {}
        format_errors: List[str] = []
        format_passed = True

        sample_template_path = self._find_sample_submission_csv(contract, workspace_dir)
        sample_template: Optional[Dict[str, Any]] = None
        sample_template_error: Optional[str] = None
        if sample_template_path:
            sample_template = self._load_csv(sample_template_path)
            if not sample_template.get("ok"):
                sample_template_error = (
                    f"sample_submission file '{sample_template_path.name}' exists but could not be parsed as CSV."
                )

        for output_file in contract.output_files:
            file_path = workspace_dir / output_file.filename
            is_csv_submission = file_path.suffix.lower() == ".csv"

            if not file_path.exists():
                results[output_file.filename] = {"passed": False, "reason": "File was not generated."}
                if is_csv_submission:
                    format_result = {"passed": False, "errors": ["File was not generated."]}
                    format_file_results[output_file.filename] = format_result
                    format_passed = False
                    format_errors.extend(
                        f"{output_file.filename}: {error}" for error in format_result.get("errors", [])
                    )
                continue

            llm_passed = False
            llm_reason = ""
            try:
                content_snippet = "\\n".join(file_path.read_text().splitlines()[:20])
                prompt = get_validator_prompt(contract, output_file.filename, content_snippet)
                validation = await self.llm_service.call_with_json(prompt, output_model=ValidationResponse)
                llm_passed = bool(validation.passed)
                llm_reason = str(validation.reason or "")
            except Exception as exc:
                llm_passed = False
                llm_reason = f"Could not validate file: {exc}"

            deterministic_passed = True
            deterministic_errors: List[str] = []
            if is_csv_submission:
                csv_format_result = self._run_csv_format_checks(
                    submission_path=file_path,
                    sample_template=sample_template,
                    sample_template_path=sample_template_path,
                    sample_template_error=sample_template_error,
                )
                format_file_results[output_file.filename] = csv_format_result
                deterministic_passed = bool(csv_format_result.get("passed", False))
                deterministic_errors = [str(err) for err in csv_format_result.get("errors", [])]
                if not deterministic_passed:
                    format_passed = False
                    format_errors.extend(f"{output_file.filename}: {error}" for error in deterministic_errors)

            combined_passed = llm_passed and deterministic_passed
            reason_parts = [part for part in [llm_reason] if part]
            if deterministic_errors:
                reason_parts.append("Deterministic format checks failed: " + "; ".join(deterministic_errors))

            results[output_file.filename] = {
                "passed": combined_passed,
                "reason": " ".join(reason_parts).strip(),
            }

        format_validation_result: Dict[str, Any] = {
            "passed": format_passed,
            "errors": format_errors,
            "files": format_file_results,
        }
        logger.info("Validation results: %s", results)
        logger.info("Format validation results: %s", format_validation_result)
        return {"validation_result": results, "format_validation_result": format_validation_result}


class AutoKaggleDeveloperOperator(Operator):
    """Writes, executes, and validates code."""

    def __init__(
        self,
        llm_service: LLMService,
        sandbox_service: SandboxService,
        validator: DynamicValidationOperator,
        *,
        visualization_policy: VisualizationPolicy = VisualizationPolicy.NO_DISPLAY,
    ):
        super().__init__(llm_service, name="AutoKaggleDeveloper")
        self.sandbox = sandbox_service
        self.validator = validator
        self.visualization_policy = visualization_policy

    def _normalize_format_validation_result(self, raw_result: Any, fallback_reason: str) -> Dict[str, Any]:
        if not isinstance(raw_result, dict):
            return {"passed": False, "errors": [fallback_reason]}

        raw_errors = raw_result.get("errors", [])
        if isinstance(raw_errors, list):
            errors = [str(item) for item in raw_errors]
        elif raw_errors:
            errors = [str(raw_errors)]
        else:
            errors = []

        normalized: Dict[str, Any] = {
            "passed": bool(raw_result.get("passed", False)),
            "errors": errors,
        }
        if isinstance(raw_result.get("files"), dict):
            normalized["files"] = raw_result["files"]
        return normalized

    def _build_execution_code(self, code: str, branch_workdir: Optional[Path]) -> str:
        if branch_workdir is None:
            return code

        branch_literal = str(branch_workdir)
        return (
            "import os\n"
            f"os.makedirs({branch_literal!r}, exist_ok=True)\n"
            f"os.chdir({branch_literal!r})\n"
            + code
        )

    async def __call__(
        self,
        state: AutoKaggleState,
        phase_goal: str,
        plan: str,
        attempt_history: List,
        branch_workdir: Optional[str] = None,
    ) -> Dict:
        logger.info(f"Developer starting work for phase: '{phase_goal}'")
        prompt = get_developer_prompt(
            state,
            phase_goal,
            plan,
            attempt_history,
            visualization_policy=self.visualization_policy,
        )

        raw_reply = await self.llm_service.call(prompt)
        match = re.search(r"```(?:python|py)?\s*([\s\S]*?)\s*```", raw_reply, re.DOTALL)
        code = match.group(1).strip() if match else ""

        if not code:
            reason = "No code was generated."
            return {
                "code": "",
                "status": False,
                "output": "",
                "error": reason,
                "validation_result": {},
                "format_validation_result": {"passed": False, "errors": [reason]},
            }

        blocked_matches = find_blocked_display_usage(code, self.visualization_policy)
        if blocked_matches:
            reason = f"Blocked interactive display usage detected: {', '.join(blocked_matches)}"
            return {
                "code": code,
                "status": False,
                "output": "",
                "error": reason,
                "validation_result": {},
                "format_validation_result": {"passed": False, "errors": [reason]},
            }

        normalized_branch_workdir: Optional[Path] = None
        if branch_workdir:
            normalized_branch_workdir = Path(str(branch_workdir)).resolve()

        execution_code = self._build_execution_code(code, normalized_branch_workdir)
        exec_result = await self.sandbox.run_script(execution_code)

        validation_result = {}
        format_validation_result: Dict[str, Any] = {
            "passed": False,
            "errors": ["Execution failed; format validation was not run."],
        }
        if exec_result.success:
            validation_workspace = (
                normalized_branch_workdir
                if normalized_branch_workdir is not None
                else self.sandbox.workspace.get_path("sandbox_workdir")
            )

            # Note: This still validates against the *final* contract outputs. The reviewer logic handles this.
            validator_output = await self.validator(
                state.contract,
                validation_workspace,
            )

            if isinstance(validator_output, dict) and isinstance(validator_output.get("validation_result"), dict):
                validation_result = dict(validator_output.get("validation_result") or {})
                format_validation_result = self._normalize_format_validation_result(
                    validator_output.get("format_validation_result"),
                    "Validator did not return format_validation_result.",
                )
            elif isinstance(validator_output, dict):
                # Backward compatibility: previous validator shape was direct file-result mapping.
                validation_result = {
                    str(key): value for key, value in validator_output.items() if str(key) != "format_validation_result"
                }
                format_validation_result = self._normalize_format_validation_result(
                    validator_output.get("format_validation_result"),
                    "Format validation result unavailable.",
                )

        return {
            "code": code,
            "status": exec_result.success,
            "output": exec_result.stdout,
            "error": exec_result.stderr,
            "validation_result": validation_result,
            "format_validation_result": format_validation_result,
        }


class AutoKaggleReviewerOperator(Operator):
    """Reviews the developer's work and provides a score and suggestions."""

    def __init__(
        self,
        llm_service: LLMService,
        *,
        visualization_policy: VisualizationPolicy = VisualizationPolicy.NO_DISPLAY,
    ):
        super().__init__(llm_service, name="AutoKaggleReviewer")
        self.visualization_policy = visualization_policy

    async def __call__(self, state: AutoKaggleState, phase_goal: str, dev_result: Dict, plan: str = "") -> Dict:
        logger.info("Reviewer assessing developer's work...")
        prompt = get_reviewer_prompt(
            phase_goal,
            dev_result,
            plan,
            visualization_policy=self.visualization_policy,
        )
        review = await self.llm_service.call_with_json(prompt, output_model=ReviewResponse)
        review_dict = {
            "score": review.score,
            "suggestion": review.suggestion
        }
        logger.info(f"Review complete. Score: {review.score}")
        return review_dict


class AutoKaggleSummarizerOperator(Operator):
    """Summarizes a successful phase into a report."""

    async def __call__(self, state: AutoKaggleState, phase_memory: PhaseMemory) -> str:
        logger.info(f"Summarizer creating report for phase: '{phase_memory.phase_goal}'")
        prompt = get_summarizer_prompt(state, phase_memory)
        report = await self.llm_service.call(prompt)
        logger.info("Report created.")
        return report


# Backward compatibility aliases
PhasePlanningOperator = AutoKagglePlannerOperator
StepPlanningOperator = AutoKagglePlannerOperator
DeveloperOperator = AutoKaggleDeveloperOperator
ValidatorOperator = DynamicValidationOperator
