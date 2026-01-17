"""
DSLighting: Simplified API for Data Science Agent Automation

A progressive API that provides sensible defaults with full control when needed.

Quick Start:
    >>> import dslighting
    >>>
    >>> # Simple usage
    >>> data = dslighting.load_data("path/to/data")
    >>> agent = dslighting.Agent()
    >>> result = agent.run(data)
    >>>
    >>> # One-liner
    >>> result = dslighting.run_agent("path/to/data")

Advanced Usage:
    >>> agent = dslighting.Agent(
    ...     workflow="autokaggle",
    ...     model="gpt-4o",
    ...     temperature=0.5,
    ...     max_iterations=10
    ... )
    >>> result = agent.run(data)

For more information, see: https://github.com/usail-hkust/dslighting
"""

__version__ = "1.8.3"
__author__ = "DSLighting Team"

# Core API classes
from dslighting.core.agent import Agent, AgentResult
from dslighting.core.data_loader import DataLoader, LoadedData

# Example datasets
from dslighting import datasets

# Convenience functions
def setup(data_parent_dir=None, registry_parent_dir=None):
    """
    Configure default parent directories for DSLighting.

    This function sets up global configuration for data and registry directories.
    Once configured, you can run agents using only task_id.

    Args:
        data_parent_dir: Parent directory containing competition data folders.
                        Example: "/path/to/data/competitions"
                        Each task should be in: data_parent_dir/task_name/
        registry_parent_dir: Parent directory containing registry folders.
                            Example: "/path/to/registry"
                            Each task config should be in: registry_parent_dir/task_name/

    Returns:
        GlobalConfig instance for further customization

    Examples:
        >>> # Configure once at the start of your script
        >>> import dslighting
        >>> dslighting.setup(
        ...     data_parent_dir="/path/to/data/competitions",
        ...     registry_parent_dir="/path/to/registry"
        ... )
        >>>
        >>> # Now run tasks with just task_id
        >>> agent = dslighting.Agent()
        >>> result = agent.run(task_id="bike-sharing-demand")
        >>>
        >>> # Or use the one-liner
        >>> result = dslighting.run_agent(task_id="bike-sharing-demand")

    Notes:
        - This configuration is global and thread-safe
        - Call this once at the start of your application
        - Use reset() to clear the configuration
    """
    from dslighting.core.global_config import get_global_config
    config = get_global_config()
    config.set_parent_dirs(
        data_parent_dir=data_parent_dir,
        registry_parent_dir=registry_parent_dir
    )
    return config


def load_data(source, **kwargs):
    """
    Load and auto-detect data type.

    This is a convenience function that creates a DataLoader and loads data.
    For Kaggle/MLE-Bench competitions, it automatically extracts task_id from the path.

    Args:
        source: Data source (path, DataFrame, dict, etc.)
        **kwargs: Additional parameters passed to DataLoader

    Returns:
        LoadedData with auto-detected task information and task_id

    Examples:
        >>> # Load from competition path (task_id auto-detected)
        >>> data = dslighting.load_data("data/competitions/bike-sharing-demand")
        >>> print(data.task_id)  # "bike-sharing-demand"
        >>>
        >>> agent = dslighting.Agent()
        >>> result = agent.run(data)  # Auto-graded using task_id

        >>> # Load DataFrame (no task_id)
        >>> df = pd.read_csv("data.csv")
        >>> data = dslighting.load_data(df)

        >>> data = dslighting.load_data("data/house-prices")
        >>> print(data.task_detection.task_type)
        'kaggle'
    """
    loader = DataLoader()
    return loader.load(source, **kwargs)


