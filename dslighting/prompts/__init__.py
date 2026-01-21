"""
DSLighting 2.0 - Prompts Layer

This layer provides prompt engineering components:

DSLighting Native:
- PromptBuilder: Fluent API for building prompts
- StructuredPromptBuilder: Dict-based prompt builder (推荐)
- Template functions: Standard prompt templates
- Guidelines: Common prompt guidelines

DSAT Workflows (Re-exported):
- AIDE: Iterative code generation with review
- AutoKaggle: Multi-phase competition solver
- AutoMind: Planning + reasoning with RAG
- AFlow: Meta-optimization workflow
- DataInterpreter: Fast code execution in Jupyter
- DSAgent: Structured operator-based workflow
"""

# ============================================================================
# DSLighting Native Components
# ============================================================================

from .builder import PromptBuilder
from .structured_builder import (
    StructuredPromptBuilder,
    PromptTemplate,
    truncate_output,
    format_code_block,
    create_structured_prompt,
)
from .base import (
    create_prompt_template,
    get_common_guidelines,
)

# Re-export template functions
try:
    from .templates import (
        create_modeling_prompt,
        create_eda_prompt,
        create_debug_prompt as create_dslighting_debug_prompt,
    )
    _has_templates = True
except ImportError:
    _has_templates = False

# ============================================================================
# DSAT Workflow Prompts (Re-exported)
# ============================================================================

# AIDE Workflow
try:
    from .aide_prompt import (
        create_improve_prompt,
        create_debug_prompt,
    )
    _has_aide = True
except ImportError:
    _has_aide = False

# AutoKaggle Workflow
try:
    from .autokaggle_prompt import (
        get_deconstructor_prompt,
        get_phase_planner_prompt,
        get_step_planner_prompt,
        get_developer_prompt,
        get_validator_prompt,
        get_reviewer_prompt,
        get_summarizer_prompt,
    )
    _has_autokaggle = True
except ImportError:
    _has_autokaggle = False

# AutoMind Workflow
try:
    from .automind_prompt import (
        create_stepwise_code_prompt,
        create_stepwise_debug_prompt,
    )
    _has_automind = True
except ImportError:
    _has_automind = False

# AFlow Workflow
try:
    from .aflow_prompt import (
        get_operator_description,
        get_graph_optimize_prompt,
        GraphOptimize,
    )
    _has_aflow = True
except ImportError:
    _has_aflow = False

# Data Interpreter Workflow
try:
    from .data_interpreter_prompt import (
        PLAN_SYSTEM_MESSAGE,
        PLAN_PROMPT,
        GENERATE_CODE_PROMPT,
        REFLECT_AND_DEBUG_PROMPT,
        FINALIZE_OUTPUT_PROMPT,
    )
    _has_data_interpreter = True
except ImportError:
    _has_data_interpreter = False

# DSAgent Workflow
try:
    from .dsagent_prompt import (
        PLAN_PROMPT_TEMPLATE,
        PROGRAMMER_PROMPT_TEMPLATE,
        DEBUGGER_PROMPT_TEMPLATE,
        LOGGER_PROMPT_TEMPLATE,
    )
    _has_dsagent = True
except ImportError:
    _has_dsagent = False

# Common Utilities
try:
    from .common import (
        _dict_to_str,
        _get_common_guidelines,
        create_draft_prompt,
    )
    _has_common = True
except ImportError:
    _has_common = False

# ============================================================================
# Export List
# ============================================================================

__all__ = [
    # DSLighting Native - Fluent API
    "PromptBuilder",

    # DSLighting Native - Structured API (推荐)
    "StructuredPromptBuilder",
    "PromptTemplate",
    "truncate_output",
    "format_code_block",
    "create_structured_prompt",

    # DSLighting Native - Base functions
    "create_prompt_template",
    "get_common_guidelines",
]

# Add DSLighting templates if available
if _has_templates:
    __all__.extend([
        "create_modeling_prompt",
        "create_eda_prompt",
        "create_dslighting_debug_prompt",
    ])

# Add AIDE workflow prompts
if _has_aide:
    __all__.extend([
        "create_improve_prompt",
        "create_debug_prompt",  # AIDE debug prompt (overrides dslighting template)
    ])

# Add AutoKaggle workflow prompts
if _has_autokaggle:
    __all__.extend([
        "get_deconstructor_prompt",
        "get_phase_planner_prompt",
        "get_step_planner_prompt",
        "get_developer_prompt",
        "get_validator_prompt",
        "get_reviewer_prompt",
        "get_summarizer_prompt",
    ])

