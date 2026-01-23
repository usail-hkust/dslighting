"""
Convenience Functions - Top-Level User API

Simple functions for common tasks.
"""

from pathlib import Path
from typing import Union, Optional
from .agent import Agent
from ..core.data_loader import DataLoader, TaskContext


def setup(
    model: str = "gpt-4o",
    api_key: Optional[str] = None,
):
    """
    Setup DSLighting configuration.

    Args:
        model: Default LLM model to use
        api_key: Optional API key (or set OPENAI_API_KEY env variable)

    Example:
        from dslighting import setup

        setup(model="gpt-4o")
    """
    import os

    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

    # You could store configuration globally here if needed
    print(f"✓ DSLighting configured with model: {model}")


def load_data(
    data: Union[str, Path],
    task: Optional[str] = None,
    target: Optional[str] = None,
    registry_dir: Union[str, Path, None] = None,
) -> TaskContext:
    """
    Load data for agent processing.

    Args:
        data: Path to data file or directory, OR built-in dataset name (e.g., "bike-sharing-demand")
        task: Optional task description
        target: Optional target variable name
        registry_dir: Optional registry directory path (for grading). Example: "registry/titanic"

    Returns:
        TaskContext object (Agent's view of the task, NOT just data)

    Examples:
        from dslighting import load_data

        # Way 1: Use built-in dataset name
        context = load_data("bike-sharing-demand")

        # Way 2: Use explicit path
        data = load_data("path/to/data", task="Predict bike sharing demand")

        # Way 3: Explicit data and registry paths (for custom projects)
        data = load_data(
            "data/competitions/titanic",
            registry_dir="registry/titanic"
        )
    """
    import_path = data

    # Check if data is a built-in dataset name (not a file path)
    data_path = Path(data)
    if not data_path.is_file() and not data_path.is_dir():
        # Try to load from registry
        resolved_path = None
        try:
            from ..registry import load_task_config
            config = load_task_config(str(data))
            resolved_path = config.get("data_path")
            if resolved_path:
                import_path = resolved_path
                if task is None:
                    task = config.get("task_description")
        except Exception:
            pass  # Registry lookup failed, will try datasets directory below

        # If registry didn't resolve the path, try built-in datasets directory
        if not resolved_path or not Path(resolved_path).exists():
            dataset_path = Path(__file__).parent.parent / "datasets" / str(data)
            if dataset_path.exists():
                import_path = dataset_path
                # If task still not set, provide a default description
                if task is None:
                    task = f"Analyze {data} dataset"
            else:
                # Dataset not found - provide helpful error message
                from ..datasets import list_datasets
                available = list_datasets()
                raise ValueError(
                    f"Dataset '{data}' not found.\n"
                    f"Available built-in datasets: {', '.join(available)}\n"
                    f"Or provide an explicit path to your data."
                )

    # Always treat loaded data as kaggle/competition type for benchmark grading
    loader = DataLoader()
    loaded_data = loader.load(import_path, task=task, target=target, registry_dir=registry_dir)

    # Override task_type to ensure benchmark grading works
    if loaded_data.task_detection and loaded_data.task_detection.task_type != "kaggle":
        from dslighting.core.task_detector import TaskDetection
        original_detection = loaded_data.task_detection
        loaded_data.task_detection = TaskDetection(
            task_type="kaggle",  # Force kaggle type for benchmark grading
            task_mode=original_detection.task_mode,
            data_dir=original_detection.data_dir,
            description=original_detection.description,
            recommended_workflow=original_detection.recommended_workflow,
            confidence=1.0,
        )

    return loaded_data


def run_agent(
    task_id: Optional[str] = None,
    data: Optional[Union[str, Path, TaskContext]] = None,
    workflow: str = "aide",
    model: str = "gpt-4o",
    **kwargs
):
    """
    Run an agent - simplest way to use DSLighting.

    Args:
        task_id: Optional predefined task ID (e.g., "bike-sharing-demand")
        data: Data path or TaskContext object
        workflow: Workflow to use ("aide", "autokaggle", "data_interpreter")
        model: LLM model
        **kwargs: Additional arguments

    Returns:
        AgentResult object

    Examples:
        from dslighting import run_agent

        # Way 1: Use task_id
        result = run_agent(task_id="bike-sharing-demand")

        # Way 2: Provide data directly
        result = run_agent(data="path/to/data")

        # Way 3: With custom workflow
        result = run_agent(data="path/to/data", workflow="autokaggle")
    """
    # Handle task_id
    if task_id:
        # Try to load from registry
        try:
            from ..registry import load_task_config
            config = load_task_config(task_id)
            data_path = config.get("data_path")
            if data is None:
                data = data_path
            if "task" not in kwargs:
                kwargs["task"] = config.get("task_description")
        except Exception:
            # If registry fails, try datasets directory
            dataset_path = Path(__file__).parent.parent / "datasets" / task_id
            if dataset_path.exists():
                if data is None:
                    data = dataset_path

    if data is None:
        raise ValueError("Either task_id or data must be provided")

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
    """
    Open-ended analysis helper for beginners.

    This runs the open-ended flow (analysis subtype) and returns a summary preview.

    Args:
        data: Data path or TaskContext object
        description: User intent (e.g., "想做可视化")
        model: LLM model
        **kwargs: Additional Agent args

    Returns:
        AgentResult object with summary preview
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
    """
    Open-ended data processing helper (open-ended subtype: processing).
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
    """
    Open-ended modeling helper (open-ended subtype: modeling).
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
