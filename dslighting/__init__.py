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

__version__ = "1.9.8"
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

    # Help functions
    "help",
    "list_workflows",
    "show_example",

    # Example datasets
    "datasets",
]


# ============================================================================
# Help Functions
# ============================================================================

def help():
    """
    Show DSLighting help and quick start guide.

    This is the main help function for DSLighting. It displays:
    - Quick start guide
    - Available workflows
    - Useful commands
    - Documentation links

    Examples:
        >>> import dslighting
        >>> dslighting.help()
    """
    print("=" * 70)
    print("DSLighting - Data Science Agent Framework")
    print("=" * 70)
    print()
    print("🚀 Quick Start:")
    print("-" * 70)
    print("""
from dotenv import load_dotenv
load_dotenv()

import dslighting

# Method 1: Use built-in dataset
data = dslighting.load_data("bike-sharing-demand")
agent = dslighting.Agent(workflow="aide")
result = agent.run(data)

# Method 2: Quick one-liner
result = dslighting.run_agent(task_id="bike-sharing-demand")
""")

    print("📋 Available Workflows:")
    print("-" * 70)
    print("""
  1. aide              - Adaptive Iteration & Debugging (Default)
  2. autokaggle        - Advanced competition solver
  3. data_interpreter  - Interactive data analysis
  4. automind          - Complex planning with knowledge base
  5. dsagent           - Long-term planning with logging
  6. deepanalyze       - Deep analysis with structured tags
""")

    print("💡 Python Help Functions:")
    print("-" * 70)
    print("""
  dslighting.list_workflows()         - List all workflows with details
  dslighting.show_example("aide")      - Show workflow example code
""")

    print("🖥️  CLI Commands:")
    print("-" * 70)
    print("""
  dslighting help                      - Show this help
  dslighting workflows                  - Show all workflows
  dslighting example <workflow>         - Show workflow example
  dslighting quickstart                 - Show quick start guide
  dslighting detect-packages            - Detect Python packages
""")

    print("📚 Documentation:")
    print("-" * 70)
    print("""
  Online:  https://luckyfan-cs.github.io/dslighting-web/
  GitHub:  https://github.com/usail-hkust/dslighting
  PyPI:    https://pypi.org/project/dslighting/
""")


def list_workflows():
    """
    List all available workflows with detailed information.

    Shows workflow name, description, use cases, default parameters,
    and unique parameters for each workflow.

    Returns:
        None (prints to console)

    Examples:
        >>> import dslighting
        >>> dslighting.list_workflows()
    """
    workflows = [
        {
            "name": "aide",
            "full_name": "AIDE (Adaptive Iteration & Debugging Enhancement)",
            "description": "Self-improving code with iterative debugging",
            "use_cases": ["Kaggle competitions (simple)", "Data analysis", "Quick prototyping"],
            "default_model": "gpt-4o",
            "parameters": {"max_iterations": 10, "temperature": 0.7},
            "unique_params": None
        },
        {
            "name": "autokaggle",
            "full_name": "AutoKaggle",
            "description": "Advanced competition solver with dynamic phase planning",
            "use_cases": ["Kaggle competitions (complex)", "High-stakes competitions", "Multi-phase problems"],
            "default_model": "gpt-4o",
            "parameters": {"temperature": 0.5},
            "unique_params": {
                "max_attempts_per_phase": "Max retries per phase (default: 5)",
                "success_threshold": "Score threshold 1-5 (default: 3.0)"
            }
        },
        {
            "name": "data_interpreter",
            "full_name": "DataInterpreter",
            "description": "Interactive data analysis and exploration",
            "use_cases": ["Data exploration", "Visualization", "Quick analysis"],
            "default_model": "gpt-4o-mini",
            "parameters": {"max_iterations": 5, "temperature": 0.7},
            "unique_params": None
        },
        {
            "name": "automind",
            "full_name": "AutoMind",
            "description": "Complex planning with knowledge base and experience replay",
            "use_cases": ["Complex tasks", "Multi-step problems", "Need historical context"],
            "default_model": "gpt-4o",
            "parameters": {"max_iterations": 10, "temperature": 0.5},
            "unique_params": {
                "case_dir": "Experience replay directory (e.g., ./experience_replay)",
                "enable_rag": "Enable RAG/knowledge base (default: True). Set to False to disable HuggingFace downloads"
            }
        },
        {
            "name": "dsagent",
            "full_name": "DS-Agent",
            "description": "Long-term planning with Plan-Execute-Log loop",
            "use_cases": ["Long-running tasks", "Need detailed logging", "Step-by-step refinement"],
            "default_model": "gpt-4o",
            "parameters": {"max_iterations": 15, "temperature": 0.6},
            "unique_params": {
                "case_dir": "Experience replay directory (e.g., ./experience_replay)",
                "enable_rag": "Enable RAG/knowledge base (default: True). Set to False to disable HuggingFace downloads"
            }
        },
        {
            "name": "deepanalyze",
            "full_name": "DeepAnalyze",
            "description": "Deep analysis with structured thinking tags",
            "use_cases": ["Deep data analysis", "Complex reasoning", "Structured outputs"],
            "default_model": "gpt-4o",
            "parameters": {"max_iterations": 10, "temperature": 0.8},
            "unique_params": None
        }
    ]

    print("=" * 70)
    print("DSLighting Workflows")
    print("=" * 70)
    print()

    for idx, wf in enumerate(workflows, 1):
        print(f"{idx}. {wf['name'].upper()}")
        print(f"   Full Name: {wf['full_name']}")
        print(f"   Description: {wf['description']}")
        print(f"   Use Cases: {', '.join(wf['use_cases'])}")
        print(f"   Default Model: {wf['default_model']}")

        if wf['unique_params']:
            print(f"   Unique Parameters:")
            for param, desc in wf['unique_params'].items():
                print(f"     - {param}: {desc}")
        else:
            print(f"   Unique Parameters: None (uses common params only)")

        print()

    print("💡 Use dslighting.show_example('workflow_name') to see example code")


