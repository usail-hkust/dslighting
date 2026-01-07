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
    def __init__(self, name: str, file_path: Optional[str], log_path: str, data_dir: Optional[str] = None, competitions: Optional[List[str]] = None):
        # Set up data_dir and registry before calling parent constructor
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_MLE_REGISTRY.get_data_dir()
        self.registry: Registry = DEFAULT_MLE_REGISTRY.set_data_dir(self.data_dir)
        
        # Load configuration
        self.config = self._load_config()
        if competitions:
            self.config["competitions"] = list(competitions)  # 使用命令行参数覆盖实验数据集配置
        
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
        # Get competition list from configuration
        competition_ids = self.config.get("competitions", [])
        
        if not competition_ids:
            logger.warning("No competitions configured in config.yaml")
            return problems
        
        # Iterate over competitions from configuration
        for competition_id in competition_ids:
            try:
                competition = self.registry.get_competition(competition_id)
                if is_dataset_prepared(competition, grading_only=False):
                    problems.append({"competition_id": competition_id})
                    logger.debug(f"Found prepared competition: {competition_id}")
                else:
                    logger.warning(
                        f"Skipping competition '{competition_id}' as its dataset is not fully prepared."
                    )
            except Exception as e:
                logger.warning(f"Error loading competition '{competition_id}': {e}")
        
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
        competition_id = self.problems[0]["competition_id"]
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
            # The check is already done in _load_problems, but this is a safe guard
            if not is_dataset_prepared(competition, grading_only=False):
                raise ValueError(f"Dataset for '{competition_id}' not prepared in '{self.data_dir}'.")

            # 1. Create standardized TaskDefinition
            task = TaskDefinition(
                task_id=competition_id,
                task_type="kaggle", # Explicit task type
                payload={
                    "description": competition.description,
                    "public_data_dir": str(competition.public_dir.absolute()),
                    "output_submission_path": str(output_submission_path.absolute())
                }
            )

            # 2. Call the generic evaluation function
            result, cost, usage_summary = await eval_fn(task)

            # 3. Extract token information from usage_summary
            input_tokens = usage_summary.get("prompt_tokens", 0)
            output_tokens = usage_summary.get("completion_tokens", 0)
            total_tokens = usage_summary.get("total_tokens", 0)

            # 3. Process result and perform grading
            if isinstance(result, Path):
                logger.debug(f"Grading submission {result} for {competition_id}")
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
