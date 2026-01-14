from abc import ABC, abstractmethod
from pathlib import Path
import tempfile
import logging
from typing import Tuple, Any
from dsat.models.task import TaskDefinition
from dsat.services.data_analyzer import DataAnalyzer

logger = logging.getLogger(__name__)


class TaskHandler(ABC):
    """
    Base class for handlers that translate between logical TaskDefinition and physical file interfaces required by DSATWorkflow.

    Each handler encapsulates preparation and parsing logic for specific task types (e.g., Kaggle, QA),
    allowing the workflow itself to remain task-agnostic.
    """
    def __init__(self):
        """
        Initialize the handler and create a temporary, self-managed directory
        for storing physical files generated for the task.
        """
        try:
            self.temp_dir = tempfile.TemporaryDirectory()
        except Exception as e:
            logger.error(f"Failed to create temporary directory for TaskHandler: {e}")
            self.temp_dir = None
        
        self.analyzer = DataAnalyzer()

    @abstractmethod
    def prepare_input(self, task: TaskDefinition) -> Tuple[str, str, Path, Path]:
        """
        Prepare the physical file input required by the workflow.

        This method converts logical tasks into physical parameters needed by DSATWorkflow.solve().

        Args:
            task: Logical task definition.

        Returns:
            A tuple (description, io_instructions, data_dir, output_path) to pass to workflow.solve().
        """
        raise NotImplementedError

    @abstractmethod
    def parse_output(self, output_path: Path) -> Any:
        """
        Parse the workflow's output file into structured results required by benchmarking.

        This method converts physical output files back into logical answers.

        Args:
            output_path: Path where the workflow saved its output.

        Returns:
            Final answer in the format expected by benchmarking (e.g., string for QA, Path object for Kaggle).
        """
        raise NotImplementedError

    def cleanup(self):
        """
        Explicitly clean up the temporary directory.
        """
        if self.temp_dir:
            try:
                self.temp_dir.cleanup()
                logger.debug(f"Successfully cleaned up temporary directory for {self.__class__.__name__}.")
            except Exception as e:
                logger.error(f"Error cleaning up temporary directory for {self.__class__.__name__}: {e}")

    def __del__(self):
        """Ensure cleanup is called when the object is garbage collected."""
        self.cleanup()


class KaggleTaskHandler(TaskHandler):
    """
    Handler for Kaggle-style file input/file output tasks.
    This is a "pass-through" implementation since tasks are already file-based.
    """
    def prepare_input(self, task: TaskDefinition) -> Tuple[str, str, Path, Path]:
        """Extract paths, analyze data, and separate description from I/O instructions."""
        if task.task_type != "kaggle":
            raise ValueError("KaggleTaskHandler can only handle tasks of type 'kaggle'.")

        description = task.payload.get("description")
        data_dir = Path(task.payload.get("public_data_dir"))
        output_path = Path(task.payload.get("output_submission_path"))

        if not all([description, data_dir, output_path]):
            raise ValueError("Kaggle task payload is missing required keys: 'description', 'public_data_dir', 'output_submission_path'.")
        if not data_dir.exists() or not data_dir.is_dir():
            raise FileNotFoundError(f"Kaggle public_data_dir not found: {data_dir}")

        logger.info(f"Analyzing input data for task '{task.task_id}'...")
        
        data_report = self.analyzer.analyze_data(data_dir, task_type="kaggle")
        io_instructions = self.analyzer.generate_io_instructions(output_path.name, optimization_context=False)

        augmented_description = f"{description}\n{data_report}"

        logger.debug(f"Preparing Kaggle task '{task.task_id}': data_dir='{data_dir}', output_path='{output_path}'")
        return augmented_description, io_instructions, data_dir, output_path

    def parse_output(self, output_path: Path) -> Path:
        """
        For Kaggle tasks, the result is the output file itself.
        This just validates that the file was created.
        """
        if not output_path.exists():
            # In actual evaluation, this will be caught and reported as a failure.
            logger.warning(f"Agent did not produce the required submission file at: {output_path}")
            # Return the path even if it doesn't exist, let the caller (e.g., benchmark) handle the file not found case.
        return output_path


