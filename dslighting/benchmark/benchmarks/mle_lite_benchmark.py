"""
MLE-Bench Lite Benchmark

Inherits MLE-Bench capabilities + DSLighting base capabilities.

This benchmark provides:
1. BaseBenchmark (DSLighting):
   - Unified batch evaluation interface
   - Statistical analysis
   - Config-driven execution

2. MLEBenchmark (open-source, optional):
   - Task loading (Registry)
   - Grading logic (grade_csv)
   - Competition management

Note: DABenchmark, MLEBenchmark, and ScienceBenchBenchmark are optional
integrations. They are loaded lazily when needed. If not available,
benchmarks will gracefully degrade to using only core functionality.

Example:
    >>> # Use default curated tasks
    >>> benchmark = MLELiteBenchmark()
    >>> results = benchmark.run_evaluation(eval_fn)
    >>>
    >>> # Custom task list
    >>> benchmark = MLELiteBenchmark(
    ...     competitions=["bike-sharing-demand", "titanic"]
    ... )
    >>> results = benchmark.run_evaluation(eval_fn)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from dslighting.benchmark.core.base import BaseBenchmark, BenchmarkTaskEvaluator
from dslighting.core.types.task import TaskDefinition

logger = logging.getLogger(__name__)


__all__ = ["MLELiteBenchmark", "MPPETaskEvaluator"]


class MPPETaskEvaluator(BenchmarkTaskEvaluator):
    """Task evaluator for MLE-Bench Lite benchmarks.

    This evaluator processes tasks from MLE-Bench competitions and
    transforms evaluation results into the standard format.

    Attributes:
        RESULT_COLUMNS: Result column names for CSV output.
    """

    RESULT_COLUMNS = [
        "task_id",
        "score",
        "cost",
        "duration",
        "output",
        "error",
        "metadata",
    ]

    async def evaluate(
        self,
        task: TaskDefinition,
        eval_fn: Callable,
        **kwargs: Any,
    ) -> Tuple[Tuple, Optional[Any], Optional[str]]:
        """Evaluate a single MLE-Bench task.

        Args:
            task: TaskDefinition to evaluate.
            eval_fn: Evaluation function to call.
            **kwargs: Additional keyword arguments.

        Returns:
            Tuple of (result_row, report, error_message).
        """
        error_message = None

        try:
            result = await eval_fn(task, **kwargs)
        except Exception as exc:
            result = {}
            error_message = str(exc)

        if not isinstance(result, dict):
            error_message = error_message or f"Invalid result type: {type(result)}"
            result = {"output": result}

        score = result.get("score")
        cost = result.get("cost")
        duration = result.get("duration")
        output = result.get("output")
        if not error_message:
            error_message = result.get("error")

        extras = {
            key: value
            for key, value in result.items()
            if key not in {"task_id", "score", "cost", "duration", "output", "error"}
        }
        metadata = json.dumps(extras, ensure_ascii=True) if extras else ""

        row = (
            task.task_id,
            score,
            cost,
            duration,
            output,
            error_message,
            metadata,
        )
        return row, None, error_message


class MLELiteBenchmark(BaseBenchmark):
    """MLE-Bench Lite - Curated Core Competitions.

    This benchmark provides access to a curated set of MLE-Bench competitions
    with DSLighting's unified evaluation interface.

    Attributes:
        DEFAULT_COMPETITIONS: Default list of curated competitions.
        RESULT_COLUMNS: Result column names for CSV output.

    Example:
        >>> # Use default curated tasks
        >>> benchmark = MLELiteBenchmark()
        >>> results = benchmark.run_evaluation(eval_fn)
        >>>
        >>> # Custom task list
        >>> benchmark = MLELiteBenchmark(
        ...     competitions=["bike-sharing-demand", "titanic"]
        ... )
        >>> results = benchmark.run_evaluation(eval_fn)
    """

    # Built-in curated task list (22 competitions)
    DEFAULT_COMPETITIONS = [
        "aerial-cactus-identification",
        "aptos2019-blindness-detection",
        "denoising-dirty-documents",
        "detecting-insults-in-social-commentary",
        "dog-breed-identification",
        "dogs-vs-cats-redux-kernels-edition",
        "histopathologic-cancer-detection",
        "jigsaw-toxic-comment-classification-challenge",
        "leaf-classification",
        "mlsp-2013-birds",
        "new-york-city-taxi-fare-prediction",
        "nomad2018-predict-transparent-conductors",
        "plant-pathology-2020-fgvc7",
        "random-acts-of-pizza",
        "ranzcr-clip-catheter-line-classification",
        "siim-isic-melanoma-classification",
        "spooky-author-identification",
        "tabular-playground-series-dec-2021",
        "tabular-playground-series-may-2022",
        "text-normalization-challenge-english-language",
        "text-normalization-challenge-russian-language",
        "the-icml-2013-whale-challenge-right-whale-redux",
    ]

    RESULT_COLUMNS = [
        "task_id",
        "score",
        "cost",
        "duration",
        "output",
        "error",
        "metadata",
    ]

    def __init__(
        self,
        competitions: Optional[List[str]] = None,
        name: str = "mle-lite",
        log_path: str = "runs/benchmarks/mle-lite",
        data_dir: Optional[Path] = None,
    ):
        """Initialize MLE-Bench Lite.

        Args:
            competitions: Competition list (if None, use default curated tasks).
            name: Benchmark name.
            log_path: Log path.
            data_dir: Data directory.
        """
        self.competitions = competitions or self.DEFAULT_COMPETITIONS

        if data_dir is None:
            data_dir = Path("data/competitions")

        self.data_dir = Path(data_dir)

        # Initialize MLE-Bench capabilities
        self._init_mlebench()

        # Convert to TaskDefinition
        self.tasks = self._convert_to_task_definitions()

        # Initialize BaseBenchmark (problem-based)
        super().__init__(name, file_path=None, log_path=log_path)
        Path(self.log_path).mkdir(parents=True, exist_ok=True)

        logger.debug("MLE-Lite Benchmark initialized")
        logger.info(f"  Competitions: {len(self.competitions)}")
        logger.info(f"  Data dir: {self.data_dir}")

    def _load_problems(self) -> List[Dict[str, Any]]:
        """Load problems from internal task list."""
        return [{"task": task} for task in self.tasks]

    def get_result_columns(self) -> List[str]:
        """Get result column names.

        Returns:
            List of column names for the results CSV.
        """
        return self.RESULT_COLUMNS

    async def evaluate_problem(
        self,
        problem: Dict[str, Any],
        eval_fn: Callable,
        **kwargs: Any,
    ) -> Tuple[Tuple, Optional[Any], Optional[str]]:
        """Evaluate a single problem.

        Args:
            problem: Problem dictionary containing task.
            eval_fn: Evaluation function to call.
            **kwargs: Additional keyword arguments.

        Returns:
            Tuple of (result_row, report, error_message).
        """
        evaluator = MPPETaskEvaluator()
        task: TaskDefinition = problem["task"]
        return await evaluator.evaluate(task, eval_fn, **kwargs)

    def _init_mlebench(self) -> None:
        """Initialize MLE-Bench capabilities.

        Note: MLE-Bench is an optional dependency. If import fails,
        the benchmark will run without MLE-Bench integration.
        """
        try:
            # Import MLE-Bench components from vendored package
            from dslighting.benchmark.vendor.mlebench.registry import Registry as MLERegistry
            from dslighting.benchmark.vendor.dabench.registry import Registry as DABenchRegistry
            from dslighting.benchmark.vendor.mlebench.data import is_dataset_prepared

            self.mle_registry = MLERegistry()
            self.mle_registry = self.mle_registry.set_data_dir(self.data_dir)
            self.dabench_registry = DABenchRegistry().set_data_dir(self.data_dir)

            self.is_dataset_prepared = is_dataset_prepared

            logger.info("MLE-Bench capabilities loaded")

        except ImportError as e:
            logger.warning("MLE-Bench import failed: %s", e)
            logger.warning("Will run without MLE-Bench integration")
            self.mle_registry = None
            self.dabench_registry = None
            self.is_dataset_prepared = None

    @staticmethod
    def _is_dabench_competition(task_id: str) -> bool:
        """Check if a task ID is from DABench.

        Args:
            task_id: Task identifier to check.

        Returns:
            True if the task is from DABench.
        """
        return task_id.startswith("dabench-")

    def _get_registry_for_competition(self, task_id: str):
        """Get the appropriate registry for a competition.

        Args:
            task_id: Competition task ID.

        Returns:
            Registry instance (MLE-Bench or DABench).
        """
        if self._is_dabench_competition(task_id):
            return self.dabench_registry
        return self.mle_registry

    def _convert_to_task_definitions(self) -> List[TaskDefinition]:
        """Convert competitions to TaskDefinition objects.

        Returns:
            List of TaskDefinition objects.
        """
        tasks = []

        for comp_id in self.competitions:
            try:
                registry = self._get_registry_for_competition(comp_id)
                if registry:
                    try:
                        competition = registry.get_competition(comp_id)
                        description = competition.description if hasattr(competition, 'description') else f"Competition: {comp_id}"
                        public_dir = competition.public_dir if hasattr(competition, 'public_dir') else None
                        private_dir = competition.private_dir if hasattr(competition, 'private_dir') else None

                    except Exception:
                        description = f"Competition: {comp_id}"
                        public_dir = None
                        private_dir = None
                else:
                    description = f"Competition: {comp_id}"
                    public_dir = None
                    private_dir = None

                task = TaskDefinition(
                    task_id=comp_id,
                    task_type="kaggle",
                    payload={
                        "description": description,
                        "data_dir": str(self.data_dir / comp_id),
                        "public_data_dir": str(public_dir) if public_dir else str(self.data_dir / comp_id / "prepared" / "public"),
                        "output_submission_path": str(self.data_dir / comp_id / "submission.csv"),
                    }
                )

                tasks.append(task)

            except Exception as e:
                logger.warning(f"Failed to convert competition '{comp_id}': {e}")
                continue

        logger.info(f"Converted {len(tasks)} competitions to TaskDefinition")

        return tasks

    async def run_evaluation(self, eval_fn: Callable, **kwargs) -> List[Dict[str, Any]]:
        """Run batch evaluation using MLE-Bench grading capabilities.

        Args:
            eval_fn: Evaluation function.
            **kwargs: Extra parameters.

        Returns:
            List of evaluation results.
        """
        logger.info(f"Running MLE-Lite evaluation with {len(self.tasks)} tasks")

        results = await super().run_evaluation(eval_fn, **kwargs)
        return results or []

    def grade_submission(
        self,
        task_id: str,
        submission_path: Path,
    ) -> Optional[float]:
        """Grade a single submission using MLE-Bench grading logic.

        Args:
            task_id: Task ID to grade.
            submission_path: Path to submission CSV.

        Returns:
            Score (None if grading failed).
        """
        registry = self._get_registry_for_competition(task_id)
        if not registry:
            logger.warning("Registry not available, cannot grade submission")
            return None

        try:
            from dslighting.benchmark.vendor.mlebench.grade import grade_csv

            competition = registry.get_competition(task_id)
            report = grade_csv(submission_path, competition)

            return report.score if report.score is not None else None

        except Exception as e:
            logger.error(f"Grading failed for '{task_id}': {e}")
            return None

    @classmethod
    def get_default_competitions(cls) -> List[str]:
        """Get the default curated competition list.

        Returns:
            List of competition IDs.
        """
        return cls.DEFAULT_COMPETITIONS.copy()

    @classmethod
    def list_available_competitions(
        cls,
        data_dir: Optional[Path] = None,
    ) -> List[str]:
        """List available competitions in the data directory.

        Args:
            data_dir: Data directory to scan.

        Returns:
            List of available competition IDs.
        """
        if data_dir is None:
            data_dir = Path("data/competitions")

        competitions = []

        for comp_dir in data_dir.iterdir():
            if comp_dir.is_dir() and (comp_dir / "prepared").exists():
                competitions.append(comp_dir.name)

        return sorted(competitions)
