"""
DSLighting 2.0 - Data Science Agent Framework

A complete 5-layer architecture for building and running data science agents.

Architecture:
    🧠 agents/     - Strategy and orchestration center
    💪 operators/  - Atomic, reusable capability units
    ⚙️ services/   - Infrastructure support
    📝 state/      - Memory and context management
    🗣️ prompts/    - Prompt engineering components

Quick Start:
    >>> from dslighting import run_agent
    >>> result = run_agent(task_id="bike-sharing-demand")

Documentation: https://github.com/usail-hkust/dslighting
"""

__version__ = "2.4.1"
__author__ = "DSLighting Team"

# ============================================================================
# DSLighting 2.0 - User Layer (Top Level API)
# ============================================================================

from dslighting.api import Agent, AgentResult, DataLoader, TaskContext
from dslighting.api.convenience import run_agent, load_data, setup

# New unified API (recommended)
from dslighting.core.dataset import Dataset, load_dataset as load_dataset_new, DatasetInfo

# ============================================================================
# DSLighting 2.0 - DSAT Inheritance (推理模式)
# ============================================================================

# DSAT Types & Config
try:
    from dslighting.core.types import (
        TaskDefinition,
        TaskType,
        TaskMode,
        WorkflowCandidate,
        ReviewResult,
        Plan,
    )
    from dslighting.core.config import (
        LLMConfig,
        TaskConfig,
    )
except ImportError:
    pass

# ============================================================================
# DSLighting 2.0 - Training Integration (训练模式)
# ============================================================================

try:
    from dslighting.training import (
        LitDSAgent,
        RewardEvaluator,
        KaggleReward,
        ClassificationReward,
        RegressionReward,
        DatasetConverter,
        VerlConfigBuilder,
    )
except ImportError:
    pass

# ============================================================================
# DSLighting 2.0 - Five Layer Architecture
# ============================================================================

# 🧠 agents/ - Strategy and Orchestration Center
try:
    from dslighting.agents import BaseAgent  # DSATWorkflow alias
except ImportError:
    BaseAgent = None

# patterns 已弃用 - 所有功能通过 DSAT workflows 提供

try:
    from dslighting.agents.presets import (
        AIDE,                # AIDEWorkflow
        AutoKaggle,          # AutoKaggleWorkflow
        DataInterpreter,     # DataInterpreterWorkflow
        DeepAnalyze,         # DeepAnalyzeWorkflow
        DSAgent,             # DSAgentWorkflow
        AutoMind,            # AutoMindWorkflow
        AFlow,               # AFlowWorkflow
    )
except ImportError:
    AIDE = None
    AutoKaggle = None
    DataInterpreter = None
    DeepAnalyze = None
    DSAgent = None
    AutoMind = None
    AFlow = None

try:
    from dslighting.agents.strategies import (
        SearchStrategy,      # Base class for search strategies
        GreedyStrategy,      # Greedy search
        BeamSearchStrategy,  # Beam search
        MCTSStrategy,        # Monte Carlo Tree Search
        EvolutionaryStrategy, # Evolutionary algorithm
    )
except ImportError:
    SearchStrategy = None
    GreedyStrategy = None
    BeamSearchStrategy = None
    MCTSStrategy = None
    EvolutionaryStrategy = None

# 💪 operators/ - Atomic Capability Units
from dslighting.operators import (
    Operator,            # Base operator class
    GenerateCodeAndPlanOperator,  # LLM code generation
    PlanOperator,        # LLM planning
    ReviewOperator,      # LLM review
    SummarizeOperator,   # LLM summarization
    ExecuteAndTestOperator,  # Code execution
)

from dslighting.operators.orchestration import (
    Pipeline,            # Sequential orchestration
    Parallel,            # Parallel orchestration
    Conditional,         # Conditional orchestration
)

# ⚙️ services/ - Infrastructure Support
from dslighting.services import (
    LLMService,          # LLM invocation service
    SandboxService,      # Sandboxed code execution
    WorkspaceService,    # Workspace management
    DataAnalyzer,        # Data analysis service (optional)
    VDBService,          # Vector database service (optional)
)

