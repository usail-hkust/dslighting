"""
Custom benchmark implementation - House price prediction example.

This DABench-style benchmark shows how to:
1. Organize competition metadata and dataset directories.
2. Separate data preparation from scoring.
3. Integrate with the DSAT framework.
"""

import sys
import uuid
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple, Optional

import pandas as pd

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dsat.benchmark.benchmark import BaseBenchmark
from dsat.models.task import TaskDefinition

logger = logging.getLogger(__name__)


class HousePriceBenchmark(BaseBenchmark):
    """
    House price prediction benchmark (DABench style).

    Layout:
    examples/custom_benchmark/en/
    ├── competitions/custom_house_price_prediction/
    │   ├── config.yaml
    │   ├── description.md
    │   ├── grade.py
    │   └── prepare.py
    └── data/custom-house-price-prediction/
        ├── raw/houses.csv
        └── prepared/
            ├── public/
            │   ├── train.csv
            │   └── sample_submission.csv
            └── private/
                └── answer.csv
    """

    def __init__(
        self,
        name: str,
        file_path: Optional[str],
        log_path: str,
        data_dir: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the house price benchmark.

        Args:
            name: Benchmark name.
            file_path: Compatibility arg, not used.
            log_path: Directory for logs and results.
            data_dir: Dataset root (defaults to ./data).
        """
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).parent / "data"
        self.competitions_dir = Path(__file__).parent / "competitions"

        super().__init__(name, file_path, log_path)

        # Ensure log directory exists
        Path(self.log_path).mkdir(parents=True, exist_ok=True)

        # Load tasks
        self.problems = self._load_problems()
        logger.info("HousePriceBenchmark initialized with %d task(s)", len(self.problems))

    def _load_problems(self) -> List[Dict[str, Any]]:
        """
        Load the task list.

        Returns:
            List[Dict]: task list with task_id and related paths.
        """
        competition_id = "custom-house-price-prediction"
        competition_module = "custom_house_price_prediction"
        competition_data_dir = self.data_dir / competition_id
        competition_meta_dir = self.competitions_dir / competition_module

        if not competition_data_dir.exists():
            logger.error("Competition data directory does not exist: %s", competition_data_dir)
            logger.info("Run: python prepare_example_data.py")
            return []

        # Check prepared data
        prepared_dir = competition_data_dir / "prepared"
        if not prepared_dir.exists():
            logger.error("Data not prepared, please run prepare.py")
            return []

        problems = [{
            "task_id": competition_id,
            "competition_dir": str(competition_data_dir),
            "competitions_meta_dir": str(competition_meta_dir)
        }]

        logger.debug("Loaded task: %s", competition_id)
        return problems

    def get_result_columns(self) -> List[str]:
        """
        Define result CSV columns.

        Returns:
            List[str]: column names.
        """
        return [
            "task_id",
            "submission_path",
            "rmse_score",
            "cost",
            "submission_valid",
            "error_message"
        ]

    async def evaluate_problem(
        self,
        problem: Dict[str, Any],
        eval_fn: Callable
    ) -> Tuple[Tuple, Any, Optional[str]]:
        """
        Evaluate the house price task.

        Args:
            problem: Task metadata dictionary.
            eval_fn: DSAT workflow evaluation function.

        Returns:
            Tuple: (csv_tuple, report, error_message)
        """
        task_id = problem["task_id"]
        competition_dir = Path(problem["competition_dir"])
        competitions_meta_dir = Path(problem["competitions_meta_dir"])

        logger.info("Evaluating task: %s", task_id)

        # Define output file path
        unique_id = uuid.uuid4().hex[:6]
        output_file = Path(self.log_path) / f"submission_{task_id}_{unique_id}.csv"

        # Initialize result placeholders
        rmse_score = float('inf')
        cost = 0.0
        submission_valid = False
        error_message = None

        try:
            # 1. Build TaskDefinition (Kaggle-style)
            description_file = competitions_meta_dir / "description.md"
            description = description_file.read_text(encoding='utf-8') if description_file.exists() else ""

            task = TaskDefinition(
                task_id=task_id,
                task_type="kaggle",  # File I/O style task
                payload={
                    "description": description,
                    "public_data_dir": str(competition_dir / "prepared" / "public"),
                    "output_submission_path": str(output_file)
                }
            )

            # 2. Execute workflow
            logger.info("Running workflow: %s", task_id)
            result, cost = await eval_fn(task)

            # 3. Ensure submission exists
            if isinstance(result, str) and result.startswith("[ERROR]"):
                error_message = result
                logger.error("Workflow failed: %s", error_message)

            elif output_file.exists():
                # 4. Grade submission
                try:
                    logger.info("Scoring task: %s", task_id)

                    # Load submission and answers
                    submission = pd.read_csv(output_file)
                    answer_file = competition_dir / "prepared" / "private" / "answer.csv"
                    answers = pd.read_csv(answer_file)

                    # Import grader dynamically
                    sys.path.insert(0, str(self.competitions_dir))
                    from custom_house_price_prediction.grade import grade

                    # Compute RMSE
                    rmse_score = grade(submission, answers)
                    submission_valid = True

                    logger.info("Task %s RMSE: %.2f", task_id, rmse_score)

                except Exception as e:
                    error_message = f"Grading failed: {str(e)}"
                    logger.error(error_message, exc_info=True)
            else:
                error_message = "Submission file not created"
                logger.error(error_message)

        except Exception as e:
            error_message = f"Task evaluation failed: {str(e)}"
            logger.error(error_message, exc_info=True)

        # Build result tuple
        csv_tuple = (
            task_id,
            str(output_file),
            rmse_score,
            cost,
            submission_valid,
            error_message
        )

        report = {
            "rmse": rmse_score,
            "valid": submission_valid,
            "cost": cost
        }

        return csv_tuple, report, error_message


if __name__ == "__main__":
    """
    Standalone test script.

    Run this file to test the benchmark without a real workflow.
    """
    import asyncio

    async def mock_eval_fn(task: TaskDefinition) -> Tuple[Any, float]:
        """Mock evaluator that generates random predictions."""
        print(f"[Mock] Running task: {task.task_id}")

        # Read sample submission to get row count
        public_dir = Path(task.payload["public_data_dir"])
        sample_submission = pd.read_csv(public_dir / "sample_submission.csv")

        # Generate random predictions (simple baseline)
        import numpy as np
        np.random.seed(42)
        predictions = sample_submission.copy()
        predictions['predicted_price'] = np.random.uniform(200000, 400000, len(predictions))

        # Save submission
        output_path = task.payload["output_submission_path"]
        predictions.to_csv(output_path, index=False)
        print(f"[Mock] Submission saved: {output_path}")

        return Path(output_path), 0.0

    async def test_benchmark():
        """Test the benchmark end-to-end."""
        print("=" * 60)
        print("Testing HousePriceBenchmark")
        print("=" * 60)

        # Create benchmark instance
        benchmark = HousePriceBenchmark(
            name="house_price_test",
            file_path=None,
            log_path="./test_results"
        )

        if not benchmark.problems:
            print("\n❌ No tasks loaded")
            print("Run:")
            print("  1. python prepare_example_data.py")
            print("  2. python competitions/custom_house_price_prediction/prepare.py")
            return

        print(f"\n✓ Loaded {len(benchmark.problems)} task(s)\n")

        # Evaluate the first task
        problem = benchmark.problems[0]
        csv_tuple, report, error = await benchmark.evaluate_problem(problem, mock_eval_fn)

        # Display results
        print("\n" + "=" * 60)
        print("Results:")
        print("=" * 60)
        print(f"Task ID: {csv_tuple[0]}")
        print(f"RMSE: {csv_tuple[2]:.2f}")
        print(f"Submission valid: {csv_tuple[4]}")
        print(f"Error message: {csv_tuple[5] or 'None'}")
        print(f"\nFull report: {report}")

    # Run test
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_benchmark())