class QATaskHandler(TaskHandler):
    """
    Handler for simple question-answer (QA) tasks.
    This is a "translation" implementation that converts string questions to files and expects answers as files.
    """
    def prepare_input(self, task: TaskDefinition) -> Tuple[str, str, Path, Path]:
        """Convert QA question to physical file input."""
        if task.task_type != "qa":
            raise ValueError("QATaskHandler can only handle tasks of type 'qa'.")
        if not self.temp_dir:
            raise RuntimeError("Temporary directory not available for QATaskHandler.")

        question = task.payload.get("question")
        if not question:
            raise ValueError("QA task payload is missing required key: 'question'.")

        data_dir = Path(self.temp_dir.name)
        
        # Create physical task representation
        problem_file = data_dir / "problem.txt"
        problem_file.write_text(question, encoding='utf-8')
        
        # Define output contract
        output_path = data_dir / "answer.txt"
        
        # This core instruction is now simpler
        core_instruction = (
            "Your task is to answer the question found in `problem.txt`. "
            "Write ONLY the final answer into the required output file."
        )

        data_report = self.analyzer.analyze_data(data_dir, task_type="qa")
        io_instructions = self.analyzer.generate_io_instructions(output_path.name, optimization_context=False)
        
        description = f"{core_instruction}\n{data_report}"
        
        logger.debug(f"Preparing QA task '{task.task_id}': input file='{problem_file}', expected output='{output_path}'")
        return description, io_instructions, data_dir, output_path

    def parse_output(self, output_path: Path) -> str:
        """Read and return the final answer string from the output file."""
        if not output_path.exists() or not output_path.is_file():
            logger.warning(f"Agent did not produce the answer file for QA task at: {output_path}")
            return "[ERROR] Agent did not produce an answer file."
        
        try:
            answer = output_path.read_text(encoding='utf-8').strip()
            logger.debug(f"Parsed QA answer from '{output_path}': '{answer[:50]}...'")
            return answer
        except Exception as e:
            logger.error(f"Failed to read or parse QA answer file '{output_path}': {e}")
            return f"[ERROR] Failed to parse answer file: {e}"


class DataSciTaskHandler(TaskHandler):
    """
    Handler for DataSciBench tasks.
    These are multi-step data science tasks with prompts and optional input files.
    """
    def prepare_input(self, task: TaskDefinition) -> Tuple[str, str, Path, Path]:
        """Prepare DataSciBench task input."""
        if task.task_type != "datasci":
            raise ValueError("DataSciTaskHandler can only handle tasks of type 'datasci'.")

        prompt = task.payload.get("prompt", "")
        input_dir = task.payload.get("input_dir", "")
        output_dir = task.payload.get("output_dir", "")

        if not prompt:
            raise ValueError("DataSci task payload is missing required key: 'prompt'.")

        # Use input_dir as data_dir, or temp_dir if no input files
        if input_dir and Path(input_dir).exists():
            data_dir = Path(input_dir)
        elif self.temp_dir:
            data_dir = Path(self.temp_dir.name)
        else:
            raise RuntimeError("No data directory available for DataSciTaskHandler.")

        # Output directory
        if output_dir:
            output_path = Path(output_dir) / "output.csv"
        else:
            output_path = data_dir / "output.csv"

        # Build description with the prompt
        description = prompt

        # Analyze data if available
        try:
            data_report = self.analyzer.analyze_data(data_dir, task_type="datasci")
            description = f"{prompt}\n\n{data_report}"
        except Exception as e:
            logger.debug(f"Data analysis skipped: {e}")

        # Generate I/O instructions
        io_instructions = (
            f"All input data files are in the current working directory.\n"
            f"Save all output files to the current working directory.\n"
            f"Follow the task instructions carefully and generate the required output files."
        )

        logger.debug(f"Preparing DataSci task '{task.task_id}': data_dir='{data_dir}', output_dir='{output_dir}'")
        return description, io_instructions, data_dir, output_path

    def parse_output(self, output_path: Path) -> Path:
        """
        For DataSci tasks, return the output directory path.
        The actual evaluation is done by the benchmark class using metric.yaml.
        """
        if output_path.parent.exists():
            return output_path.parent
        return output_path


