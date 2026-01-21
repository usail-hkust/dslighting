"""Data preparation utilities for ScienceBench"""
from pathlib import Path
from typing import TYPE_CHECKING

from benchmarks.sciencebench.utils import get_logger

if TYPE_CHECKING:
    from benchmarks.sciencebench.registry import Competition

logger = get_logger(__name__)


def is_dataset_prepared(competition: "Competition", grading_only: bool = False) -> bool:
    """
    Check if a dataset is prepared.

    Args:
        competition: Competition object
        grading_only: If True, only check if grading files exist (answers, sample_submission)

    Returns:
        bool: True if dataset is prepared, False otherwise
    """
    # Check if public directory exists
    if not grading_only:
        if not competition.public_dir.exists():
            logger.debug(f"Public directory does not exist: {competition.public_dir}")
            return False

        # Check if sample submission exists
        if not competition.sample_submission.exists():
            logger.debug(f"Sample submission does not exist: {competition.sample_submission}")
            return False

    # Check if private directory exists
    if not competition.private_dir.exists():
        logger.debug(f"Private directory does not exist: {competition.private_dir}")
        return False

    # Check if answers file exists
    if not competition.answers.exists():
        logger.debug(f"Answers file does not exist: {competition.answers}")
        return False

    return True


def prepare_dataset(competition: "Competition") -> bool:
    """
    Prepare a dataset by calling its prepare function.

    Args:
        competition: Competition object

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Preparing dataset for {competition.id}...")

        # Create directories
        competition.raw_dir.mkdir(parents=True, exist_ok=True)
        competition.public_dir.mkdir(parents=True, exist_ok=True)
        competition.private_dir.mkdir(parents=True, exist_ok=True)

        # Call the prepare function
        competition.prepare_fn(
            competition.raw_dir,
            competition.public_dir,
            competition.private_dir
        )

        # Verify preparation
        if is_dataset_prepared(competition):
            logger.info(f"Dataset prepared successfully for {competition.id}")
            return True
        else:
            logger.error(f"Dataset preparation incomplete for {competition.id}")
            return False

    except Exception as e:
        logger.error(f"Error preparing dataset for {competition.id}: {e}", exc_info=True)
        return False
