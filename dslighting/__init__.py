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

__version__ = "1.0.1"
__author__ = "DSLighting Team"

# Core API classes
from dslighting.core.agent import Agent, AgentResult
from dslighting.core.data_loader import DataLoader, LoadedData

# Convenience functions
def load_data(source, **kwargs):
    """
    Load and auto-detect data type.

    This is a convenience function that creates a DataLoader and loads data.

    Args:
        source: Data source (path, DataFrame, dict, etc.)
        **kwargs: Additional parameters passed to DataLoader

    Returns:
        LoadedData with auto-detected task information

    Examples:
        >>> data = dslighting.load_data("data/titanic")
        >>> agent = dslighting.Agent()
        >>> result = agent.run(data)

        >>> data = dslighting.load_data("data/house-prices")
        >>> print(data.task_detection.task_type)
        'kaggle'
    """
    loader = DataLoader()
    return loader.load(source, **kwargs)


def run_agent(data, **kwargs):
    """
    Quick one-liner: load data and run with defaults.

    This function creates an Agent with the specified parameters and runs it on the data.

    Args:
        data: Data source (path, DataFrame, dict, etc.)
        **kwargs: Parameters passed to Agent.__init__ and Agent.run

    Returns:
        AgentResult with output, metrics, and metadata

    Examples:
        >>> # Simplest usage - all defaults
        >>> result = dslighting.run_agent("data/titanic")
        >>> print(f"Score: {result.score}, Cost: ${result.cost}")

        >>> # With custom parameters
        >>> result = dslighting.run_agent(
        ...     "data/titanic",
        ...     workflow="autokaggle",
        ...     model="gpt-4o"
        ... )
    """
    # Extract run-specific parameters if present
    run_kwargs = {}
    agent_params = {}

    # Parameters that should go to run(), not __init__
    run_only_params = {'task_id', 'output_path', 'description'}

    for key, value in kwargs.items():
        if key in run_only_params:
            run_kwargs[key] = value
        else:
            agent_params[key] = value

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