# Add AutoMind workflow prompts
if _has_automind:
    __all__.extend([
        "create_stepwise_code_prompt",
        "create_stepwise_debug_prompt",
    ])

# Add AFlow workflow prompts
if _has_aflow:
    __all__.extend([
        "get_operator_description",
        "get_graph_optimize_prompt",
        "GraphOptimize",
    ])

# Add Data Interpreter workflow prompts
if _has_data_interpreter:
    __all__.extend([
        "PLAN_SYSTEM_MESSAGE",
        "PLAN_PROMPT",
        "GENERATE_CODE_PROMPT",
        "REFLECT_AND_DEBUG_PROMPT",
        "FINALIZE_OUTPUT_PROMPT",
    ])

# Add DSAgent workflow prompts
if _has_dsagent:
    __all__.extend([
        "PLAN_PROMPT_TEMPLATE",
        "PROGRAMMER_PROMPT_TEMPLATE",
        "DEBUGGER_PROMPT_TEMPLATE",
        "LOGGER_PROMPT_TEMPLATE",
    ])

# Add common utilities
if _has_common:
    __all__.extend([
        "_dict_to_str",
        "_get_common_guidelines",
        "create_draft_prompt",
    ])

# ============================================================================
# Discovery Functions - Help users discover available prompts
# ============================================================================

def list_available_prompts(category: str = "all") -> dict[str, list[str]]:
    """
    List all available prompt functions by category.

    Args:
        category: Filter by category ('all', 'aide', 'autokaggle', 'automind',
                  'aflow', 'data_interpreter', 'dsagent', 'native')
                  Default: 'all'

    Returns:
        Dictionary mapping category names to lists of prompt functions

    Example:
        >>> from dslighting.prompts import list_available_prompts
        >>> prompts = list_available_prompts()
        >>> for category, functions in prompts.items():
        ...     print(f"{category}: {len(functions)} prompts")
    """
    categories = {
        "native": [
            "PromptBuilder",
            "StructuredPromptBuilder",
            "PromptTemplate",
            "create_modeling_prompt",
            "create_eda_prompt",
            "create_structured_prompt",
            "create_prompt_template",
            "get_common_guidelines",
        ],
        "aide": [
            "create_improve_prompt",
            "create_debug_prompt",
        ],
        "autokaggle": [
            "get_deconstructor_prompt",
            "get_phase_planner_prompt",
            "get_step_planner_prompt",
            "get_developer_prompt",
            "get_validator_prompt",
            "get_reviewer_prompt",
            "get_summarizer_prompt",
        ],
        "automind": [
            "create_stepwise_code_prompt",
            "create_stepwise_debug_prompt",
        ],
        "aflow": [
            "get_operator_description",
            "get_graph_optimize_prompt",
            "GraphOptimize",
        ],
        "data_interpreter": [
            "PLAN_SYSTEM_MESSAGE",
            "PLAN_PROMPT",
            "GENERATE_CODE_PROMPT",
            "REFLECT_AND_DEBUG_PROMPT",
            "FINALIZE_OUTPUT_PROMPT",
        ],
        "dsagent": [
            "PLAN_PROMPT_TEMPLATE",
            "PROGRAMMER_PROMPT_TEMPLATE",
            "DEBUGGER_PROMPT_TEMPLATE",
            "LOGGER_PROMPT_TEMPLATE",
        ],
        "common": [
            "create_draft_prompt",
        ],
    }

    if category == "all":
        return categories
    elif category in categories:
        return {category: categories[category]}
    else:
        return {}


