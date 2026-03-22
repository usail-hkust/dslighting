"""Helper classes related to grading"""
import inspect
from typing import Any, Optional, Union

import pandas as pd

from dslighting.benchmark.grading.errors import InvalidSubmissionError
from dslighting.benchmark.reporting.models import CompetitionReport
from dslighting.benchmark.vendor.sciencebench.utils import get_logger, import_fn

logger = get_logger(__name__)


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
