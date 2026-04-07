# dslighting/benchmark/benchmarks/mle_style_benchmark.py

import logging
import os
import time
import uuid
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from dslighting.benchmark.core.base import BaseBenchmark
from dslighting.benchmark.core.config_loader import (
    BaseBenchmarkConfigLoader,
    create_problem_entry,
)
from dslighting.benchmark.evaluation.service import TaskEvaluationService
from dslighting.benchmark.evaluation.contract_builder import build_task_evaluation_contract
from dslighting.benchmark.evaluation.models import EvaluationOutcome
from dslighting.benchmark.reporting import CompetitionReport, CompetitionReportBuilder

# --- mlebench related imports ---
from dslighting.benchmark.vendor.mlebench.data import is_dataset_prepared
from dslighting.benchmark.vendor.mlebench.registry import Registry
from dslighting.benchmark.vendor.mlebench.registry import registry as DEFAULT_MLE_REGISTRY
from dslighting.benchmark.vendor.dabench.registry import Registry as DABenchRegistry
from dslighting.benchmark.vendor.dabench.registry import registry as DEFAULT_DABENCH_REGISTRY

# --- DSLighting core model imports ---
from dslighting.core.tasks.output_artifact import resolve_output_artifact_path_for_competition
from dslighting.core.types.task import TaskDefinition

logger = logging.getLogger(__name__)


