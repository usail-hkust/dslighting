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

__version__ = "1.3.14"
__author__ = "DSLighting Team"

# Core API classes
from dslighting.core.agent import Agent, AgentResult
from dslighting.core.data_loader import DataLoader, LoadedData

# Convenience functions
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


def run_agent(data=None, task_id=None, data_dir=None, keep_workspace=False, keep_workspace_on_failure=True, **kwargs):
    """
    Quick one-liner: load data and run with defaults.

    This function creates an Agent with the specified parameters and runs it on the data.

    Args:
        data: Optional data source (path, DataFrame, dict, etc.)
        task_id: Task/Competition identifier (e.g., "bike-sharing-demand")
        data_dir: Base data directory (default: "data/competitions")
        keep_workspace: Keep workspace after completion (default: False)
        keep_workspace_on_failure: Keep workspace on failure (default: True)
        **kwargs: Parameters passed to Agent.__init__ and Agent.run

    Returns:
        AgentResult with output, metrics, and metadata

    Examples:
        >>> # Recommended: using task_id
        >>> result = dslighting.run_agent(
        ...     task_id="bike-sharing-demand",
        ...     data_dir="data/competitions"
        ... )
        >>> print(f"Score: {result.score}, Cost: ${result.cost}")

        >>> # Legacy: using data path
        >>> result = dslighting.run_agent("data/titanic")

        >>> # With custom parameters
        >>> result = dslighting.run_agent(
        ...     task_id="bike-sharing-demand",
        ...     workflow="autokaggle",
        ...     model="gpt-4o",
        ...     keep_workspace=True  # Keep workspace for debugging
        ... )
    """
    # Extract run-specific parameters if present
    run_kwargs = {}
    agent_params = {}

    # Parameters that should go to run(), not __init__
    run_only_params = {'task_id', 'data_dir', 'output_path', 'description'}

    for key, value in kwargs.items():
        if key in run_only_params:
            run_kwargs[key] = value
        else:
            agent_params[key] = value

    # Add explicit parameters to run_kwargs
    if task_id is not None:
        run_kwargs['task_id'] = task_id
    if data_dir is not None:
        run_kwargs['data_dir'] = data_dir

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
    "load_data",
    "run_agent",
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