def show_example(workflow_name: str):
    """
    Show workflow example code.

    Args:
        workflow_name: Name of the workflow (e.g., "aide", "autokaggle")

    Returns:
        None (prints to console)

    Examples:
        >>> import dslighting
        >>> dslighting.show_example("aide")
        >>> dslighting.show_example("autokaggle")
    """
    workflow_name = workflow_name.lower()

    examples = {
        "aide": """
from dotenv import load_dotenv
load_dotenv()

import dslighting

data = dslighting.load_data("bike-sharing-demand")

agent = dslighting.Agent(
    workflow="aide",
    model="gpt-4o",
    temperature=0.7,
    max_iterations=10,
)

result = agent.run(data)

print(f"Score: {result.score}")
print(f"Cost: ${result.cost:.2f}")
""",
        "autokaggle": """
from dotenv import load_dotenv
load_dotenv()

import dslighting

data = dslighting.load_data("bike-sharing-demand")

agent = dslighting.Agent(
    workflow="autokaggle",
    model="gpt-4o",
    temperature=0.5,

    autokaggle={
        "max_attempts_per_phase": 5,
        "success_threshold": 3.5
    }
)

result = agent.run(data)

print(f"Score: {result.score}")
print(f"Duration: {result.duration:.1f}s")
print(f"Cost: ${result.cost:.2f}")
""",
        "data_interpreter": """
from dotenv import load_dotenv
load_dotenv()

import dslighting

data = dslighting.load_data("sales_data.csv")

agent = dslighting.Agent(
    workflow="data_interpreter",
    model="gpt-4o-mini",
    temperature=0.7,
    max_iterations=5,
)

result = agent.run(data, description="分析销售趋势")

print(f"Output: {result.output}")
print(f"Cost: ${result.cost:.2f}")
""",
        "automind": """
from dotenv import load_dotenv
load_dotenv()

import dslighting

data = dslighting.load_data("bike-sharing-demand")

agent = dslighting.Agent(
    workflow="automind",
    model="gpt-4o",
    temperature=0.5,
    max_iterations=10,

    automind={
        "case_dir": "./experience_replay",
        "enable_rag": True  # Set False to disable HuggingFace downloads
    }
)

result = agent.run(data)

print(f"Score: {result.score}")
print(f"Output: {result.output}")
print(f"Cost: ${result.cost:.2f}")
""",
        "dsagent": """
from dotenv import load_dotenv
load_dotenv()

import dslighting

data = dslighting.load_data("bike-sharing-demand")

agent = dslighting.Agent(
    workflow="dsagent",
    model="gpt-4o",
    temperature=0.6,
    max_iterations=15,

    dsagent={
        "case_dir": "./experience_replay",
        "enable_rag": True  # Set False to disable HuggingFace downloads
    }
)

result = agent.run(data)

print(f"Score: {result.score}")
print(f"Output: {result.output}")
print(f"Cost: ${result.cost:.2f}")
""",
        "deepanalyze": """
from dotenv import load_dotenv
load_dotenv()

import dslighting

data = dslighting.load_data("your_data.csv")

agent = dslighting.Agent(
    workflow="deepanalyze",
    model="gpt-4o",
    temperature=0.8,
    max_iterations=10,
)

result = agent.run(data, description="深度分析数据")

print(f"Output: {result.output}")
print(f"Cost: ${result.cost:.2f}")
"""
    }

    if workflow_name not in examples:
        print(f"❌ Unknown workflow: {workflow_name}")
        print(f"\nAvailable workflows: {', '.join(examples.keys())}")
        print(f"\nUse dslighting.list_workflows() to see all workflows")
        return

    print("=" * 70)
    print(f"Example: {workflow_name.upper()}")
    print("=" * 70)
    print(examples[workflow_name])
    print("=" * 70)
    print(f"💡 Copy this code and run it!")
    print(f"💡 Use dslighting.list_workflows() for more workflow details")


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
