"""
MLE Task Loader - Simple grading system

Uses user's grade function directly without complex framework loading.
"""

import logging
import uuid
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
import importlib
import sys

logger = logging.getLogger(__name__)


class MLETaskLoader:
    """
    MLE Task loader

    Functionality:
    1. Load task configuration from registry
    2. Read description.md
    3. Find data directory
    4. Use DataAnalyzer to generate standard format
    5. Generate unique output file name

    Usage:
        >>> loader = MLETaskLoader()
        >>> description, io_instructions, data_dir, output_path = loader.load_task("bike-sharing-demand")
    """

    def load_task(
        self,
        task_id: str,
        data_dir: Optional[Path] = None
    ) -> Tuple[str, str, Path, Path]:
        """
        Load standard MLE format task configuration

        Args:
            task_id: Task ID (e.g. "bike-sharing-demand")
            data_dir: Optional data directory path. If not provided, will search from registry

        Returns:
            (description, io_instructions, data_dir, output_path) standard format tuple
        """
        logger.info(f"Load MLE Task: {task_id}")

        # 1. Try to load configuration from registry
        try:
            from dslighting.registry import load_task_config
            config = load_task_config(task_id)

            # Get data directory
            if data_dir is None:
                data_dir = config.get("data_path")
                if data_dir:
                    data_dir = Path(data_dir)
                    logger.info(f"Loaded data directory from registry: {data_dir}")

            # Get description
            description_path = config.get("description")
            if description_path:
                description_path = Path(description_path)
                if description_path.exists():
                    description = description_path.read_text(encoding='utf-8')
                    logger.info(f"Loaded description from registry: {len(description)} characters")
                else:
                    logger.warning(f"Description file does not exist: {description_path}")
                    description = f"MLE competition task: {task_id}"
            else:
                description = f"MLE competition task: {task_id}"

            # Get sample_submission file name
            sample_submission = config.get("dataset", {}).get("sample_submission")
            if sample_submission:
                submission_name = Path(sample_submission).name.replace("sampleSubmission", "submission")
            else:
                submission_name = "submission.csv"

            # Generate unique output file name
            unique_id = uuid.uuid4().hex[:6]
            output_filename = f"submission_{task_id}_{unique_id}.csv"
            output_path = Path(output_filename)

            logger.info(f"Output file name: {output_filename}")

        except Exception as e:
            logger.warning(f"Failed to load from registry: {e}")
            logger.warning(f"Using default configuration")

            if data_dir is None:
                raise ValueError(f"Cannot automatically find data directory, please provide data_dir parameter")

            description = f"Analyze data in: {task_id}"
            output_path = Path("submission.csv")

        # 2. Use DSAT analyzer to generate data report and I/O instructions
        try:
            from dsat.services.data_analyzer import DataAnalyzer

            analyzer = DataAnalyzer()

            # Analyze data and generate report
            data_report = analyzer.analyze_data(data_dir, task_type="kaggle")

            # Generate I/O instructions
            io_instructions = analyzer.generate_io_instructions(
                output_path.name,
                optimization_context=False
            )

            # Merge description and data_report
            full_description = f"{description}\n\n{data_report}"

            logger.info(f"Used analyzer to generate standard format")
            logger.info(f"  - Description: {len(full_description)} characters")
            logger.info(f"  - I/O Instructions: {len(io_instructions)} characters")

        except Exception as e:
            logger.warning(f"Analyzer generation failed: {e}")
            logger.warning(f"Using simplified format")

            full_description = description
            io_instructions = (
                f"Read the training data, train a model, "
                f"and generate predictions saved to '{output_path.name}'."
            )

        return full_description, io_instructions, data_dir, output_path

    def load_benchmark(
        self,
        task_id: str,
        data_dir: Optional[Path] = None
    ):
        """
        Load benchmark for grading

        This is a simplified version that directly loads the user's grade function
        from the registry directory without any framework overhead.

        Args:
            task_id: Task ID
            data_dir: Data directory path

        Returns:
            Grader object with grade() method
        """
        logger.info(f"Loading grader for: {task_id}")

        try:
            # Load task configuration from registry
            from dslighting.registry import load_task_config
            config = load_task_config(task_id)

            # Get grader configuration
            grader_config = config.get("grader", {})
            grade_fn_str = grader_config.get("grade_fn")

            if not grade_fn_str:
                logger.warning(f"No grade_fn found in config for task: {task_id}")
                return SimpleGrader(task_id, data_dir)

            # Parse grade_fn string (format: "module:function_name")
            # Example: "grade:grade" means import grade module and call grade function
            try:
                if ":" not in grade_fn_str:
                    logger.warning(f"Invalid grade_fn format: {grade_fn_str}")
                    return SimpleGrader(task_id, data_dir)

                module_name, func_name = grade_fn_str.rsplit(":", 1)

                # Get the registry directory for this task
                # Path: dslighting/registry/{task_id}/
                registry_dir = Path(__file__).parent.parent / "registry" / task_id

                if not registry_dir.exists():
                    logger.warning(f"Registry directory does not exist: {registry_dir}")
                    return SimpleGrader(task_id, data_dir)

                # Add registry directory to sys.path so we can import from it
                registry_path = str(registry_dir)
                if registry_path not in sys.path:
                    sys.path.insert(0, registry_path)

                # Import the grade module from the registry directory
                grade_module = importlib.import_module(module_name)
                grade_func = getattr(grade_module, func_name)

                logger.info(f"Loaded grade function: {module_name}:{func_name} from {registry_dir}")

                # Get paths
                answers_path_str = config.get("dataset", {}).get("answers")
                if answers_path_str:
                    answers_path = Path(answers_path_str)
                    # Convert relative path to absolute path
                    if not answers_path.is_absolute():
                        # Relative to data/competitions directory
                        # Path format: bike-sharing-demand/prepared/private/test_answer.csv
                        # data_dir should be: data/competitions/bike-sharing-demand
                        # So we need to go up one level and use the relative path
                        if data_dir:
                            answers_path = data_dir.parent / answers_path
                        else:
                            # Fallback: use data/competitions as base
                            answers_path = Path("data/competitions") / answers_path
                else:
                    logger.warning(f"No answers path found in config")
                    return SimpleGrader(task_id, data_dir)

                return DirectGrader(
                    task_id=task_id,
                    data_dir=data_dir,
                    grade_func=grade_func,
                    answers_path=answers_path
                )

            except Exception as e:
                logger.warning(f"Failed to load grade function: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                return SimpleGrader(task_id, data_dir)

        except Exception as e:
            logger.warning(f"Failed to load benchmark configuration: {e}")
            logger.warning(f"Will fall back to simple grading")
            return SimpleGrader(task_id, data_dir)


class DirectGrader:
    """
    Direct grader that calls user's grade function directly

    This is the simplest and most reliable grading approach.
    Just calls: grade(submission_df, answers_df)
    """

    def __init__(self, task_id: str, data_dir: Optional[Path], grade_func, answers_path: Path):
        self.task_id = task_id
        self.data_dir = data_dir
        self.grade_func = grade_func
        self.answers_path = answers_path

    async def grade(self, submission_path: str) -> dict:
        """
        Grade submission file

        Args:
            submission_path: Submission file path

        Returns:
            Grading result dict with score
        """
        import pandas as pd

        try:
            logger.info(f"Grading with user's grade function: {submission_path}")

            # Load submission and answers
            submission_df = pd.read_csv(submission_path)
            answers_df = pd.read_csv(self.answers_path)

            logger.info(f"  Submission shape: {submission_df.shape}")
            logger.info(f"  Answers shape: {answers_df.shape}")

            # Call user's grade function directly
            # This is the simple interface: grade(submission_df, answers_df) -> float
            score = self.grade_func(submission_df, answers_df)

            logger.info(f"Grading completed: score = {score}")

            return {
                'score': float(score),
                'task_id': self.task_id,
                'valid_submission': True
            }

        except Exception as e:
            logger.error(f"Grading failed: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None


class SimpleGrader:
    """
    Simplified Grader implementation

    Used when grade function is not available
    """

    def __init__(self, task_id: str, data_dir: Optional[Path] = None):
        self.task_id = task_id
        self.data_dir = data_dir

    async def grade(self, submission_path: str) -> dict:
        """
        Simplified grading - check file existence only

        Args:
            submission_path: Submission file path

        Returns:
            Grading result (score = 0.0, just validation)
        """
        from pathlib import Path

        logger.info(f"Using simplified grading: {submission_path}")

        # Check if file exists
        if Path(submission_path).exists():
            return {
                'score': 0.0,
                'valid_submission': True,
                'note': 'Simple grading - file exists but no score calculated'
            }
        else:
            return None