# 📝 state/ - Memory and Context Management
from dslighting.state import (
    JournalState,        # Search tree state
    Node,                # Search tree node
    MetricValue,         # Comparable metric value
    Experience,          # Meta-optimization experience (optional)
    MemoryManager,       # Memory manager (optional)
    ContextManager,      # Context manager (optional)
)

# 🗣️ prompts/ - Prompt Engineering
from dslighting.prompts import (
    PromptBuilder,       # Fluent API for building prompts
    create_prompt_template,  # Create prompt from dict
    get_common_guidelines,   # Get common DS guidelines
    create_modeling_prompt,  # Create modeling prompt
    create_eda_prompt,       # Create EDA prompt
    create_debug_prompt,     # Create debugging prompt
)

# ============================================================================
# Legacy Support (v1.x - Backward Compatible)
# ============================================================================

# Legacy core API
try:
    from dslighting.core.agent import Agent as LegacyAgent
    from dslighting.core.data_loader import DataLoader as LegacyDataLoader
except ImportError:
    # Legacy components may not be available
    pass

# Example datasets
from dslighting import datasets

# ============================================================================
# Custom Workflow Support
# ============================================================================

try:
    from dslighting.workflows import BaseWorkflowFactory
except ImportError:
    BaseWorkflowFactory = None

try:
    from dslighting.tasks import MLETaskLoader
except ImportError:
    MLETaskLoader = None

# ============================================================================
# Help Functions
# ============================================================================

def help():
    """Show DSLighting 2.0 help and quick start guide."""
    print("=" * 70)
    print("DSLighting 2.0 - Data Science Agent Framework")
    print("=" * 70)
    print()
    print("🚀 Quick Start:")
    print("-" * 70)
    print("""
# Scenario 1: One-liner (simplest)
from dslighting import run_agent
result = run_agent(task_id="bike-sharing-demand")

# Scenario 2: Use Agent with preset workflow
from dslighting import Agent
agent = Agent(workflow="aide")
result = agent.run(data="path/to/data")

# Scenario 3: Custom agent with patterns
from dslighting import IterativeAgent, PromptBuilder

agent = IterativeAgent(operators, services, agent_config)
await agent.solve(description, io_instructions, data_dir, output_path)
""")

    print("\n📋 Available Workflows (from DSAT):")
    print("-" * 70)
    print("""
Manual Workflows:
  1. AIDE              - Adaptive Iteration & Debugging Enhancement
  2. AutoKaggle        - Advanced competition solver
  3. DataInterpreter   - Data analysis and exploration
  4. DeepAnalyze       - Analysis-focused workflow
  5. DSAgent           - Structured operator-based workflow

Search Workflows:
  6. AutoMind          - Planning + reasoning with knowledge base
  7. AFlow             - Meta-optimization workflow selector
""")

    print("\n🧱 Five Layer Architecture:")
    print("-" * 70)
    print("""
  1. 🧠 agents/     - BaseAgent, SimpleAgent, IterativeAgent, presets, strategies
  2. 💪 operators/  - LLM, code, data, orchestration (Pipeline, Parallel)
  3. ⚙️ services/   - LLMService, SandboxService, WorkspaceService
  4. 📝 state/      - JournalState, Experience, MemoryManager
  5. 🗣️ prompts/    - PromptBuilder, templates
""")

    print("\n📚 Documentation:")
    print("-" * 70)
    print("""
  GitHub:  https://github.com/usail-hkust/dslighting
  PyPI:    https://pypi.org/project/dslighting/
""")


