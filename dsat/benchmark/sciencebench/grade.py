"""Grading utilities for ScienceBench"""
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, List

import pandas as pd
import numpy as np

from benchmarks.sciencebench.grade_helpers import CompetitionReport, InvalidSubmissionError
from benchmarks.sciencebench.utils import get_logger

if TYPE_CHECKING:
    from benchmarks.sciencebench.registry import Competition

logger = get_logger(__name__)


def load_answers(path_to_answers: Path) -> Any:
    """Load answers from a file."""
    if path_to_answers.suffix == ".csv":
        return pd.read_csv(path_to_answers)

    if path_to_answers.suffix == ".jsonl":
        import json
        result = []
        with open(path_to_answers, "r") as f:
            for line in f:
                result.append(json.loads(line))
        return result

    if path_to_answers.suffix == ".npy":
        return np.load(path_to_answers)

    raise ValueError(f"Unsupported file format for answers: {path_to_answers}")


def grade_submission(submission_path: Path, competition: "Competition") -> CompetitionReport:
    """
    Grade a submission file for a competition.

    Supports diverse output formats (e.g. .csv, .npy). For non-CSV formats, this function
    passes paths/arrays through to the competition's grader, allowing task-specific graders
    to control loading and comparison.
    """
    submission_exists = submission_path.exists()
    valid_submission = False
    score = None

    try:
        if not submission_exists:
            raise InvalidSubmissionError(f"Submission file does not exist: {submission_path}")

        submission_obj: Any
        answers_obj: Any

        if submission_path.suffix == ".csv":
            submission_obj = pd.read_csv(submission_path)
            answers_obj = load_answers(competition.answers)
        elif submission_path.suffix == ".npy":
            submission_obj = np.load(submission_path)
            # Prefer loading gold arrays when the answers are also .npy; otherwise pass the path through.
            answers_obj = load_answers(competition.answers) if competition.answers.suffix == ".npy" else competition.answers
        else:
            submission_obj = submission_path
            answers_obj = competition.answers

        score = competition.grader(submission_obj, answers_obj)
        valid_submission = score is not None

    except InvalidSubmissionError as e:
        logger.warning(f"Invalid submission: {e}")
    except Exception as e:
        logger.error(f"Error grading submission: {e}", exc_info=True)

    report = CompetitionReport(
        competition_id=competition.id,
        score=score,
        gold_medal=False,
        silver_medal=False,
        bronze_medal=False,
        above_median=False,
        submission_exists=submission_exists,
        valid_submission=valid_submission,
        is_lower_better=False,
        created_at=datetime.now().isoformat(),
        submission_path=str(submission_path),
    )
    return report


def grade_csv(submission_path: Path, competition: "Competition") -> CompetitionReport:
    """
    Grade a CSV submission file for a competition.

    Args:
        submission_path: Path to the submission file
        competition: Competition object

    Returns:
        CompetitionReport: Grading report
    """
    submission_exists = submission_path.exists()
    valid_submission = False
    score = None

    try:
        if not submission_exists:
            raise InvalidSubmissionError(f"Submission file does not exist: {submission_path}")

        # Load submission
        submission = pd.read_csv(submission_path)

        # Load answers
        answers = load_answers(competition.answers)

        # Grade the submission
        score = competition.grader(submission, answers)

        valid_submission = score is not None

    except InvalidSubmissionError as e:
        logger.warning(f"Invalid submission: {e}")
    except Exception as e:
        logger.error(f"Error grading submission: {e}", exc_info=True)

    # Create report
    report = CompetitionReport(
        competition_id=competition.id,
        score=score,
        gold_medal=False,
        silver_medal=False,
        bronze_medal=False,
        above_median=False,
        submission_exists=submission_exists,
        valid_submission=valid_submission,
        is_lower_better=False,  # Will be set by leaderboard ranking
        created_at=datetime.now().isoformat(),
        submission_path=str(submission_path),
    )

    return report


def aggregate_reports(reports: List[CompetitionReport]) -> dict:
    """
    Aggregate multiple competition reports.

    Args:
        reports: List of CompetitionReport objects

    Returns:
        dict: Aggregated statistics
    """
    total = len(reports)
    valid = sum(1 for r in reports if r.valid_submission)
    with_score = sum(1 for r in reports if r.score is not None)
    avg_score = sum(r.score for r in reports if r.score is not None) / with_score if with_score > 0 else 0

    return {
        "total_tasks": total,
        "valid_submissions": valid,
        "tasks_with_score": with_score,
        "average_score": avg_score,
        "gold_medals": sum(1 for r in reports if r.gold_medal),
        "silver_medals": sum(1 for r in reports if r.silver_medal),
        "bronze_medals": sum(1 for r in reports if r.bronze_medal),
    }
