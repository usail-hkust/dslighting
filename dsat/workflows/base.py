# dsat/workflows/base.py

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any
import logging


# --- New, standardized workflow interface (core) ---
class DSATWorkflow(ABC):
    """
    New standardized workflow abstract base class defining the "physical interface contract".

    Any workflow implementing this interface becomes a generic problem solver
    that is completely decoupled from the specific form of the task (QA, Kaggle, etc.).
    It only understands files and directories.
    """
    def __init__(self, operators: Dict[str, Any], services: Dict[str, Any], agent_config: Dict[str, Any]):
        """
        Initialize through dependency injection.

        Args:
            operators: A dictionary containing all operator instances needed by this workflow.
            services: A dictionary containing required service instances (e.g., LLMService, SandboxService).
            agent_config: A dictionary containing agent behavior-specific configuration.
        """
        self.operators = operators
        self.services = services
        self.agent_config = agent_config

    @abstractmethod
    async def solve(
        self,
        description: str,
        io_instructions: str, # NEW ARGUMENT
        data_dir: Path,
        output_path: Path
    ) -> None:
        """
        Solve a given task based on the physical file interface.

        This is the core method for all standardized workflows. Workflows implementing this method need to:
        1.  Treat `data_dir` as their only input source.
        2.  Execute their internal logic (e.g., call LLM, run code) to solve the task described in `description`.
        3.  Write their final, evaluable answer as a single file to the complete path specified by `output_path`.

        Args:
            description: Natural language goal description and data analysis report.
            io_instructions: Explicit, standardized instructions for reading input and writing output.
            data_dir: A directory containing all input files needed to solve the task (e.g., `problem.txt`, `train.csv`).
            output_path: The complete path where the final output file (e.g., `answer.txt`, `submission.csv`) must be saved.
        """
        raise NotImplementedError