def run_agent(data=None, task_id=None, data_dir=None, registry_dir=None,
               keep_workspace=False, keep_workspace_on_failure=True, **kwargs):
    """
    Quick one-liner: load data and run with defaults.

    This function creates an Agent with the specified parameters and runs it on the data.

    Args:
        data: Optional data source (path, DataFrame, dict, or LoadedData)
        task_id: Task/Competition identifier (e.g., "bike-sharing-demand")
               For built-in datasets, just provide task_id without data_dir
        data_dir: Direct path to task data directory (must contain prepared/ folder).
                 Example: "/path/to/data/competitions/my-task"
                 If not provided, will use global config from setup().
        registry_dir: Direct path to task registry directory (must contain config.yaml).
                     Example: "/path/to/registry/my-task"
                     If not provided, will use global config from setup().
        keep_workspace: Keep workspace after completion (default: False)
        keep_workspace_on_failure: Keep workspace on failure (default: True)
        **kwargs: Parameters passed to Agent.__init__ and Agent.run

    Returns:
        AgentResult with output, metrics, and metadata

    Examples:
        >>> # Method 1: Using global setup (recommended)
        >>> import dslighting
        >>> dslighting.setup(
        ...     data_parent_dir="/path/to/data/competitions",
        ...     registry_parent_dir="/path/to/registry"
        ... )
        >>> result = dslighting.run_agent(task_id="bike-sharing-demand")

        >>> # Method 2: Built-in dataset (simplest)
        >>> result = dslighting.run_agent(task_id="bike-sharing-demand")

        >>> # Method 3: Direct paths (explicit)
        >>> result = dslighting.run_agent(
        ...     task_id="my-task",
        ...     data_dir="/path/to/data/competitions/my-task",
        ...     registry_dir="/path/to/registry/my-task"
        ... )

        >>> # Using LoadedData
        >>> data = dslighting.load_data("./datasets/bike-sharing-demand")
        >>> result = dslighting.run_agent(data)

        >>> # With custom parameters
        >>> result = dslighting.run_agent(
        ...     task_id="bike-sharing-demand",
        ...     workflow="autokaggle",
        ...     model="gpt-4o",
        ...     keep_workspace=True
        ... )
    """
    from pathlib import Path

    # Extract run-specific parameters if present
    run_kwargs = {}
    agent_params = {}

    # Parameters that should go to run(), not __init__
    run_only_params = {'task_id', 'data_dir', 'registry_dir', 'output_path', 'description'}

    for key, value in kwargs.items():
        if key in run_only_params:
            run_kwargs[key] = value
        else:
            agent_params[key] = value

    # Handle data loading
    if task_id and data is None:
        # Case 1: Built-in dataset with no data_dir specified
        if data_dir is None:
            # Check if it's a built-in dataset
            try:
                import dslighting.datasets
                load_func = getattr(dslighting.datasets, f'load_{task_id.replace("-", "_")}', None)
                if load_func:
                    # Use built-in dataset
                    loaded_info = load_func()
                    data = dslighting.load_data(loaded_info['data_dir'])
                    # task_id and data_dir will be extracted from LoadedData
                    run_kwargs.pop('task_id', None)
                    run_kwargs.pop('data_dir', None)
                    run_kwargs.pop('registry_dir', None)
            except (AttributeError, FileNotFoundError):
                pass

        # Case 2: data_dir is provided - verify it's a direct task directory
        if data is None and data_dir is not None:
            data_dir_path = Path(data_dir)
            if data_dir_path.exists():
                # Verify it points to a task directory (has prepared/public)
                if (data_dir_path / "prepared" / "public").exists():
                    # data_dir is the task directory - load it
                    data = dslighting.load_data(data_dir_path, registry_dir=registry_dir)
                    run_kwargs.pop('task_id', None)
                    run_kwargs.pop('data_dir', None)
                    run_kwargs.pop('registry_dir', None)
                # else: keep data_dir for Agent.run() to handle (will use with task_id)

    # Add explicit parameters to run_kwargs
    if task_id is not None:
        run_kwargs['task_id'] = task_id
    if data_dir is not None:
        run_kwargs['data_dir'] = data_dir
    if registry_dir is not None:
        run_kwargs['registry_dir'] = registry_dir

    # Add workspace preservation parameters to agent
    agent_params['keep_workspace'] = keep_workspace
    agent_params['keep_workspace_on_failure'] = keep_workspace_on_failure

    # Create agent and run
    agent = Agent(**agent_params)
    return agent.run(data, **run_kwargs)


# Public API
__all__ = [
    # Version info
    "__version__",
    "__author__",

    # Core classes
    "Agent",
    "AgentResult",
    "DataLoader",
    "LoadedData",

    # Convenience functions
    "setup",
    "load_data",
    "run_agent",

    # Example datasets
    "datasets",
]


# Import logging configuration
try:
    import logging
    from rich.logging import RichHandler

    # Set up rich logging if available
    logging.basicConfig(
        level="INFO",
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        handlers=[RichHandler(show_path=False)],
    )
except ImportError:
    # Fallback to basic logging
    logging.basicConfig(
        level="INFO",
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
