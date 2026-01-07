# dsat/benchmark/sciencebench.py

import logging
import time
import uuid
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from dsat.benchmark.benchmark import BaseBenchmark
from dsat.models.task import TaskDefinition

from sciencebench.data import is_dataset_prepared
from sciencebench.grade import grade_submission
from sciencebench.grade_helpers import CompetitionReport
from sciencebench.registry import Competition, Registry
from sciencebench.registry import registry as DEFAULT_SCIENCEBENCH_REGISTRY

logger = logging.getLogger(__name__)


class ScienceBenchBenchmark(BaseBenchmark):
    """
    Benchmark class to integrate ScienceBench competitions into the DSAT framework.

    Expected `data_dir` layout (same as MLEBench):
      <data_dir>/<competition_id>/prepared/public/...
      <data_dir>/<competition_id>/prepared/private/...
    """

    def __init__(
        self,
        name: str,
        file_path: Optional[str],
        log_path: str,
        data_dir: Optional[str] = None,
        competitions: Optional[List[str]] = None,
    ):
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_SCIENCEBENCH_REGISTRY.get_data_dir()
        self.registry: Registry = DEFAULT_SCIENCEBENCH_REGISTRY.set_data_dir(self.data_dir)

        self.config = self._load_config()
        if competitions:
            self.config["competitions"] = list(competitions)

        super().__init__(name, file_path, log_path)
        Path(self.log_path).mkdir(parents=True, exist_ok=True)

        self.problems = self._load_problems()
        logger.info("ScienceBenchBenchmark initialized with data_dir: %s", self.data_dir)

    def _load_config(self) -> Dict[str, Any]:
        try:
            framework_dir = Path(__file__).parent.parent.parent
            config_path = framework_dir / "config.yaml"
            if not config_path.exists():
                logger.warning("Config file not found at %s, using default configuration", config_path)
                return {"competitions": []}

            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}

            competitions = config.get("sciencebench_competitions", [])
            if competitions:
                return {"competitions": list(competitions)}
            return {"competitions": []}
        except Exception as exc:
            logger.error("Error loading config file for ScienceBench: %s", exc)
            return {"competitions": []}

    def _load_problems(self) -> List[Dict[str, Any]]:
        logger.info("Discovering prepared ScienceBench competitions in %s...", self.data_dir)

        if not self.data_dir.exists():
            raise FileNotFoundError(
                f"ScienceBench data directory not found: {self.data_dir}. "
                "Please provide a valid path via --data-dir."
            )

        competition_ids = self.config.get("competitions", [])
        if not competition_ids:
            logger.warning("No sciencebench competitions provided; pass --task-id <competition_id>.")
            return []

        problems: List[Dict[str, Any]] = []
        for competition_id in competition_ids:
            try:
                competition = self.registry.get_competition(competition_id)
                if is_dataset_prepared(competition, grading_only=False):
                    problems.append({"competition_id": competition_id})
                else:
                    logger.warning(
                        "Skipping competition '%s' as its dataset is not fully prepared under '%s'.",
                        competition_id,
                        self.data_dir,
                    )
            except Exception as exc:
                logger.warning("Error loading competition '%s': %s", competition_id, exc)

        if not problems:
            logger.error(
                "No prepared ScienceBench competitions found in %s. "
                "Please prepare the dataset or point --data-dir to a prepared competitions folder.",
                self.data_dir,
            )
        return problems

    def set_mode(self, mode: str):
        logger.info("Setting ScienceBenchBenchmark mode to '%s'", mode)
        self.registry.set_mode(mode)

    async def grade(self, submission_path: Path) -> float:
        """Grades a submission and returns a numerical fitness score for AFlow."""
        if not self.problems:
            return 0.0

        competition_id = self.problems[0].get("competition_id")
        if not competition_id:
            return 0.0

        try:
            competition = self.registry.get_competition(competition_id)
            if not submission_path.exists():
                logger.warning("Grading failed: submission file not found at %s", submission_path)
                return 0.0

            report = grade_submission(submission_path, competition)
            score = report.score if report.score is not None else 0.0

            is_lower_better = False
            try:
                if competition.leaderboard.exists():
                    import pandas as pd

                    leaderboard = pd.read_csv(competition.leaderboard)
                    if "score" in leaderboard.columns and len(leaderboard.index) > 1:
                        is_lower_better = competition.grader.is_lower_better(leaderboard)
            except Exception as exc:
                logger.warning(
                    "Could not determine score direction for %s: %s",
                    competition_id,
                    exc,
                )

            if is_lower_better:
                return 1.0 / (1.0 + score) if score > 0 else 1.0
            return float(score)

        except Exception as exc:
            logger.error("Error during grading for %s: %s", competition_id, exc)
            return 0.0

    def get_result_columns(self) -> List[str]:
        return [
            "competition_id",
            "submission_path",
            "answers_path",
            "score",
            "cost",
            "running_time",
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "gold_medal",
            "silver_medal",
            "bronze_medal",
            "above_median",
            "submission_exists",
            "valid_submission",
            "error_message",
        ]

    def _create_error_report(self, competition_id: str, submission_path: Path, error_msg: str) -> CompetitionReport:
        base_data = {
            "competition_id": competition_id,
            "score": None,
            "gold_threshold": float("nan"),
            "silver_threshold": float("nan"),
            "bronze_threshold": float("nan"),
            "median_threshold": float("nan"),
            "any_medal": False,
            "gold_medal": False,
            "silver_medal": False,
            "bronze_medal": False,
            "above_median": False,
            "submission_exists": submission_path.exists(),
            "valid_submission": False,
            "is_lower_better": False,
            "created_at": datetime.now().isoformat(),
            "submission_path": str(submission_path),
        }
        report = CompetitionReport.from_dict(base_data)
        logger.error("Error for %s: %s", competition_id, error_msg)
        return report

    async def evaluate_problem(
        self, problem: dict, eval_fn: Callable
    ) -> Tuple[Tuple, CompetitionReport, Optional[str]]:
        competition_id = problem.get("competition_id")
        if not competition_id:
            raise ValueError("Problem data must contain 'competition_id'")

        unique_id = uuid.uuid4().hex[:6]
        competition: Optional[Competition] = None

        # Default output: a unique CSV name under log_path/.
        # If the competition declares a specific submission format in config (e.g. `.npy`),
        # keep the same naming scheme but switch the file extension accordingly (resolved after
        # loading the competition config).
        output_filename = f"submission_{competition_id}_{unique_id}.csv"
        output_submission_path = (Path(self.log_path) / output_filename).absolute()

        start_time = time.perf_counter()

        cost = 0.0
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0
        report: Optional[CompetitionReport] = None
        error_message: Optional[str] = None

        try:
            competition = self.registry.get_competition(competition_id)

            submission_filename = getattr(competition, "submission_filename", None)
            submission_suffix = Path(submission_filename).suffix if submission_filename else ".csv"
            if submission_suffix and not submission_suffix.startswith("."):
                submission_suffix = f".{submission_suffix}"
            output_filename = f"submission_{competition_id}_{unique_id}{submission_suffix}"
            output_submission_path = (Path(self.log_path) / output_filename).absolute()

            if not is_dataset_prepared(competition, grading_only=False):
                raise ValueError(f"Dataset for '{competition_id}' not prepared in '{self.data_dir}'.")

            task = TaskDefinition(
                task_id=competition_id,
                task_type="kaggle",
                payload={
                    "description": competition.description,
                    "public_data_dir": str(competition.public_dir.absolute()),
                    "output_submission_path": str(output_submission_path.absolute()),
                },
            )

            result, cost, usage_summary = await eval_fn(task)

            input_tokens = usage_summary.get("prompt_tokens", 0)
            output_tokens = usage_summary.get("completion_tokens", 0)
            total_tokens = usage_summary.get("total_tokens", 0)

            if isinstance(result, Path):
                report = grade_submission(result, competition)
            elif isinstance(result, str) and result.startswith("[ERROR]"):
                error_message = f"DSAT workflow failed: {result}"
                report = self._create_error_report(competition_id, output_submission_path, error_message)
            else:
                error_message = f"Unexpected result type from eval_fn: {type(result).__name__}"
                report = self._create_error_report(competition_id, output_submission_path, error_message)

        except Exception as exc:
            error_message = f"Error during ScienceBench evaluation of {competition_id}: {exc}"
            logger.error(error_message, exc_info=True)
            report = self._create_error_report(competition_id, output_submission_path, error_message)

        if report is None:
            final_error = error_message or "Unknown error: report is None"
            report = self._create_error_report(competition_id, output_submission_path, final_error)
            error_message = final_error

        if not report.valid_submission:
            answers_path_str = str(getattr(competition, "answers", "N/A")) if competition else "N/A"
            self.log_mismatch(
                problem=competition_id,
                expected_output=answers_path_str,
                prediction=f"File: {output_submission_path}, Exists: {report.submission_exists}, Valid: {report.valid_submission}",
                extracted_output=report.score,
                extract_answer_code=error_message or "Grading function failed or file invalid/missing",
            )
            if not error_message:
                error_message = "Submission invalid or missing."

        running_time = round(time.perf_counter() - start_time, 4)
        answers_path_str = str(getattr(competition, "answers", "N/A")) if competition else "N/A"

        csv_tuple = (
            report.competition_id,
            str(report.submission_path),
            answers_path_str,
            report.score,
            cost,
            running_time,
            input_tokens,
            output_tokens,
            total_tokens,
            bool(getattr(report, "gold_medal", False)),
            bool(getattr(report, "silver_medal", False)),
            bool(getattr(report, "bronze_medal", False)),
            bool(getattr(report, "above_median", False)),
            report.submission_exists,
            report.valid_submission,
            error_message,
        )
        return csv_tuple, report, error_message
