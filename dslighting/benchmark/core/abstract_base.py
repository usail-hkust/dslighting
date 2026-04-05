"""Abstract base classes for benchmark implementations.

This module defines the abstract interfaces for benchmark classes.
"""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


__all__ = [
    "AbstractBenchmark",
    "AbstractTaskEvaluator",
]


class AbstractBenchmark(ABC):
    """Abstract base class for all benchmark tests.

    Subclasses must provide:
    - A list of problems (dicts or objects)
    - get_result_columns() implementation
    - evaluate_problem() async implementation

    The class provides common functionality for:
    - Problem loading from JSONL files
    - Evaluation execution with scheduler integration
    - Result and metadata persistence
    - Error logging and mismatch tracking
    """

    def __init__(self, name: str, file_path: Optional[str], log_path: str, **kwargs: Any) -> None:
        """Initialize the benchmark.

        Args:
            name: Benchmark name.
            file_path: Path to JSONL file with problems.
            log_path: Directory for output logs.
            **kwargs: Additional keyword arguments.
        """
        self.name = name
        self.file_path = file_path
        self.log_path = log_path
        self._default_eval_fn: Optional[Callable] = kwargs.get("eval_fn")
        self.problems = self._load_problems()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_path = Path(self.log_path) / f"{self.name}_results_{timestamp}.csv"
        self.metadata_path = Path(self.log_path) / f"{self.name}_metadata_{timestamp}.json"
        self.mismatches_path = Path(self.log_path) / f"{self.name}_mismatches.log"

    def _load_problems(self) -> List[Dict[str, Any]]:
        """Load problems from jsonl file if provided.

        Returns:
            List of problem dictionaries.

        Raises:
            FileNotFoundError: If file_path is provided but file doesn't exist.
            JSONDecodeError: If file contains invalid JSON.
        """
        if not self.file_path:
            logger.debug(
                "No file_path provided. Subclass is expected to override _load_problems."
            )
            return []

        with open(self.file_path, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f]

    @abstractmethod
    def get_result_columns(self) -> List[str]:
        """Get the column names for the results CSV.

        Returns:
            List of column names.
        """

    @abstractmethod
    async def evaluate_problem(
        self,
        problem: Dict[str, Any],
        eval_fn: Callable,
        **kwargs: Any,
    ) -> Tuple:
        """Evaluate a single problem.

        Args:
            problem: Problem dictionary.
            eval_fn: Evaluation function to call.
            **kwargs: Additional keyword arguments.

        Returns:
            Tuple of (result_row, report, error_message).
        """

    def set_eval_function(self, eval_fn: Callable) -> None:
        """Bind a default task-evaluation function.

        Args:
            eval_fn: Evaluation function to bind.
        """
        self._default_eval_fn = eval_fn

    def log_mismatch(self, **kwargs: Any) -> None:
        """Log a mismatch to the mismatches log file.

        Args:
            **kwargs: Key-value pairs to log.
        """
        with open(self.mismatches_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(kwargs) + "\n")

    def _resolve_model_name_for_metadata(
        self, explicit_model_name: Optional[str] = None
    ) -> str:
        """Resolve model name for CSV metadata.

        Args:
            explicit_model_name: Explicitly provided model name.

        Returns:
            Resolved model name string.
        """
        if isinstance(explicit_model_name, str) and explicit_model_name.strip():
            return explicit_model_name.strip()

        bound_model_name = getattr(self, "model_name", None)
        if isinstance(bound_model_name, str) and bound_model_name.strip():
            return bound_model_name.strip()

        runner = getattr(self, "runner", None)
        runner_config = getattr(runner, "config", None)
        llm_config = getattr(runner_config, "llm", None)
        runner_model_name = getattr(llm_config, "model", None)
        if isinstance(runner_model_name, str) and runner_model_name.strip():
            return runner_model_name.strip()

        env_model_name = (os.environ.get("LLM_MODEL") or "").strip()
        if env_model_name:
            return env_model_name

        raw_model_configs = os.environ.get("LLM_MODEL_CONFIGS")
        if raw_model_configs:
            try:
                parsed = json.loads(raw_model_configs)
                if isinstance(parsed, dict):
                    for candidate in parsed.keys():
                        if isinstance(candidate, str) and candidate.strip():
                            return candidate.strip()
            except Exception as exc:
                logger.debug(
                    "Failed to parse LLM_MODEL_CONFIGS for metadata model resolution: %s",
                    exc,
                )

        return "N/A"

    @property
    def summary(self) -> Dict[str, Any]:
        """Get results summary similar to AgentResult.

        Returns:
            Dictionary containing aggregated benchmark statistics.
        """
        summary_stats = {
            "success": True,
            "output": getattr(self, "results", []),
            "score": None,
            "cost": 0.0,
            "duration": 0.0,
            "num_tasks": len(getattr(self, "results", [])),
            "num_successful": 0,
            "error": None,
            "metadata": {
                "benchmark_name": self.name,
                "results_path": str(self.results_path),
                "metadata_path": str(self.metadata_path),
            },
        }

        if self.results_path and self.results_path.exists():
            try:
                df = pd.read_csv(self.results_path)
                total_tasks = int(len(df))

                if "score" in df.columns:
                    score_series = pd.to_numeric(df["score"], errors="coerce")
                    valid_scores = score_series.dropna()
                    if len(valid_scores) > 0:
                        summary_stats["score"] = float(score_series.fillna(0.0).mean())
                        summary_stats["metadata"]["score_stats"] = {
                            "average": float(valid_scores.mean()),
                            "actual_average": float(score_series.fillna(0.0).mean()),
                            "scored_task_count": int(len(valid_scores)),
                            "unscored_task_count": int(total_tasks - len(valid_scores)),
                            "median": float(valid_scores.median()),
                            "std": float(valid_scores.std()),
                            "min": float(valid_scores.min()),
                            "max": float(valid_scores.max()),
                        }

                if "submission_exists" in df.columns:
                    exists_series = df["submission_exists"].map(
                        lambda value: str(value).strip().lower() in {"1", "true", "yes", "on"}
                    )
                    summary_stats["metadata"]["submission_stats"] = {
                        "exists_count": int(exists_series.sum()),
                        "exists_rate": float(exists_series.mean()) if len(exists_series) > 0 else 0.0,
                    }
                if "valid_submission" in df.columns:
                    valid_submission_series = df["valid_submission"].map(
                        lambda value: str(value).strip().lower() in {"1", "true", "yes", "on"}
                    )
                    submission_stats = summary_stats["metadata"].setdefault("submission_stats", {})
                    submission_stats.update(
                        {
                            "valid_count": int(valid_submission_series.sum()),
                            "valid_rate": float(valid_submission_series.mean()) if len(valid_submission_series) > 0 else 0.0,
                            "failed_submission_count": int(total_tasks - int(valid_submission_series.sum())),
                            "failed_submission_rate": float((total_tasks - int(valid_submission_series.sum())) / total_tasks) if total_tasks > 0 else 0.0,
                        }
                    )

                if "cost" in df.columns:
                    valid_costs = df["cost"].dropna()
                    if len(valid_costs) > 0:
                        summary_stats["cost"] = float(valid_costs.sum())

                if "running_time" in df.columns:
                    valid_times = df["running_time"].dropna()
                    if len(valid_times) > 0:
                        summary_stats["duration"] = float(valid_times.sum())
                        summary_stats["metadata"]["running_time_stats"] = {
                            "total": float(valid_times.sum()),
                            "mean": float(valid_times.mean()),
                        }

                if "status" in df.columns:
                    summary_stats["num_successful"] = len(
                        df[df["status"].isin(["passed", "completed", "success"])]
                    )
                elif "score" in df.columns:
                    summary_stats["num_successful"] = len(df["score"].dropna())

                summary_stats["num_tasks"] = len(df)

            except Exception as e:
                logger.debug("Failed to read results for summary: %s", e)

        return summary_stats