class MLEStyleBenchmark(BaseBenchmark):
    """
    Shared benchmark engine for competition-style registry sources.

    This engine is used by multiple benchmark sources that share the
    ``mle_task_contract/v1`` task layout and ``engine_id = "mle"`` runtime:
    DACode, DABench, and MLEBench.
    """
    def __init__(
        self,
        name: str,
        file_path: Optional[str],
        log_path: str,
        data_dir: Optional[str] = None,
        competitions: Optional[List[str]] = None,
        data_source: str = "prepared",  # Default to "prepared" for competition simulation
        runner: Optional[Any] = None,
        eval_fn: Optional[Callable] = None,
        registry: Optional[Any] = None,
    ):
        # Set up data_dir and registry before calling parent constructor
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_MLE_REGISTRY.get_data_dir()
        self.registry: Registry = (
            registry.set_data_dir(self.data_dir) if registry is not None else DEFAULT_MLE_REGISTRY.set_data_dir(self.data_dir)
        )
        self._competition_registries: Dict[str, Any] = {}
        self._legacy_dabench_registry: Optional[DABenchRegistry] = None
        if registry is None:
            self._legacy_dabench_registry = DEFAULT_DABENCH_REGISTRY.set_data_dir(self.data_dir)
        self.data_source = data_source  # Save data source preference

        # Load configuration using shared config loader
        self.config_loader = BaseBenchmarkConfigLoader(config_key="competitions")
        self.config = self.config_loader.load_config()

        # Merge CLI competitions with config if provided
        if competitions:
            merged = self.config_loader.merge_competitions(
                self.config.get("competitions", []),
                competitions
            )
            self.config["competitions"] = merged
        
        self.runner = runner
        resolved_eval_fn = eval_fn
        if resolved_eval_fn is None and runner is not None and hasattr(runner, "get_eval_function"):
            resolved_eval_fn = runner.get_eval_function()
        if runner is not None and hasattr(runner, "benchmark"):
            runner.benchmark = self

        # file_path is accepted for compatibility but will be ignored.
        super().__init__(name, file_path, log_path, eval_fn=resolved_eval_fn)
        
        Path(self.log_path).mkdir(parents=True, exist_ok=True)
        
        for entry in self.config.get("competitions", []):
            comp_id = entry if isinstance(entry, str) else entry.get("id")
            if isinstance(comp_id, str) and comp_id:
                self._competition_registries[comp_id] = self.registry

        # RE-INITIALIZE problems by calling the correct loader after registry is set up.
        self.problems = self._load_problems()
        self._evaluation_service = TaskEvaluationService()
        self._report_builder = CompetitionReportBuilder()
        logger.info(f"MLEStyleBenchmark initialized with data_dir: {self.data_dir}")

    # _load_config() removed - now uses self.config_loader.load_config() directly

    def _load_problems(self) -> List[Dict[str, Any]]:
        """
        Dynamically load competition problems from the mlebench registry
        instead of a static file. This is the correct integration pattern.
        """
        logger.info(f"Discovering prepared competitions in {self.data_dir}...")
        
        if not self.data_dir.exists():
            raise FileNotFoundError(
                f"Benchmark data directory not found: {self.data_dir}. "
                "Please provide a valid path via --mle-data-dir."
            )

        problems = []
        # The competition IDs are loaded from configuration (already merged with arguments in __init__)
        competition_entries = self.config.get("competitions", [])
        
        if not competition_entries:
            logger.warning("No competitions configured in config.yaml")
            return problems
        
        # Iterate over competitions from configuration
        for entry in competition_entries:
            # Handle both string (legacy) and dict (new) config formats
            if isinstance(entry, str):
                comp_id = entry
                mode = "standard_ml"
            elif isinstance(entry, dict):
                comp_id = entry.get("id")
                mode = entry.get("mode", "standard_ml")
            else:
                logger.warning(f"Invalid competition entry type: {type(entry)}")
                continue

            if not comp_id:
                continue

            try:
                registry = self._get_registry_for_competition(comp_id)
                competition = registry.get_competition(comp_id)
                
                # For open_ended tasks, skip the prepared check and add directly
                if mode == "open_ended":
                    problem_entry = {
                        "competition_id": comp_id,
                        "mode": mode
                    }
                    if isinstance(entry, dict) and isinstance(entry.get("resources"), dict):
                        problem_entry["resources"] = entry.get("resources")
                    problems.append(problem_entry)
                    logger.info(f"Found open-ended competition: {comp_id} (mode={mode})")
                elif is_dataset_prepared(competition, grading_only=False):
                    problem_entry = {
                        "competition_id": comp_id,
                        "mode": mode
                    }
                    if isinstance(entry, dict) and isinstance(entry.get("resources"), dict):
                        problem_entry["resources"] = entry.get("resources")
                    problems.append(problem_entry)
                    logger.debug(f"Found prepared competition: {comp_id} (mode={mode})")
                else:
                    # Standard ML tasks must be prepared
                    logger.warning(
                        f"Skipping standard ML competition '{comp_id}' as its dataset is not fully prepared."
                    )
            except Exception as e:
                logger.warning(f"Error loading competition '{comp_id}': {e}")
        
        if not problems:
            logger.error(
                f"No prepared competitions found in {self.data_dir}. "
                "Please run `mlebench prep <competition_id>` or `mlebench prep --all`."
            )

        return problems

    def set_mode(self, mode: str):
        """Sets the benchmark mode to 'validation' or 'test'."""
        logger.info(f"Setting MLEStyleBenchmark mode to '{mode}'")
        self.registry.set_mode(mode)
        if self._legacy_dabench_registry is not None:
            self._legacy_dabench_registry.set_mode(mode)

    @staticmethod
    def _is_dabench_competition(competition_id: str) -> bool:
        return competition_id.startswith("dabench-")

    def _get_registry_for_competition(self, competition_id: str):
        registry = self._competition_registries.get(competition_id)
        if registry is not None:
            return registry
        if self._legacy_dabench_registry is not None and self._is_dabench_competition(competition_id):
            return self._legacy_dabench_registry
        return self.registry

    def _get_problem_by_competition_id(self, competition_id: str) -> Optional[Dict[str, Any]]:
        """Return problem entry for the given competition id if available."""
        for problem in self.problems:
            if isinstance(problem, dict) and problem.get("competition_id") == competition_id:
                return problem
        return None

    def _infer_competition_id_from_submission_path(self, submission_path: Path) -> Optional[str]:
        """
        Infer competition id from submission filename.

        Expected filename pattern is usually:
          submission_<competition_id>_<unique>.csv
        but we keep this resilient by matching against known loaded competition ids.
        """
        stem = submission_path.stem
        if stem.startswith("submission_"):
            stem = stem[len("submission_") :]

        candidates: List[str] = []
        for problem in self.problems:
            if isinstance(problem, dict):
                comp_id = problem.get("competition_id")
                if isinstance(comp_id, str) and comp_id:
                    candidates.append(comp_id)

        # Prefer longer ids first in case one id is a prefix of another.
        for comp_id in sorted(set(candidates), key=len, reverse=True):
            if stem == comp_id or stem.startswith(f"{comp_id}_"):
                return comp_id
        return None

    async def grade(self, submission_path: Path, competition_id: Optional[str] = None) -> float:
        """Grade a submission for the correct competition and return a numeric score."""
        if not self.problems:
            return 0.0

        submission_path = Path(submission_path)
        resolved_competition_id = competition_id or self._infer_competition_id_from_submission_path(submission_path)

        problem = None
        if resolved_competition_id:
            problem = self._get_problem_by_competition_id(resolved_competition_id)

        if problem is None:
            logger.warning(
                "grade(): unable to resolve competition id; refusing ambiguous fallback. "
                "submission=%s requested=%s inferred_from_path=%s",
                submission_path,
                competition_id,
                self._infer_competition_id_from_submission_path(submission_path),
            )
            return 0.0

        if not resolved_competition_id or not isinstance(problem, dict):
            logger.warning("grade(): unable to resolve competition id for submission %s", submission_path)
            return 0.0

        mode = problem.get("mode", "standard_ml")

        try:
            competition = self._get_registry_for_competition(resolved_competition_id).get_competition(
                resolved_competition_id
            )
            if not submission_path.exists():
                logger.warning(f"Grading failed: submission file not found at {submission_path}")
                return 0.0

            contract = self._build_evaluation_contract(
                competition=competition,
                competition_id=resolved_competition_id,
                mode=mode,
                output_submission_path=submission_path,
            )
            outcome = await self._evaluation_service.evaluate(
                submission_path=submission_path,
                contract=contract,
                mode="validation" if mode == "validation" else "test",
                metadata={"benchmark_name": self.name},
            )
            report = self._report_builder.build(
                outcome=outcome,
                semantics=contract.evaluation_semantics,
                competition_id=resolved_competition_id,
                submission_path=submission_path,
            )
            score = report.score if report.score is not None else 0.0

            # Normalize score to be a fitness value (higher is better)
            if report.is_lower_better:
                if score < 0:
                    return 1.0 / (1.0 + abs(score))
                return 1.0 / (1.0 + score)
            return max(0.0, min(score, 1.0))

        except Exception as e:
            logger.error(f"Error during grading for {resolved_competition_id}: {e}")
            return 0.0

    def _build_evaluation_contract(
        self,
        *,
        competition: Any,
        competition_id: str,
        mode: str,
        output_submission_path: Path,
    ):
        registry = self._get_registry_for_competition(competition_id)
        source_id = getattr(getattr(registry, "descriptor", None), "source_id", "mlebench")
        contract, _ = build_task_evaluation_contract(
            competition=competition,
            source_id=source_id,
            engine_id="mle",
            registry_root=registry.get_competitions_dir() if hasattr(registry, "get_competitions_dir") else None,
            data_root=registry.get_data_dir() if hasattr(registry, "get_data_dir") else self.data_dir,
            mode="validation" if mode == "validation" else "test",
            output_submission_path=output_submission_path,
            evaluation_mode="judge_based" if mode == "open_ended" else "artifact_submission",
        )
        if mode == "open_ended" and contract.judging is not None:
            contract = replace(
                contract,
                judging=replace(contract.judging, judge_fn=self._evaluate_open_ended_contract),
            )
        return contract

    def _resolve_llm_judge_model(self) -> str:
        """
        Resolve the model used by open-ended LLM judge.

        Priority:
        1. Explicit `LLM_MODEL` env var (if non-empty)
        2. First model key in `LLM_MODEL_CONFIGS` (if available)
        3. Legacy default `glm-4.7`
        """
        model_name = (os.environ.get("LLM_MODEL") or "").strip()
        if model_name:
            return model_name

        raw_model_configs = os.environ.get("LLM_MODEL_CONFIGS")
        if raw_model_configs:
            try:
                import json
                parsed = json.loads(raw_model_configs)
                if isinstance(parsed, dict):
                    for candidate in parsed.keys():
                        if isinstance(candidate, str) and candidate.strip():
                            chosen = candidate.strip()
                            logger.info(
                                "LLM_MODEL is empty; using first model from LLM_MODEL_CONFIGS for judge: %s",
                                chosen,
                            )
                            return chosen
            except Exception as exc:
                logger.warning("Failed to parse LLM_MODEL_CONFIGS for judge model resolution: %s", exc)

        return "glm-4.7"

    def _build_llm_judge_service(self):
        """
        Build LLMService for open-ended judge with support for:
        - API_KEY/API_BASE/LLM_MODEL
        - model-level overrides from LLM_MODEL_CONFIGS
        - OPENAI_API_KEY fallback for backward compatibility
        """
        from dslighting.core.config.builder import ConfigBuilder
        from dslighting.services.llm import LLMService

        judge_model = self._resolve_llm_judge_model()
        llm_config = ConfigBuilder().build_config(model=judge_model).llm

        # Compatibility: keep supporting OPENAI_API_KEY-only setups.
        if not llm_config.get_api_keys():
            openai_api_key = os.environ.get("OPENAI_API_KEY")
            if openai_api_key:
                llm_config.api_key = openai_api_key

        return LLMService(llm_config), llm_config.model

    async def _grade_open_ended(self, artifacts_path: Path, competition_id: str, mode: str) -> float:
        """
        Grade open-ended tasks using LLM judge.

        Args:
            artifacts_path: Path to the artifacts directory
            competition_id: Competition identifier
            mode: Task mode (should be "open_ended")

        Returns:
            Float score between 0.0 and 1.0
        """
        try:
            # Validate artifacts_path is a directory
            if not artifacts_path.is_dir():
                logger.warning(f"Artifacts path is not a directory: {artifacts_path}")
                return 0.0

            # Load task description and rubric
            competition = self._get_registry_for_competition(competition_id).get_competition(competition_id)
            competition_dir = competition.raw_dir.parent

            description_path = competition_dir / "description.md"
            rubric_path = competition_dir / "rubric.md"

            description = ""
            rubric = ""

            if description_path.exists():
                description = description_path.read_text(encoding='utf-8')
            else:
                description = competition.description

            # Validate rubric.md exists
            if not rubric_path.exists():
                logger.warning(f"Rubric file not found: {rubric_path}, using default criteria")
                rubric = "Evaluate based on completeness, correctness, and quality of the solution."
            else:
                rubric = rubric_path.read_text(encoding='utf-8')

            # Analyze artifacts directory contents
            artifact_files = list(artifacts_path.iterdir()) if artifacts_path.is_dir() else []

            # Build file listing
            file_summary = []
            for file in sorted(artifact_files):
                if file.is_file():
                    # Read file content based on type
                    try:
                        if file.suffix in ['.py', '.md', '.txt', '.csv']:
                            content = file.read_text(encoding='utf-8', errors='ignore')
                            # Truncate large files
                            if len(content) > 2000:
                                content = content[:2000] + "\n... (truncated)"
                            file_summary.append(f"### {file.name}\n```\n{content}\n```")
                        elif file.suffix in ['.png', '.jpg', '.jpeg']:
                            file_summary.append(f"### {file.name}\n[Image file - {file.stat().st_size} bytes]")
                        else:
                            file_summary.append(f"### {file.name}\n[Binary file - {file.stat().st_size} bytes]")
                    except Exception as e:
                        file_summary.append(f"### {file.name}\n[Error reading file: {e}]")

            # If no files found, return minimal score
            if not file_summary:
                logger.warning(f"No artifacts found in {artifacts_path}")
                return 0.1  # Small score for at least creating the directory

            # Construct LLM judge prompt
            # Define separator outside f-string (backslashes not allowed in f-string expressions)
            file_sep = "\n\n"
            judge_prompt = f"""You are an expert judge for open-ended data science tasks. Your role is to evaluate submissions based on given criteria.

## Task Description

{description}

## Evaluation Criteria

{rubric if rubric else "Evaluate based on completeness, correctness, and quality of the solution."}

## Submitted Artifacts

The following files were submitted:

{file_sep.join(file_summary)}

## Scoring Instructions

Evaluate the submission on a scale from 0.0 to 1.0 based on:

1. **Completeness** (0-0.3): Did the submission address all aspects of the task?
2. **Correctness** (0-0.4): Are the methods and results correct?
3. **Quality** (0-0.3): Is the code well-structured, documented, and the analysis thorough?

Provide your response in the following JSON format:

```json
{{
  "reasoning": "Brief explanation of the score",
  "completeness": 0.0-0.3,
  "correctness": 0.0-0.4,
  "quality": 0.0-0.3,
  "total_score": 0.0-1.0
}}
```

Respond ONLY with the JSON object, no additional text.
"""

            # Call LLM for judgment
            try:
                llm_service, llm_model = self._build_llm_judge_service()

                logger.info(f"Calling LLM judge for {competition_id} with model {llm_model}")

                # Call LLM
                llm_response = await llm_service.call(judge_prompt)

                # Parse JSON response with improved handling for nested objects
                import json
                import re

                # Try direct parse first (fastest path)
                try:
                    result = json.loads(llm_response.strip())
                except json.JSONDecodeError:
                    # Extract JSON from response - handle markdown code blocks and nested structures
                    json_text = llm_response.strip()

                    # Try to extract JSON from markdown code blocks
                    if "```json" in json_text:
                        # Extract content between ```json and closing ```
                        start = json_text.find("```json") + 7
                        end = json_text.find("```", start)
                        if end != -1:
                            json_text = json_text[start:end].strip()
                    elif "```" in json_text:
                        # Extract content between first ``` and closing ```
                        start = json_text.find("```") + 3
                        end = json_text.find("```", start)
                        if end != -1:
                            json_text = json_text[start:end].strip()

                    # Find the first { and last } to extract complete JSON object (handles nested structures)
                    first_brace = json_text.find('{')
                    last_brace = json_text.rfind('}')

                    if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
                        json_text = json_text[first_brace:last_brace + 1]
                        result = json.loads(json_text)
                    else:
                        raise ValueError("Could not extract valid JSON from LLM response")

                score = float(result.get('total_score', 0.5))

                # Log detailed breakdown
                completeness = result.get('completeness', 0.0)
                correctness = result.get('correctness', 0.0)
                quality = result.get('quality', 0.0)
                reasoning = result.get('reasoning', '')

                logger.info(f"LLM judge score for {competition_id}: {score:.2f}")
                logger.info(f"  Breakdown: completeness={completeness:.2f}, correctness={correctness:.2f}, quality={quality:.2f}")
                logger.info(f"  Reasoning: {reasoning[:200]}...")

                return max(0.0, min(score, 1.0))  # Ensure score is in [0, 1]

            except ValueError as json_error:
                logger.warning(f"Failed to parse LLM judge response as JSON: {json_error}")
                # Fallback to heuristic if parsing fails
                return self._heuristic_score(artifact_files)

            except Exception as llm_error:
                logger.error(f"LLM judge call failed: {llm_error}, using heuristic scoring")
                return self._heuristic_score(artifact_files)

        except Exception as e:
            logger.error(f"Error during LLM judge grading: {e}", exc_info=True)
            return 0.0

    async def _evaluate_open_ended_contract(
        self,
        *,
        submission_path: Path,
        contract: Any,
        mode: str,
        metadata: Dict[str, Any],
    ) -> EvaluationOutcome:
        if not submission_path.is_dir():
            return EvaluationOutcome(
                score=None,
                submission_exists=submission_path.exists(),
                valid_submission=False,
                error_kind="invalid_submission",
                error_message=f"Open-ended artifacts path is not a directory: {submission_path}",
                diagnostics={"metadata": dict(metadata or {})},
            )
        score = await self._grade_open_ended(submission_path, contract.task_id, mode)
        return EvaluationOutcome(
            score=score,
            submission_exists=submission_path.exists(),
            valid_submission=submission_path.exists(),
            error_kind="none" if submission_path.exists() else "invalid_submission",
            error_message=None if submission_path.exists() else "Artifacts directory missing.",
            diagnostics={"metadata": dict(metadata or {})},
        )

    def _heuristic_score(self, artifact_files) -> float:
        """Fallback heuristic scoring when LLM judge is unavailable."""
        has_code = any(f.suffix == '.py' for f in artifact_files if f.is_file())
        has_plots = any(f.suffix in ['.png', '.jpg', '.jpeg'] for f in artifact_files if f.is_file())
        has_report = any(f.suffix in ['.md', '.txt'] for f in artifact_files if f.is_file())

        # Simple heuristic: 0.6 base + 0.2 for code + 0.1 for plots + 0.1 for report
        score = 0.6
        if has_code:
            score += 0.2
        if has_plots:
            score += 0.1
        if has_report:
            score += 0.1

        score = min(score, 1.0)  # Cap at 1.0
        logger.info(f"Heuristic score: {score:.2f} (code={has_code}, plots={has_plots}, report={has_report})")
        return score


    def get_result_columns(self) -> List[str]:
        return [
            "competition_id", "submission_path", "answers_path", "score", "cost", "running_time",
            "input_tokens", "output_tokens", "total_tokens",
            "gold_medal", "silver_medal", "bronze_medal", "above_median",
            "submission_exists", "valid_submission", "error_message",
        ]

    def _create_error_report(self, competition_id: str, submission_path: Path, error_msg: str) -> CompetitionReport:
        """Creates a dummy report if grading or eval_fn execution fails."""
        # Create a minimal dict that CompetitionReport.from_dict can parse
        base_data = {
            "competition_id": competition_id,
            "score": None,
            "gold_threshold": float('nan'),
            "silver_threshold": float('nan'),
            "bronze_threshold": float('nan'),
            "median_threshold": float('nan'),
            "any_medal": False,
            "gold_medal": False,
            "silver_medal": False,
            "bronze_medal": False,
            "above_median": False,
            "submission_exists": submission_path.exists(),
            "valid_submission": False,
            "is_lower_better": False, # Default
            "created_at": datetime.now().isoformat(),
            "submission_path": str(submission_path),
        }
        # Use from_dict for safety
        report = CompetitionReport.from_dict(base_data)
        # Log the actual error separately
        logger.error(f"Error for {competition_id}: {error_msg}")
        return report

    async def evaluate_problem(self, problem: dict, eval_fn: Callable) -> Tuple[Tuple, CompetitionReport, Optional[str]]:
        """
        Evaluates a single competition-style benchmark task.
        """
        competition_id = problem.get("competition_id")
        mode = problem.get("mode", "standard_ml") # Default to standard_ml

        if not competition_id:
            raise ValueError("Problem data must contain 'competition_id'")

        unique_id = uuid.uuid4().hex[:6]

        # Start timing
        start_time = time.perf_counter()

        cost = 0.0
        running_time = 0.0
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0
        report: Optional[CompetitionReport] = None
        error_message: Optional[str] = None
        competition: Optional[Any] = None

        try:
            competition = self._get_registry_for_competition(competition_id).get_competition(competition_id)
            output_submission_path = (
                Path(self.log_path)
                / resolve_output_artifact_path_for_competition(
                    task_id=competition_id,
                    competition=competition,
                    unique_suffix=unique_id,
                )
            ).absolute()
            # Skip prepared check for open-ended tasks
            if mode != "open_ended" and not is_dataset_prepared(competition, grading_only=False):
                raise ValueError(f"Dataset for '{competition_id}' not prepared in '{self.data_dir}'.")

            # Determine source data directory (Host Path)
            # This path will be symlinked to './data' (or similar) in the workspace by the Runner/WorkspaceService.
            if self.data_source == "prepared":
                if competition.public_dir.exists():
                    source_data_dir = competition.public_dir
                    logger.info(f"Using prepared data source: {source_data_dir}")
                else:
                    # Strict enforcement: Do not fallback to raw if prepared was requested.
                    # This prevents accidental leakage of raw data (which might contain answers) in competition mode.
                    raise FileNotFoundError(
                        f"Prepared public data directory not found at {competition.public_dir}. "
                        f"Please run `mlebench prep {competition_id}` first, or check your data directory structure."
                    )
            else:
                # data_source == "raw"
                source_data_dir = competition.raw_dir
                logger.info(f"Using raw data source: {source_data_dir}")

            # 1. Create standardized TaskDefinition
            # Determine task_type based on mode
            task_type = "open_ended" if mode == "open_ended" else "kaggle"

            # Prepare payload based on task type
            if mode == "open_ended":
                # For open-ended tasks, provide file paths to description, rubric, and raw data
                competition_dir = competition.raw_dir.parent  # Go up from /raw to competition root

                description_path = competition_dir / "description.md"
                rubric_path = competition_dir / "rubric.md"

                # Validate rubric exists for open-ended tasks
                if not rubric_path.exists():
                    raise ValueError(
                        f"rubric.md not found in {competition_dir}. "
                        f"Open-ended tasks require a rubric.md file for LLM judge evaluation."
                    )

                payload = {
                    "description": competition.description,  # Fallback brief description
                    "description_file": str(description_path) if description_path.exists() else "",
                    "rubric": "",  # Will be loaded from file
                    "rubric_file": str(rubric_path),
                    "agent_visible_data_dir": str(source_data_dir.absolute()),
                    "public_data_dir": str(source_data_dir.absolute()),
                    "raw_data_dir": "./data",
                    "output_submission_path": str(output_submission_path.absolute())
                }
                logger.info(f"Open-ended task payload: data_source={source_data_dir}, mapped_to=./data")
            else:
                # For standard ML tasks
                sample_submission_path = getattr(competition, "sample_submission", None)
                sample_submission_name = sample_submission_path.name if isinstance(sample_submission_path, Path) else ""
                sample_submission_format = (
                    sample_submission_path.suffix.lower() if isinstance(sample_submission_path, Path) else ""
                )
                contract = self._build_evaluation_contract(
                    competition=competition,
                    competition_id=competition_id,
                    mode=mode,
                    output_submission_path=output_submission_path,
                )

                payload = {
                    "description": competition.description,
                    "agent_visible_data_dir": str(source_data_dir.absolute()),
                    "public_data_dir": str(source_data_dir.absolute()),  # Use the determined source
                    "output_submission_path": str(output_submission_path.absolute()),
                    "sample_submission_path": (
                        str(sample_submission_path.absolute()) if isinstance(sample_submission_path, Path) else ""
                    ),
                    "submission_filename": sample_submission_name,
                    "submission_format": sample_submission_format,
                }
                if contract.grading is not None:
                    payload.update(contract.grading.submission.to_payload())

            task = TaskDefinition(
                task_id=competition_id,
                task_type=task_type,
                mode=mode,
                payload=payload
            )

            # 2. Call the generic evaluation function
            result, cost, usage_summary = await eval_fn(task)

            # 3. Extract token information from usage_summary
            input_tokens = usage_summary.get("prompt_tokens", 0)
            output_tokens = usage_summary.get("completion_tokens", 0)
            total_tokens = usage_summary.get("total_tokens", 0)

            # 3. Process result and perform grading
            if isinstance(result, dict) and result.get("submission_path"):
                result = Path(str(result["submission_path"]))

            if isinstance(result, Path):
                logger.debug(f"Grading submission {result} for {competition_id} (mode={mode})")
                contract = self._build_evaluation_contract(
                    competition=competition,
                    competition_id=competition_id,
                    mode=mode,
                    output_submission_path=result,
                )
                outcome = await self._evaluation_service.evaluate(
                    submission_path=result,
                    contract=contract,
                    mode="validation" if mode == "validation" else "test",
                    metadata={"benchmark_name": self.name},
                )
                report = self._report_builder.build(
                    outcome=outcome,
                    semantics=contract.evaluation_semantics,
                    competition_id=competition_id,
                    submission_path=result,
                )
                if outcome.error_kind != "none":
                    error_message = outcome.error_message

            elif isinstance(result, str) and result.startswith("[ERROR]"):
                error_message = f"DSLighting workflow failed: {result}"
                logger.error(error_message)
                report = self._create_error_report(competition_id, output_submission_path, error_message)
            else:
                 error_message = f"Unexpected result type from eval_fn: {type(result).__name__}"
                 logger.error(error_message)
                 report = self._create_error_report(competition_id, output_submission_path, error_message)

        except Exception as e:
            error_message = f"Error during {self.__class__.__name__} evaluation of {competition_id}: {e}"
            logger.error(error_message, exc_info=True)
            report = self._create_error_report(competition_id, output_submission_path, error_message)

        if report is None:
            final_error = error_message or "Unknown error: report is None"
            report = self._create_error_report(competition_id, output_submission_path, final_error)
            error_message = final_error

        if not report.valid_submission:
            answers_path_str = str(getattr(competition, 'answers', 'N/A')) if competition else 'N/A'
            self.log_mismatch(
                problem=competition_id,
                expected_output=answers_path_str,
                prediction=f"File: {output_submission_path}, Exists: {report.submission_exists}, Valid: {report.valid_submission}",
                extracted_output=report.score,
                extract_answer_code=error_message or "Grading function failed or file invalid/missing"
            )
            if not error_message:
                error_message = "Submission invalid or missing."

        # Calculate running time
        running_time = round(time.perf_counter() - start_time, 4)

        answers_path_str = str(getattr(competition, 'answers', 'N/A')) if competition else 'N/A'
        csv_tuple = (
            report.competition_id, str(report.submission_path), answers_path_str,
            report.score, cost, running_time,
            input_tokens, output_tokens, total_tokens,
            report.gold_medal, report.silver_medal, report.bronze_medal,
            report.above_median, report.submission_exists, report.valid_submission, error_message,
         )
        return csv_tuple, report, error_message
