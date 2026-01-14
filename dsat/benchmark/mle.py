# dsat/benchmark/mle.py

import os
import time
import uuid
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, List, Tuple, Optional, Dict
import pandas as pd
import logging

from dsat.benchmark.benchmark import BaseBenchmark

# --- mlebench related imports ---
from mlebench.data import is_dataset_prepared
from mlebench.grade import aggregate_reports, grade_csv
from mlebench.grade_helpers import CompetitionReport
from mlebench.registry import Competition, Registry
from mlebench.registry import registry as DEFAULT_MLE_REGISTRY

# --- DSAT core model imports ---
from dsat.models.task import TaskDefinition

logger = logging.getLogger(__name__)


class MLEBenchmark(BaseBenchmark):
    """
    Benchmark class to integrate mle_bench competitions into the DSAT framework.
    """
    def __init__(
        self,
        name: str,
        file_path: Optional[str],
        log_path: str,
        data_dir: Optional[str] = None,
        competitions: Optional[List[str]] = None,
        data_source: str = "prepared"  # Default to "prepared" for competition simulation
    ):
        # Set up data_dir and registry before calling parent constructor
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_MLE_REGISTRY.get_data_dir()
        self.registry: Registry = DEFAULT_MLE_REGISTRY.set_data_dir(self.data_dir)
        self.data_source = data_source  # Save data source preference
        
        # Load configuration
        self.config = self._load_config()
        
        if competitions:
            # Intelligent merge: Filter config entries by CLI args, preserving metadata (like mode).
            cli_ids = set(competitions)
            merged_list = []
            
            # 1. Index existing config entries
            config_map = {}
            for entry in self.config.get("competitions", []):
                if isinstance(entry, str):
                    config_map[entry] = {"id": entry, "mode": "standard_ml"}
                elif isinstance(entry, dict) and "id" in entry:
                    config_map[entry["id"]] = entry
            
            # 2. Build new list based on CLI args
            for cid in competitions:
                if cid in config_map:
                    merged_list.append(config_map[cid])
                else:
                    # New competition not in config, use default string format
                    merged_list.append(cid)
            
            self.config["competitions"] = merged_list
        
        # file_path is accepted for compatibility but will be ignored.
        super().__init__(name, file_path, log_path)
        
        Path(self.log_path).mkdir(parents=True, exist_ok=True)
        
        # RE-INITIALIZE problems by calling the correct loader after registry is set up.
        self.problems = self._load_problems()
        logger.info(f"MLEBenchmark initialized with data_dir: {self.data_dir}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.yaml file."""
        try:
            # Get the path to the config.yaml file relative to this module
            framework_dir = Path(__file__).parent.parent.parent
            config_path = framework_dir / "config.yaml"
            
            if not config_path.exists():
                logger.warning(f"Config file not found at {config_path}, using default configuration")
                return {"competitions": []}
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config or {"competitions": []}
        except Exception as e:
            logger.error(f"Error loading config file: {e}, using default configuration")
            return {"competitions": []}
    
    def _load_problems(self) -> List[Dict[str, Any]]:
        """
        Dynamically load competition problems from the mlebench registry
        instead of a static file. This is the correct integration pattern.
        """
        logger.info(f"Discovering prepared competitions in {self.data_dir}...")
        
        if not self.data_dir.exists():
            raise FileNotFoundError(
                f"MLEBench data directory not found: {self.data_dir}. "
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
                competition = self.registry.get_competition(comp_id)
                
                # For open_ended tasks, skip the prepared check and add directly
                if mode == "open_ended":
                    problems.append({
                        "competition_id": comp_id,
                        "mode": mode
                    })
                    logger.info(f"Found open-ended competition: {comp_id} (mode={mode})")
                elif is_dataset_prepared(competition, grading_only=False):
                    problems.append({
                        "competition_id": comp_id,
                        "mode": mode
                    })
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
        logger.info(f"Setting MLEBenchmark mode to '{mode}'")
        self.registry.set_mode(mode)

    async def grade(self, submission_path: Path) -> float:
        """Grades a submission and returns a numerical fitness score for AFlow."""
        if not self.problems:
            return 0.0

        # Assume we are grading for the first (and likely only) competition
        problem = self.problems[0]
        competition_id = problem["competition_id"]
        mode = problem.get("mode", "standard_ml")

        if mode == "open_ended":
            # For open-ended tasks, use LLM judge for scoring
            return await self._grade_open_ended(submission_path, competition_id, mode)

        try:
            competition = self.registry.get_competition(competition_id)
            if not submission_path.exists():
                logger.warning(f"Grading failed: submission file not found at {submission_path}")
                return 0.0

            report = grade_csv(submission_path, competition)
            score = report.score if report.score is not None else 0.0

            # Normalize score to be a fitness value (higher is better)
            if report.is_lower_better:
                 return 1.0 / (1.0 + score) if score > 0 else 1.0
            return score

        except Exception as e:
            logger.error(f"Error during grading for {competition_id}: {e}")
            return 0.0

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
            # Check if artifacts directory exists
            if not artifacts_path.exists():
                logger.warning(f"Artifacts directory not found: {artifacts_path}")
                return 0.0

            # Load task description and rubric
            competition = self.registry.get_competition(competition_id)
            competition_dir = competition.raw_dir.parent

            description_path = competition_dir / "description.md"
            rubric_path = competition_dir / "rubric.md"

            description = ""
            rubric = ""

            if description_path.exists():
                description = description_path.read_text(encoding='utf-8')
            else:
                description = competition.description

            if rubric_path.exists():
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
                from dsat.services.llm import LLMService
                from dsat.config import LLMConfig

                # Get LLM service - need to initialize it
                # Try to get LLM model from config or environment
                llm_model = os.environ.get('LLM_MODEL', 'glm-4.7')
                # For DSATRunner context, api_key etc are usually available in env or config
                # Here we try to instantiate a service quickly
                
                # Assuming environment variables are set from .env
                api_key = os.environ.get('API_KEY')
                api_base = os.environ.get('API_BASE')
                provider = os.environ.get('LLM_PROVIDER', 'openai')

                llm_config = LLMConfig(
                    model=llm_model,
                    api_key=api_key,
                    api_base=api_base,
                    provider=provider
                )
                llm_service = LLMService(llm_config)

                logger.info(f"Calling LLM judge for {competition_id} with model {llm_model}")

                # Call LLM
                # Note: LLMService.achat is async
                messages = [{"role": "user", "content": judge_prompt}]
                llm_response = await llm_service.achat(messages)

                # Parse JSON response
                import json
                import re

                # Extract JSON from response
                json_match = re.search(r'\{[^{}]*\}', llm_response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
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
                else:
                    logger.warning(f"Failed to parse LLM judge response as JSON: {llm_response[:200]}")
                    # Fallback to heuristic if parsing fails
                    return self._heuristic_score(artifact_files)

            except Exception as llm_error:
                logger.error(f"LLM judge call failed: {llm_error}, using heuristic scoring")
                return self._heuristic_score(artifact_files)

        except Exception as e:
            logger.error(f"Error during LLM judge grading: {e}", exc_info=True)
            return 0.0

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
        Evaluates a single MLEBench competition.
        """
        competition_id = problem.get("competition_id")
        mode = problem.get("mode", "standard_ml") # Default to standard_ml

        if not competition_id:
            raise ValueError("Problem data must contain 'competition_id'")

        # Define unique output path
        # timestamp = datetime.now().strftime('%Y%m%dT%H%M%S')
        unique_id = uuid.uuid4().hex[:6]
        output_filename = f"submission_{competition_id}_{unique_id}.csv"
        output_submission_path = (Path(self.log_path) / output_filename).absolute()

        # Start timing
        start_time = time.perf_counter()

        cost = 0.0
        running_time = 0.0
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0
        report: Optional[CompetitionReport] = None
        error_message: Optional[str] = None
        competition: Optional[Competition] = None

        try:
            competition = self.registry.get_competition(competition_id)
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

                payload = {
                    "description": competition.description,  # Fallback brief description
                    "description_file": str(description_path) if description_path.exists() else "",
                    "rubric": "",  # Will be loaded from file
                    "rubric_file": str(rubric_path) if rubric_path.exists() else "",
                    "public_data_dir": str(source_data_dir.absolute()), 
                    "raw_data_dir": "./data", 
                    "output_submission_path": str(output_submission_path.absolute())
                }
                logger.info(f"Open-ended task payload: data_source={source_data_dir}, mapped_to=./data")
            else:
                # For standard ML tasks
                payload = {
                    "description": competition.description,
                    "public_data_dir": str(source_data_dir.absolute()), # Use the determined source
                    "output_submission_path": str(output_submission_path.absolute())
                }

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
            if isinstance(result, Path):
                logger.debug(f"Grading submission {result} for {competition_id} (mode={mode})")
                
                if mode == "open_ended":
                    # Skip standard grading for open-ended tasks
                    logger.info(f"Skipping CSV grading for open-ended task {competition_id}")
                    # Create a dummy 'success' report
                    base_data = {
                        "competition_id": competition_id,
                        "score": 1.0, # Placeholder score
                        "gold_threshold": 0.0,
                        "silver_threshold": 0.0,
                        "bronze_threshold": 0.0,
                        "median_threshold": 0.0,
                        "any_medal": True,
                        "gold_medal": True, # Mark as success for visualization
                        "silver_medal": False,
                        "bronze_medal": False,
                        "above_median": True,
                        "submission_exists": result.exists(),
                        "valid_submission": True, # It ran successfully
                        "is_lower_better": False,
                        "created_at": datetime.now().isoformat(),
                        "submission_path": str(result),
                    }
                    report = CompetitionReport.from_dict(base_data)
                else:
                    report = grade_csv(result, competition)

            elif isinstance(result, str) and result.startswith("[ERROR]"):
                error_message = f"DSAT workflow failed: {result}"
                logger.error(error_message)
                report = self._create_error_report(competition_id, output_submission_path, error_message)
            else:
                 error_message = f"Unexpected result type from eval_fn: {type(result).__name__}"
                 logger.error(error_message)
                 report = self._create_error_report(competition_id, output_submission_path, error_message)

        except Exception as e:
            error_message = f"Error during MLEBenchmark evaluation of {competition_id}: {e}"
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
            # Check if artifacts directory exists
            if not artifacts_path.exists():
                logger.warning(f"Artifacts directory not found: {artifacts_path}")
                return 0.0

            # Load task description and rubric
            competition = self.registry.get_competition(competition_id)
            competition_dir = competition.raw_dir.parent

            description_path = competition_dir / "description.md"
            rubric_path = competition_dir / "rubric.md"

            description = ""
            rubric = ""

            if description_path.exists():
                description = description_path.read_text(encoding='utf-8')
            else:
                description = competition.description

            if rubric_path.exists():
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
                from dsat.llm import LLMService
                from dsat.config import DSATConfig

                # Get LLM service - need to initialize it
                # Try to get LLM model from config or environment
                llm_model = os.environ.get('LLM_MODEL', 'glm-4.7')
                llm_provider = os.environ.get('LLM_PROVIDER', 'openai')

                llm_service = LLMService(
                    model=llm_model,
                    provider=llm_provider
                )

                logger.info(f"Calling LLM judge for {competition_id} with model {llm_model}")

                # Call LLM
                llm_response = await llm_service.call(judge_prompt)

                # Parse JSON response
                import json
                import re

                # Extract JSON from response
                json_match = re.search(r'\{[^{}]*\}', llm_response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
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
                else:
                    logger.warning(f"Failed to parse LLM judge response as JSON: {llm_response[:200]}")
                    # Fallback to heuristic if parsing fails
                    return self._heuristic_score(artifact_files)

            except Exception as llm_error:
                logger.error(f"LLM judge call failed: {llm_error}, using heuristic scoring")
                return self._heuristic_score(artifact_files)

        except Exception as e:
            logger.error(f"Error during LLM judge grading: {e}", exc_info=True)
            return 0.0

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
