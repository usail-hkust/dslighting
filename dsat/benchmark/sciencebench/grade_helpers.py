"""Helper classes related to grading"""
import inspect
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Union

import pandas as pd

from benchmarks.sciencebench.utils import get_logger, import_fn

logger = get_logger(__name__)


class InvalidSubmissionError(Exception):
    """Exception raised when a submission is invalid."""
    pass


class Grader:
    def __init__(self, name: str, grade_fn: str) -> None:
        self.name = name
        self.grade_fn = import_fn(grade_fn)
        assert isinstance(self.name, str), "Grader name must be a string."
        assert len(self.name) > 0, "Grader name cannot be empty."

    def is_lower_better(self, leaderboard: pd.DataFrame) -> bool:
        """
        Determines if a lower score is better based on the leaderboard.
        Returns True if lower scores are better, False otherwise.
        """
        scores = leaderboard["score"]
        top_score = scores.iloc[0]
        bottom_score = scores.iloc[-1]
        return bool(top_score < bottom_score)

    @staticmethod
    def from_dict(data: dict) -> "Grader":
        return Grader(**data)

    def __call__(self, submission: pd.DataFrame, answers: Any) -> Optional[float]:
        """
        Runs the grading function on a submission, returning the score rounded to 5 decimal places.
        """
        try:
            score = self.grade_fn(submission, answers)
        except InvalidSubmissionError as e:
            logger.warning(f"Invalid submission: {e}")
            return None
        except Exception as e:
            try:
                fpath = inspect.getfile(self.grade_fn)
                line_number = inspect.getsourcelines(self.grade_fn)[1]
                fn_info = f"{fpath}:{line_number}"
            except TypeError:
                fn_info = str(self.grade_fn)
            logger.error(f"Unexpected error during grading: {e}. Check {fn_info}")
            return None
        rounded_score = round(score, 5)
        return rounded_score


@dataclass
class CompetitionReport:
    """Report for a single competition evaluation."""
    competition_id: str
    score: Optional[float]
    gold_medal: bool
    silver_medal: bool
    bronze_medal: bool
    above_median: bool
    submission_exists: bool
    valid_submission: bool
    is_lower_better: bool
    created_at: str
    submission_path: str
    gold_threshold: float = float('nan')
    silver_threshold: float = float('nan')
    bronze_threshold: float = float('nan')
    median_threshold: float = float('nan')
    any_medal: bool = False

    @staticmethod
    def from_dict(data: dict) -> "CompetitionReport":
        return CompetitionReport(**data)

    def to_dict(self) -> dict:
        return {
            "competition_id": self.competition_id,
            "score": self.score,
            "gold_medal": self.gold_medal,
            "silver_medal": self.silver_medal,
            "bronze_medal": self.bronze_medal,
            "above_median": self.above_median,
            "submission_exists": self.submission_exists,
            "valid_submission": self.valid_submission,
            "is_lower_better": self.is_lower_better,
            "created_at": self.created_at,
            "submission_path": self.submission_path,
            "gold_threshold": self.gold_threshold,
            "silver_threshold": self.silver_threshold,
            "bronze_threshold": self.bronze_threshold,
            "median_threshold": self.median_threshold,
            "any_medal": self.any_medal,
        }