class OpenEndedTaskHandler(TaskHandler):
    """
    Handler for open-ended tasks (mathematical modeling, simulations, strategy tasks).
    These tasks don't have ground truth answers and are evaluated via LLM judges.
    """
    def prepare_input(self, task: TaskDefinition) -> Tuple[str, str, Path, Path]:
        """Prepare open-ended task input."""
        if task.task_type != "open_ended":
            raise ValueError("OpenEndedTaskHandler can only handle tasks of type 'open_ended'.")
        if not self.temp_dir:
            raise RuntimeError("Temporary directory not available for OpenEndedTaskHandler.")

        # Get task paths from payload
        raw_dir_str = task.payload.get("raw_data_dir", "")
        description_file = task.payload.get("description_file", "")
        rubric_file = task.payload.get("rubric_file", "")

        # Use temp directory as working directory
        data_dir = Path(self.temp_dir.name)

        # Copy ONLY data files (CSV, JSON, etc.) - exclude description and rubric files
        if raw_dir_str:
            raw_dir = Path(raw_dir_str)
            if raw_dir.exists():
                import shutil
                for file in raw_dir.iterdir():
                    if file.is_file() and file.suffix in ['.csv', '.json', '.txt', '.xlsx', '.parquet']:
                        # Exclude description.md and rubric.md from being treated as data files
                        if file.name not in ['description.md', 'rubric.md']:
                            shutil.copy2(file, data_dir / file.name)
                            logger.debug(f"Copied data file: {file.name}")

        # Read task description and rubric from files if provided
        description = task.payload.get("description", "")
        rubric = task.payload.get("rubric", "")

        # Read from files if specified
        if description_file and Path(description_file).exists():
            try:
                description = Path(description_file).read_text(encoding='utf-8')
                logger.debug(f"Read description from {description_file} ({len(description)} chars)")
            except Exception as e:
                logger.warning(f"Failed to read description file {description_file}: {e}")

        if rubric_file and Path(rubric_file).exists():
            try:
                rubric = Path(rubric_file).read_text(encoding='utf-8')
                logger.debug(f"Read rubric from {rubric_file} ({len(rubric)} chars)")
            except Exception as e:
                logger.warning(f"Failed to read rubric file {rubric_file}: {e}")

        if not description:
            raise ValueError("Open-ended task payload is missing required key: 'description'.")

        # Output path - agent should create an artifacts directory or report
        output_path = data_dir / "artifacts"

        # Build the FULL task description directly in the prompt
        # Include description and evaluation criteria
        # IMPORTANT: For open-ended tasks, explicitly require artifacts directory creation

        task_description_section = f"""## Task Description

{description}
"""

        if rubric:
            task_description_section += f"""

## Evaluation Criteria

{rubric}
"""

        # Analyze available data files to provide schema information (excluding task files)
        data_report = self.analyzer.analyze_data(data_dir, task_type="datasci")

        # Combine everything into the full description
        # Note: data_report already contains "--- COMPREHENSIVE DATA REPORT ---" header
        full_description = f"""{task_description_section}

{data_report}

## CRITICAL OUTPUT INSTRUCTIONS

**YOU MUST CREATE AN `artifacts/` DIRECTORY AND SAVE ALL OUTPUTS THERE:**

```python
import os
artifact_dir = 'artifacts'
os.makedirs(artifact_dir, exist_ok=True)

# Save all your work to the artifacts directory:
# - Analysis code: artifacts/analysis.py
# - Visualizations: artifacts/plot_*.png
# - Data files: artifacts/results.csv
# - Models, notebooks, etc.
```

## Task Goals
- Your goal is to complete this task to the best of your ability
- Create appropriate output files (code, analysis, visualizations, etc.) in the `artifacts/` subdirectory
- The evaluation will be based on the quality and completeness of your work according to the evaluation criteria
"""

        # Generate I/O instructions - VERY EXPLICIT for open-ended tasks
        io_instructions = f"""**OUTPUT DIRECTORY STRUCTURE (MANDATORY):**

```python
# At the START of your code, create the artifacts directory:
import os
artifact_dir = 'artifacts'
os.makedirs(artifact_dir, exist_ok=True)

# Save ALL outputs to this directory:
# - Code: f"{{artifact_dir}}/solution.py"
# - Plots: f"{{artifact_dir}}/visualization_{{i}}.png"
# - Data: f"{{artifact_dir}}/results.csv"
```

**REQUIREMENTS:**
1. Create the `artifacts/` directory at the beginning of your code
2. Save ALL generated files (plots, models, data, code) to this directory
3. Do NOT save files to the current directory - use the artifacts/ subdirectory
4. Focus on quality, completeness, and following the evaluation criteria
"""

        logger.debug(f"Preparing open-ended task '{task.task_id}': output_path='{output_path}', description_len={len(description)}")
        return full_description, io_instructions, data_dir, output_path

    def parse_output(self, output_path: Path) -> Path:
        """
        For open-ended tasks, return the artifacts directory path.
        The actual evaluation is done by LLM judges, not CSV grading.
        """
        if not output_path.exists():
            # If artifacts directory doesn't exist, return the parent temp dir
            # This allows evaluation to proceed even if no artifacts were created
            logger.warning(f"Open-ended task did not create artifacts directory at: {output_path}")
            return output_path.parent

        logger.debug(f"Parsed open-ended task artifacts from: {output_path}")
        return output_path