class AbstractTaskEvaluator(ABC):
    """Abstract base class for task evaluation logic.

    This class provides common functionality for evaluating tasks
    and processing results. Subclasses should implement the
    evaluate method to provide specific evaluation logic.
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

    @abstractmethod
    async def evaluate(
        self,
        task: Any,
        eval_fn: Callable,
        **kwargs: Any,
    ) -> Tuple[Any, Optional[Any], Optional[str]]:
        """Evaluate a single task.

        Args:
            task: Task to evaluate.
            eval_fn: Evaluation function to call.
            **kwargs: Additional keyword arguments.

        Returns:
            Tuple of (result_row, report, error_message).
        """

    def _process_result(
        self,
        task: Any,
        result: Any,
        error_message: Optional[str] = None,
    ) -> Tuple:
        """Process a result from the evaluation function.

        Args:
            task: Task that was evaluated.
            result: Result from eval_fn.
            error_message: Optional error message.

        Returns:
            Tuple of (result_row, report, error_message).
        """
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
        import json

        metadata = json.dumps(extras, ensure_ascii=True) if extras else ""

        task_id = getattr(task, "task_id", str(task))

        row = (
            task_id,
            score,
            cost,
            duration,
            output,
            error_message,
            metadata,
        )
        return row, None, error_message

    def _extract_error_message(self, result: Any) -> str:
        """Extract error message from result tuple.

        Args:
            result: Result tuple from evaluate_problem.

        Returns:
            Error message string.
        """
        if not isinstance(result, tuple):
            return ""
        if len(result) < 3:
            return ""
        candidate = result[2]
        if isinstance(candidate, str):
            return candidate
        return str(candidate or "")

    def _is_oom_error(self, message: Any) -> bool:
        """Check if an error message indicates an out-of-memory error.

        Args:
            message: Error message to check.

        Returns:
            True if OOM error detected.
        """
        text = str(message or "").lower()
        if not text:
            return False
        markers = (
            "out of memory",
            "cuda out of memory",
            "cuda error: out of memory",
            "cublas_status_alloc_failed",
            "resourceexhaustederror",
            "cannot allocate memory",
            "failed to allocate",
            "hip out of memory",
            "mps backend out of memory",
            "memoryerror",
            "oom",
        )
        return any(marker in text for marker in markers)

    def _is_timeout_error(self, message: Any) -> bool:
        """Check if an error message indicates a timeout error.

        Args:
            message: Error message to check.

        Returns:
            True if timeout error detected.
        """
        text = str(message or "").lower()
        if not text:
            return False
        markers = ("timed out", "timeout", "wrk-003")
        return any(marker in text for marker in markers)
