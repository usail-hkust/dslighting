"""
Convenience Functions - Top-Level User API

This module provides simple, high-level functions for common tasks in DSLighting.
These functions are designed for ease of use and quick prototyping.
"""

from pathlib import Path
from typing import Union, Optional
import logging

logger = logging.getLogger(__name__)
from .agent import Agent
from dslighting.core.data import DataLoader, TaskContext
from dslighting.error import TaskError


_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
_VENDOR_REGISTRY_ROOTS = [
    _PACKAGE_ROOT / "benchmark" / "vendor" / "mlebench" / "competitions",
    _PACKAGE_ROOT / "benchmark" / "vendor" / "dabench" / "competitions",
    _PACKAGE_ROOT / "benchmark" / "vendor" / "sciencebench" / "competitions",
]


def _resolve_task_data_path(task_id: str) -> Optional[Path]:
    candidates = [
        Path.cwd() / "data" / "competitions" / task_id,
        _PACKAGE_ROOT.parent / "data" / "competitions" / task_id,
        _PACKAGE_ROOT / "datasets" / task_id,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _resolve_registry_root(task_id: str) -> Optional[Path]:
    for registry_root in _VENDOR_REGISTRY_ROOTS:
        if (registry_root / task_id / "config.yaml").exists():
            return registry_root
    return None


def _resolve_task_description(task_id: str, registry_root: Optional[Path]) -> Optional[str]:
    if registry_root is None:
        return None

    config_path = registry_root / task_id / "config.yaml"
    if not config_path.exists():
        return None

    try:
        import yaml

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    except (FileNotFoundError, PermissionError, yaml.YAMLError) as e:
        logger.debug(f"Failed to load config from {config_path}: {e}")
        return None

    description_rel = config.get("description")
    if description_rel:
        description_path = _PACKAGE_ROOT / "benchmark" / str(description_rel)
        if description_path.exists():
            try:
                return description_path.read_text(encoding="utf-8").strip()
            except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
                logger.debug(f"Failed to read description from {description_path}: {e}")
                pass

    fallback = registry_root / task_id / "description.md"
    if fallback.exists():
        try:
            return fallback.read_text(encoding="utf-8").strip()
        except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
            logger.debug(f"Failed to read fallback description from {fallback}: {e}")
            return None

    return None


def setup(
    model: str = "gpt-4o",
    api_key: Optional[str] = None,
) -> None:
    """Configure DSLighting with default settings.

    This function sets up the global configuration for DSLighting including
    the default LLM model and API key. Call this before running any agents.

    Args:
        model: The default LLM model to use for all agent operations.
            Common options include "gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet".
        api_key: Optional API key for the LLM provider. If not provided,
            the key should be set via environment variables (e.g., OPENAI_API_KEY).

    Example:
        >>> from dslighting import setup
        >>> setup(model="gpt-4o", api_key="sk-...")
    """
    import os

    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

    print(f"[OK] DSLighting configured with model: {model}")


def load_data(
    data: Union[str, Path],
    task: Optional[str] = None,
    target: Optional[str] = None,
    registry_dir: Union[str, Path, None] = None,
) -> TaskContext:
    """Load data for agent processing.

    This function loads data from various sources including local files,
    directories, or built-in benchmark datasets. It creates a TaskContext
    object that provides the agent with a unified view of the data and task.

    Args:
        data: Path to data file or directory, OR built-in dataset name.
            Examples: "path/to/data.csv", "data/competitions/titanic",
            or a built-in task ID like "bike-sharing-demand".
        task: Optional task description that guides the agent on what
            to do with the data. If not provided, auto-detected for
            known benchmarks.
        target: Optional target variable column name for supervised
            learning tasks (e.g., "sales", "price", "label").
        registry_dir: Optional directory path containing benchmark metadata.
            This is used for grading competitions like MLE-Bench.

    Returns:
        TaskContext: A context object containing the loaded data, task
            description, and metadata for agent processing.

    Raises:
        ValueError: If the dataset cannot be found or is invalid.

    Example:
        >>> from dslighting import load_data
        >>> # Use built-in dataset
        >>> context = load_data("bike-sharing-demand")
        >>> # Load local data with task description
        >>> context = load_data("data.csv", task="Predict sales", target="sales")
    """
    import_path = data

    # Check if data is a built-in dataset/task name (not a file path)
    data_path = Path(data)
    if not data_path.is_file() and not data_path.is_dir():
        task_id = str(data)
        resolved_registry = _resolve_registry_root(task_id)
        resolved_path = _resolve_task_data_path(task_id)

        if resolved_path:
            import_path = resolved_path
            if registry_dir is None and resolved_registry:
                registry_dir = resolved_registry
            if task is None:
                task = _resolve_task_description(task_id, resolved_registry) or f"Analyze {task_id} dataset"
        elif resolved_registry:
            raise TaskError(
                f"Found benchmark metadata for '{task_id}', but no local dataset directory.\n"
                f"Expected one of:\n"
                f"  - data/competitions/{task_id}\n"
                f"  - {_PACKAGE_ROOT.parent / 'data' / 'competitions' / task_id}\n"
                f"  - {_PACKAGE_ROOT / 'datasets' / task_id}",
                error_code="TSK-003",
            )
        else:
            from dslighting.datasets import list_datasets

            available = list_datasets()
            raise TaskError(
                f"Dataset '{task_id}' not found.\n"
                f"Available built-in datasets: {', '.join(available)}\n"
                f"Or provide an explicit path to your data.",
                error_code="TSK-001",
            )

    # Respect DataLoader/task-detector semantics (including registry overrides).
    loader = DataLoader(import_path)
    loaded_data = loader.load()

    return loaded_data


def run_agent(
    task_id: Optional[str] = None,
    data: Optional[Union[str, Path, TaskContext]] = None,
    workflow: str = "aide",
    model: str = "gpt-4o",
    **kwargs
):
    """Run an agent - the simplest way to use DSLighting.

    This is the entry point function for running data science agents.
    It handles task resolution, data loading, and agent execution.

    Args:
        task_id: Optional predefined task ID for built-in benchmarks.
            Examples: "bike-sharing-demand", "titanic", "house-prices".
        data: Data path or TaskContext object. Can be a file path,
            directory path, or a pre-loaded TaskContext from load_data().
        workflow: Workflow name to use for the agent.
            Options: "aide" (default), "autokaggle", "data_interpreter",
            "deepanalyze", "dsagent", "automind", "aflow".
        model: LLM model identifier for the agent's reasoning.
            Examples: "gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet".
        **kwargs: Additional keyword arguments passed to the agent.
            For RAG workflows, pass namespaced parameters:
            `dsagent={"enable_rag": True, "case_dir": "./experience_replay"}`
            or `automind={"enable_rag": True, "case_dir": "./experience_replay"}`.

    Returns:
        AgentResult: An object containing the agent's execution results,
            including outputs, logs, and any generated artifacts.

    Raises:
        ValueError: If neither task_id nor data is provided, or if
            the requested task/dataset cannot be found.

    Example:
        >>> from dslighting import run_agent
        >>> # Run with built-in task
        >>> result = run_agent(task_id="bike-sharing-demand")
        >>> # Run with custom data
        >>> result = run_agent(data="path/to/data", workflow="autokaggle")
        >>> # Run RAG-enabled DSAgent
        >>> result = run_agent(
        ...     task_id="bike-sharing-demand",
        ...     workflow="dsagent",
        ...     dsagent={"enable_rag": True, "case_dir": "./experience_replay"},
        ... )
    """
    # Handle task_id
    if task_id:
        resolved_registry = _resolve_registry_root(task_id)
        if "registry_dir" not in kwargs and resolved_registry:
            kwargs["registry_dir"] = str(resolved_registry)

        if "task" not in kwargs:
            task_description = _resolve_task_description(task_id, resolved_registry)
            if task_description:
                kwargs["task"] = task_description

        if data is None:
            data = _resolve_task_data_path(task_id)

    if data is None:
        if task_id:
            raise TaskError(
                f"Task '{task_id}' was provided but no dataset directory was found.\n"
                f"Expected one of:\n"
                f"  - data/competitions/{task_id}\n"
                f"  - {_PACKAGE_ROOT.parent / 'data' / 'competitions' / task_id}\n"
                f"  - {_PACKAGE_ROOT / 'datasets' / task_id}\n"
                f"Or pass an explicit `data=` path.",
                error_code="TSK-004",
            )
        raise TaskError(
            "Either task_id or data must be provided",
            error_code="TSK-002",
        )

    # Create agent
    agent = Agent(workflow=workflow, model=model, **kwargs)

    # Run agent - pass task_id explicitly for benchmark initialization
    result = agent.run(data=data, task_id=task_id, **kwargs)

    return result


def analyze(
    data: Union[str, Path, TaskContext],
    description: str,
    model: str = "gpt-4o",
    **kwargs
):
    """Perform open-ended exploratory data analysis.

    This function provides a quick way to perform exploratory data analysis
    using the AIDE workflow. It is designed for beginners and quick prototyping.

    Args:
        data: Path to data or pre-loaded TaskContext object.
        description: User intent description in natural language.
            Examples: "Create visualizations for the data",
            "Summarize key statistics and patterns".
        model: LLM model identifier for analysis.
        **kwargs: Additional arguments passed to the Agent constructor.
            Common options: max_iterations, verbose, keep_workspace.

    Returns:
        AgentResult: An object containing analysis results including
            summaries, visualizations, and key findings.

    Example:
        >>> from dslighting import analyze
        >>> result = analyze(
        ...     data="sales_data.csv",
        ...     description="Create visualizations showing monthly trends"
        ... )
    """
    if "workflow" not in kwargs:
        kwargs["workflow"] = "aide"
    if "max_iterations" not in kwargs:
        kwargs["max_iterations"] = 2
    if "keep_workspace" not in kwargs:
        kwargs["keep_workspace"] = True
    agent = Agent(model=model, **kwargs)
    return agent.run(
        data=data,
        description=description,
        task_type="analysis",
        **kwargs
    )


def process(
    data: Union[str, Path, TaskContext],
    description: str,
    model: str = "gpt-4o",
    **kwargs
):
    """Perform data processing and transformation tasks.

    This function handles data cleaning, feature engineering, and other
    transformation tasks using the AIDE workflow.

    Args:
        data: Path to data or pre-loaded TaskContext object.
        description: User intent description for the processing task.
            Examples: "Handle missing values", "Create new features",
            "Normalize numerical columns".
        model: LLM model identifier for processing.
        **kwargs: Additional arguments passed to the Agent constructor.

    Returns:
        AgentResult: An object containing processing results including
            transformed data and processing metadata.

    Example:
        >>> from dslighting import process
        >>> result = process(
        ...     data="raw_data.csv",
        ...     description="Clean data and create time-based features"
        ... )
    """
    intent_description = f"User intent: data processing\n\n{description}"
    if "workflow" not in kwargs:
        kwargs["workflow"] = "aide"
    if "max_iterations" not in kwargs:
        kwargs["max_iterations"] = 3
    if "keep_workspace" not in kwargs:
        kwargs["keep_workspace"] = True
    agent = Agent(model=model, **kwargs)
    return agent.run(
        data=data,
        description=intent_description,
        task_type="processing",
        **kwargs
    )


def model(
    data: Union[str, Path, TaskContext],
    description: str,
    model: str = "gpt-4o",
    **kwargs
):
    """Build and train machine learning models.

    This function provides automated model building and training capabilities
    using the AIDE workflow. It handles feature preparation, model selection,
    hyperparameter tuning, and evaluation.

    Args:
        data: Path to data or pre-loaded TaskContext object.
        description: User intent description for modeling task.
            Examples: "Build a classification model to predict customer churn",
            "Train a regression model for price prediction".
        model: LLM model identifier for modeling.
        **kwargs: Additional arguments passed to the Agent constructor.
            Common options: max_iterations, verbose, keep_workspace.

    Returns:
        AgentResult: An object containing model results including trained
            model, predictions, and evaluation metrics.

    Example:
        >>> from dslighting import model
        >>> result = model(
        ...     data="customer_data.csv",
        ...     description="Build classification model to predict churn"
        ... )
    """
    intent_description = f"User intent: modeling\n\n{description}"
    if "workflow" not in kwargs:
        kwargs["workflow"] = "aide"
    if "max_iterations" not in kwargs:
        kwargs["max_iterations"] = 4
    if "keep_workspace" not in kwargs:
        kwargs["keep_workspace"] = True
    agent = Agent(model=model, **kwargs)
    return agent.run(
        data=data,
        description=intent_description,
        task_type="modeling",
        **kwargs
    )