def get_prompt_info(prompt_name: str) -> dict[str, any]:
    """
    Get detailed information about a specific prompt function.

    Args:
        prompt_name: Name of the prompt function

    Returns:
        Dictionary with 'name', 'category', 'description', 'inputs', 'outputs',
        'output_format', 'example' keys

    Example:
        >>> from dslighting.prompts import get_prompt_info
        >>> info = get_prompt_info("create_improve_prompt")
        >>> print(f"Inputs: {info['inputs']}")
        >>> print(f"Returns: {info['output_format']}")
    """
    import inspect

    prompts_info = {
        # AIDE
        "create_improve_prompt": {
            "category": "aide",
            "description": "Create improvement prompt for AIDE workflow iteration",
            "workflow": "AIDE - Iterative code generation with review",
            "inputs": [
                {
                    "name": "task_context",
                    "type": "Dict[str, Any]",
                    "description": "Task context containing goal and I/O requirements",
                    "required": True,
                    "fields": {
                        "goal_and_data": "str - Task goal and data overview",
                        "io_instructions": "str - Critical I/O requirements that must be followed"
                    }
                },
                {
                    "name": "memory_summary",
                    "type": "str",
                    "description": "Summary of past attempts from memory",
                    "required": True,
                },
                {
                    "name": "previous_code",
                    "type": "str",
                    "description": "The previous successful code to improve",
                    "required": True,
                },
                {
                    "name": "previous_analysis",
                    "type": "str",
                    "description": "Analysis of the previous solution",
                    "required": True,
                },
                {
                    "name": "previous_plan",
                    "type": "str",
                    "description": "Previous execution plan (optional)",
                    "required": False,
                    "default": '""""',
                },
                {
                    "name": "previous_output",
                    "type": "str",
                    "description": "Previous execution output (optional)",
                    "required": False,
                    "default": '""""',
                }
            ],
            "outputs": "A formatted prompt string",
            "output_type": "str",
            "output_format": "str - Structured prompt string with role, context, task goal, data overview, I/O instructions, memory summary, previous code, previous analysis, and execution plan",
            "example": """
from dslighting.prompts.aide_prompt import create_improve_prompt

# Input
task_context = {
    "goal_and_data": "Predict bike rental demand using historical data",
    "io_instructions": "Output must be saved to 'predictions.csv' with columns: datetime, count"
}
memory_summary = "Attempt 1 used linear regression with RMSE 0.65"
previous_code = "import pandas as pd\\nmodel = LinearRegression()..."
previous_analysis = "The model achieved RMSE 0.65 but underpredicts peak hours"

# Call
prompt = create_improve_prompt(
    task_context=task_context,
    memory_summary=memory_summary,
    previous_code=previous_code,
    previous_analysis=previous_analysis
)

# Returns formatted prompt string with all context
            """,
        },
        "create_debug_prompt": {
            "category": "aide",
            "description": "Create debug prompt for fixing code errors in AIDE workflow",
            "workflow": "AIDE - Iterative code generation with review",
            "inputs": [
                {
                    "name": "task_context",
                    "type": "Dict[str, Any]",
                    "description": "Task context containing goal and I/O requirements",
                    "required": True,
                    "fields": {
                        "goal_and_data": "str - Task goal and data overview",
                        "io_instructions": "str - Critical I/O requirements"
                    }
                },
                {
                    "name": "buggy_code",
                    "type": "str",
                    "description": "The code that failed with bugs",
                    "required": True,
                },
                {
                    "name": "error_history",
                    "type": "str",
                    "description": "History of previous failures (oldest to newest)",
                    "required": True,
                },
                {
                    "name": "previous_plan",
                    "type": "str",
                    "description": "Previous execution plan (optional)",
                    "required": False,
                    "default": '""""',
                },
                {
                    "name": "memory_summary",
                    "type": "str",
                    "description": "Summary of past attempts from memory (optional)",
                    "required": False,
                    "default": '""""',
                }
            ],
            "outputs": "A formatted debug prompt string",
            "output_type": "str",
            "output_format": "str - Structured prompt with error context and fix instructions",
            "example": """
from dslighting.prompts.aide_prompt import create_debug_prompt

# Input
task_context = {
    "goal_and_data": "Predict bike rental demand",
    "io_instructions": "Save predictions to 'predictions.csv'"
}
buggy_code = "model.fit(X_train, y_train)  # Missing data preprocessing"
error_history = '''
Attempt 1: Failed with KeyError - missing column 'temp'
Attempt 2: Failed with ValueError - shape mismatch
Attempt 3: Current code fails with AttributeError
'''

# Call
prompt = create_debug_prompt(
    task_context=task_context,
    buggy_code=buggy_code,
    error_history=error_history
)

# Returns formatted debug prompt with full error history
            """,
        },
        # AutoKaggle
        "get_deconstructor_prompt": {
            "category": "autokaggle",
            "description": "Deconstruct task into sub-problems for AutoKaggle",
            "workflow": "AutoKaggle - Multi-phase competition solver",
            "inputs": [
                {
                    "name": "task_context",
                    "type": "Dict",
                    "description": "Task context and requirements",
                    "required": True,
                }
            ],
            "outputs": "Prompt for task deconstruction",
            "output_type": "str",
            "output_format": "str - Formatted prompt for breaking down complex tasks",
            "example": "See AutoKaggle workflow documentation",
        },
        "get_phase_planner_prompt": {
            "category": "autokaggle",
            "description": "Plan phases for AutoKaggle workflow execution",
            "workflow": "AutoKaggle - Multi-phase competition solver",
            "inputs": [
                {
                    "name": "task_context",
                    "type": "Dict",
                    "description": "Task context and current state",
                    "required": True,
                }
            ],
            "outputs": "Prompt for phase planning",
            "output_type": "str",
            "output_format": "str - Formatted prompt for planning execution phases",
            "example": "See AutoKaggle workflow documentation",
        },
        # Data Interpreter
        "PLAN_SYSTEM_MESSAGE": {
            "category": "data_interpreter",
            "description": "System message for planner in Data Interpreter",
            "type": "Constant (str)",
            "workflow": "Data Interpreter - Fast code execution in Jupyter",
            "inputs": "None - This is a constant template",
            "outputs": "str - System message for planner",
            "output_type": "str",
            "output_format": "str - Pre-defined system message",
            "example": """
from dslighting.prompts.data_interpreter_prompt import PLAN_SYSTEM_MESSAGE

# Use as system message when calling LLM
system_msg = PLAN_SYSTEM_MESSAGE  # "You are a master planner AI..."
            """,
        },
        "GENERATE_CODE_PROMPT": {
            "category": "data_interpreter",
            "description": "Template for generating code in Data Interpreter",
            "type": "Constant Template (str)",
            "workflow": "Data Interpreter - Fast code execution in Jupyter",
            "inputs": "Template with placeholders: {user_requirement}, {io_instructions}, {plan_status}, {current_task}, {history}",
            "outputs": "str - Formatted code generation prompt",
            "output_type": "str",
            "output_format": "str - Prompt template to be filled with actual values",
            "example": """
from dslighting.prompts.data_interpreter_prompt import GENERATE_CODE_PROMPT

# Fill in the template
prompt = GENERATE_CODE_PROMPT.format(
    user_requirement="Analyze the dataset",
    io_instructions="Output must be saved to 'results.csv'",
    plan_status="Step 1 of 3: Data loading",
    current_task="Load the CSV file",
    history="Previous steps completed"
)
            """,
        },
        # Native
        "PromptBuilder": {
            "category": "native",
            "description": "Fluent API for building prompts programmatically",
            "type": "Class",
            "inputs": "Method chain: .add_role(), .add_context(), .add_instruction()",
            "outputs": "str - The built prompt string",
            "output_type": "str",
            "output_format": "str - Formatted prompt",
            "example": """
from dslighting.prompts import PromptBuilder

builder = PromptBuilder()
prompt = (builder
    .add_role("You are a data scientist")
    .add_context("Task: Analyze bike data")
    .add_instruction("Load data and create visualizations")
    .build())
            """,
        },
        "StructuredPromptBuilder": {
            "category": "native",
            "description": "Dict-based prompt builder (recommended)",
            "type": "Class",
            "inputs": "Dict with sections as keys",
            "outputs": "str - The formatted prompt",
            "output_type": "str",
            "output_format": "str - Structured text with sections",
            "example": """
from dslighting.prompts import StructuredPromptBuilder

builder = StructuredPromptBuilder()
prompt = builder.build({
    "Role": "Data Scientist",
    "Task": "Analyze dataset",
    "Instructions": ["Load data", "Create plots", "Train model"]
})
            """,
        },
    }

    if prompt_name in prompts_info:
        info = prompts_info[prompt_name].copy()
        info["name"] = prompt_name

        # Try to get function signature
        if prompt_name in globals():
            func = globals()[prompt_name]
            if callable(func):
                try:
                    sig = inspect.signature(func)
                    info["signature"] = str(sig)
                except Exception:
                    info["signature"] = "N/A"
            else:
                info["signature"] = "Not callable (constant or class)"

        return info
    else:
        return {
            "name": prompt_name,
            "error": f"Prompt '{prompt_name}' not found. Use list_available_prompts() to see all available prompts.",
        }


# Add discovery functions to __all__
__all__.extend([
    "list_available_prompts",
    "get_prompt_info",
])
