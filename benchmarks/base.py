from abc import ABC, abstractmethod
from typing import Dict, Any
from pathlib import Path

from dsat.services.workspace import WorkspaceService

class BaseBenchmarkEvaluator(ABC):
    """
    Abstract base class for benchmark evaluators.

    An evaluator is responsible for scoring the final artifact produced by an
    agent run against a predefined benchmark dataset and metric.
    """
    def __init__(
        self,
        workspace: WorkspaceService,
        benchmark_path: Path,
        benchmark_config: Dict[str, Any]
    ):
        """
        Initializes the evaluator.

        Args:
            workspace: The WorkspaceService instance for the current run, used to locate generated artifacts.
            benchmark_path: The root path to the benchmark's directory (e.g., 'benchmarks/kaggle_house_prices').
            benchmark_config: The loaded configuration from the benchmark's YAML file.
        """
        self.workspace = workspace
        self.benchmark_path = benchmark_path
        self.config = benchmark_config

    @abstractmethod
    async def evaluate(self) -> Dict[str, Any]:
        """
        Executes the evaluation logic.

        This method should locate the agent's output artifact within the workspace,
        load the ground truth data from the benchmark path, compute the score,
        and return a dictionary of metrics.

        Returns:
            A dictionary containing metric names and their calculated values.
        """
        raise NotImplementedError