def list_workflows():
    """List all available workflows."""
    print("=" * 70)
    print("DSLighting 2.0 Workflows (from DSAT)")
    print("=" * 70)
    print()

    workflows = [
        ("AIDE", "Adaptive Iteration & Debugging Enhancement",
         "Most data science tasks", "gpt-4o"),
        ("AutoKaggle", "Competition-solving agent",
         "Kaggle competitions, benchmarks", "gpt-4o"),
        ("DataInterpreter", "Data analysis and exploration",
         "Data exploration, EDA", "gpt-4o-mini"),
        ("DeepAnalyze", "Analysis-focused workflow",
         "Deep analysis tasks", "gpt-4o"),
        ("DSAgent", "Structured operator-based workflow",
         "Tasks with logging", "gpt-4o"),
        ("AutoMind", "Planning + reasoning with knowledge base",
         "Tasks requiring RAG", "gpt-4o"),
        ("AFlow", "Meta-optimization workflow selector",
         "Automated workflow selection", "gpt-4o"),
    ]

    for name, full_name, use_case, model in workflows:
        print(f"  {name}")
        print(f"    Full Name: {full_name}")
        print(f"    Use Case: {use_case}")
        print(f"    Default Model: {model}")
        print()


def show_example(workflow_name: str):
    """Show workflow example code."""
    examples = {
        "aide": """
from dslighting import Agent

agent = Agent(workflow="aide", model="gpt-4o")
result = agent.run(data="path/to/data")
print(f"Success: {result.success}")
""",
        "autokaggle": """
from dslighting import Agent

agent = Agent(workflow="autokaggle", model="gpt-4o")
result = agent.run(data="path/to/data")
print(f"Success: {result.success}")
""",
        "data_interpreter": """
from dslighting import Agent

agent = Agent(workflow="data_interpreter", model="gpt-4o")
result = agent.run(data="path/to/data")
print(f"Success: {result.success}")
""",
    }

    if workflow_name.lower() in examples:
        print(examples[workflow_name.lower()])
    else:
        print(f"Unknown workflow: {workflow_name}")
        print(f"Available: {', '.join(examples.keys())}")


# ============================================================================
# Public API
# ============================================================================

__all__ = [
    # Version info
    "__version__",
    "__author__",

    # ========== User Layer (Top Level) ==========
    "Agent",
    "AgentResult",
    "DataLoader",
    "TaskContext",
    "run_agent",
    "load_data",
    "setup",

    # ========== DSAT Inheritance (推理模式) ==========
    "TaskDefinition",
    "TaskType",
    "TaskMode",
    "WorkflowCandidate",
    "ReviewResult",
    "Plan",
    "LLMConfig",
    "TaskConfig",
    "BaseAgent",

    # ========== Training Integration (训练模式) ==========
    "LitDSAgent",
    "RewardEvaluator",
    "KaggleReward",
    "ClassificationReward",
    "RegressionReward",
    "DatasetConverter",
    "VerlConfigBuilder",

    # ========== agents/ - Strategy Center ==========
    "BaseAgent",
    # DSAT 预设 workflows
    "AIDE",
    "AutoKaggle",
    "DataInterpreter",
    "DeepAnalyze",
    "DSAgent",
    "AutoMind",
    "AFlow",
    # 搜索策略
    "SearchStrategy",
    "GreedyStrategy",
    "BeamSearchStrategy",
    "MCTSStrategy",
    "EvolutionaryStrategy",

    # ========== operators/ - Atomic Capabilities ==========
    "Operator",
    "GenerateCodeAndPlanOperator",
    "PlanOperator",
    "ReviewOperator",
    "SummarizeOperator",
    "ExecuteAndTestOperator",
    "Pipeline",
    "Parallel",
    "Conditional",

    # ========== services/ - Infrastructure ==========
    "LLMService",
    "SandboxService",
    "WorkspaceService",
    "DataAnalyzer",
    "VDBService",

    # ========== state/ - Memory Management ==========
    "JournalState",
    "Node",
    "MetricValue",
    "Experience",
    "MemoryManager",
    "ContextManager",

    # ========== prompts/ - Prompt Engineering ==========
    "PromptBuilder",
    "create_prompt_template",
    "get_common_guidelines",
    "create_modeling_prompt",
    "create_eda_prompt",
    "create_debug_prompt",

    # ========== Help Functions ==========
    "help",
    "list_workflows",
    "show_example",

    # ========== Custom Workflow Support ==========
    "BaseWorkflowFactory",
    "MLETaskLoader",

    # ========== Legacy ==========
    "datasets",
]


# ============================================================================
# Logging Configuration
# ============================================================================

try:
    import logging
    from rich.logging import RichHandler

    logging.basicConfig(
        level="INFO",
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        handlers=[RichHandler(show_path=False)],
    )
except ImportError:
    logging.basicConfig(
        level="INFO",
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


# ============================================================================
# Discovery Functions - Help users discover available components
# ============================================================================

def list_prompts(category: str = "all") -> dict[str, list[str]]:
    """
    List all available prompt functions by category.

    This is a convenience wrapper around dslighting.prompts.list_available_prompts

    Args:
        category: Filter by category ('all', 'aide', 'autokaggle', 'automind',
                  'aflow', 'data_interpreter', 'dsagent', 'native')
                  Default: 'all'

    Returns:
        Dictionary mapping category names to lists of prompt functions

    Example:
        >>> import dslighting
        >>> prompts = dslighting.list_prompts()
        >>> for cat, funcs in prompts.items():
        ...     print(f"{cat}: {len(funcs)} prompts")
    """
    try:
        from dslighting.prompts import list_available_prompts
        return list_available_prompts(category)
    except ImportError:
        return {}


def list_operators(category: str = "all") -> dict[str, list[str]]:
    """
    List all available operators by category.

    This is a convenience wrapper around dslighting.operators.list_available_operators

    Args:
        category: Filter by category ('all', 'llm', 'code', 'data', 'orchestration', 'custom')
                  Default: 'all'

    Returns:
        Dictionary mapping category names to lists of operator names

    Example:
        >>> import dslighting
        >>> ops = dslighting.list_operators()
        >>> for cat, names in ops.items():
        ...     print(f"{cat}: {len(names)} operators")
    """
    try:
        from dslighting.operators import list_available_operators
        return list_available_operators(category)
    except ImportError:
        return {}


def explore():
    """
    Interactive exploration of DSLighting components.

    Shows all available prompts, operators, and workflows with descriptions.

    Example:
        >>> import dslighting
        >>> dslighting.explore()
    """
    print("=" * 80)
    print("DSLighting 2.0 - Component Explorer")
    print("=" * 80)
    print()

    # Prompts
    print("\n🗣️  Available Prompts")
    print("-" * 80)
    prompts = list_prompts()
    for category, functions in prompts.items():
        if functions:
            print(f"\n{category.upper()} ({len(functions)} items):")
            for func in functions[:5]:  # Show first 5
                print(f"  - {func}")
            if len(functions) > 5:
                print(f"  ... and {len(functions) - 5} more")

    # Operators
    print("\n\n💪 Available Operators")
    print("-" * 80)
    operators = list_operators()
    for category, names in operators.items():
        if names:
            print(f"\n{category.upper()} ({len(names)} items):")
            for name in names[:5]:  # Show first 5
                print(f"  - {name}")
            if len(names) > 5:
                print(f"  ... and {len(names) - 5} more")

    # Workflows
    print("\n\n🚀 Available Workflows")
    print("-" * 80)
    print("""
  AIDE              - Adaptive Iteration & Debugging Enhancement
  AutoKaggle        - Competition-solving agent
  DataInterpreter   - Data analysis and exploration
  DeepAnalyze       - Analysis-focused workflow
  DSAgent           - Structured operator-based workflow
  AutoMind          - Planning + reasoning with knowledge base
  AFlow             - Meta-optimization workflow selector
    """)

    print("\n" + "=" * 80)
    print("For more information:")
    print("  - dslighting.help()              - Show quick start guide")
    print("  - dslighting.list_workflows()    - List all workflows")
    print("  - dslighting.list_prompts()      - List all prompts")
    print("  - dslighting.list_operators()    - List all operators")
    print("=" * 80)


# Add discovery functions to __all__
__all__.extend([
    "list_prompts",
    "list_operators",
    "explore",
])
