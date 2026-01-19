"""
DSLighting 2.0 - Operators Layer

This layer provides atomic, reusable capability units.

Operators are organized into categories:
- LLM Operators: Language model operations (generate, plan, review, summarize)
- Code Operators: Code execution operations
- Data Operators: Data science operations (analysis, features, modeling, evaluation)
- Orchestration Operators: Composition patterns (Pipeline, Parallel, Conditional)
"""

# Base operator class
try:
    from dsat.operators.base import Operator
except ImportError:
    Operator = None

# LLM Operators
try:
    from dsat.operators.llm_basic import GenerateCodeAndPlanOperator
    from dsat.operators.llm_basic import PlanOperator
    from dsat.operators.llm_basic import ReviewOperator
    from dsat.operators.llm_basic import SummarizeOperator
except ImportError:
    GenerateCodeAndPlanOperator = None
    PlanOperator = None
    ReviewOperator = None
    SummarizeOperator = None

# Code Operators
try:
    from dsat.operators.code import ExecuteAndTestOperator
except ImportError:
    ExecuteAndTestOperator = None

# Re-export orchestration operators
from .orchestration import Pipeline, Parallel, Conditional

# Custom Operators (用户自定义)
try:
    from .custom import *  # 导入所有自定义 operators
except ImportError:
    # 如果没有自定义 operators，忽略
    pass

__all__ = [
    # Base
    "Operator",
    # LLM Operators
    "GenerateCodeAndPlanOperator",
    "PlanOperator",
    "ReviewOperator",
    "SummarizeOperator",
    # Code Operators
    "ExecuteAndTestOperator",
    # Orchestration
    "Pipeline",
    "Parallel",
    "Conditional",
]


# ============================================================================
# Discovery Functions - Help users discover available operators
# ============================================================================

def list_available_operators(category: str = "all") -> dict[str, list[str]]:
    """
    List all available operators by category.

    Args:
        category: Filter by category ('all', 'llm', 'code', 'data', 'orchestration', 'custom')
                  Default: 'all'

    Returns:
        Dictionary mapping category names to lists of operator names

    Example:
        >>> from dslighting.operators import list_available_operators
        >>> ops = list_available_operators()
        >>> for category, names in ops.items():
        ...     print(f"{category}: {len(names)} operators")
    """
    categories = {
        "base": ["Operator"],
        "llm": [
            "GenerateCodeAndPlanOperator",
            "PlanOperator",
            "ReviewOperator",
            "SummarizeOperator",
        ],
        "code": [
            "ExecuteAndTestOperator",
        ],
        "orchestration": [
            "Pipeline",
            "Parallel",
            "Conditional",
        ],
    }

    # Add custom operators if any
    try:
        from .custom import __all__ as custom_all
        if custom_all:
            categories["custom"] = custom_all
    except (ImportError, AttributeError):
        pass

    if category == "all":
        return categories
    elif category in categories:
        return {category: categories[category]}
    else:
        return {}


def get_operator_info(operator_name: str) -> dict[str, any]:
    """
    Get detailed information about a specific operator.

    Args:
        operator_name: Name of the operator class

    Returns:
        Dictionary with 'name', 'category', 'description', 'inputs', 'outputs',
        'output_format', 'example' keys

    Example:
        >>> from dslighting.operators import get_operator_info
        >>> info = get_operator_info("PlanOperator")
        >>> print(f"Inputs: {info['inputs']}")
        >>> print(f"Outputs: {info['outputs']}")
    """
    operators_info = {
        # Base
        "Operator": {
            "category": "base",
            "description": "Base class for all operators. Inherit from this to create custom operators.",
            "inputs": "Varies by implementation",
            "outputs": "Varies by implementation",
            "output_type": "Any",
            "output_format": "Any - Depends on the specific operator implementation",
            "example": """
from dslighting.operators import Operator

class MyCustomOperator(Operator):
    async def __call__(self, input_data: str) -> dict:
        # Your custom logic here
        result = await self.process(input_data)
        return result
            """,
        },
        # LLM Operators
        "PlanOperator": {
            "category": "llm",
            "description": "Creates a structured, multi-step plan based on a user request using LLM",
            "inputs": [
                {
                    "name": "user_request",
                    "type": "str",
                    "description": "The user's task request or goal",
                    "required": True,
                }
            ],
            "outputs": "A structured Plan object",
            "output_type": "Plan",
            "output_format": "Plan from dslighting.core.types with tasks: List[Task], where each Task has: task_id (str), instruction (str), dependent_task_ids (List[str])",
            "async": True,
            "requires_services": ["LLMService"],
            "example": """
from dslighting.operators import PlanOperator
from dslighting.services import LLMService

llm_service = LLMService(model="gpt-4o")
operator = PlanOperator(llm_service=llm_service)

# Input
user_request = "Analyze the bike sharing dataset and predict future demand"

# Call
plan = await operator(user_request=user_request)

# Output structure:
# Plan(tasks=[
#   Task(task_id="1", instruction="Load and explore data", dependent_task_ids=[]),
#   Task(task_id="2", instruction="Build prediction model", dependent_task_ids=["1"]),
#   Task(task_id="3", instruction="Generate predictions", dependent_task_ids=["2"])
# ])
            """,
        },
        "GenerateCodeAndPlanOperator": {
            "category": "llm",
            "description": "Generates both a plan and corresponding code based on prompts",
            "inputs": [
                {
                    "name": "system_prompt",
                    "type": "str",
                    "description": "System prompt defining the task context",
                    "required": True,
                },
                {
                    "name": "user_prompt",
                    "type": "str",
                    "description": "User-specific instructions",
                    "required": False,
                    "default": '""""',
                }
            ],
            "outputs": "Tuple containing plan string and generated code string",
            "output_type": "tuple[str, str]",
            "output_format": "tuple[str, str] - First element (str) is the plan, second element (str) is the generated code",
            "async": True,
            "requires_services": ["LLMService"],
            "example": """
from dslighting.operators import GenerateCodeAndPlanOperator
from dslighting.services import LLMService

llm_service = LLMService(model="gpt-4o")
operator = GenerateCodeAndPlanOperator(llm_service=llm_service)

# Input
system_prompt = "Create a data analysis script for the bike dataset"
user_prompt = "Include visualization and predictions"

# Call
plan, code = await operator(system_prompt=system_prompt, user_prompt=user_prompt)

# Output structure:
# plan: "1. Load data\\n2. Visualize trends\\n3. Build model"
# code: "import pandas as pd\\n..."
            """,
        },
        "ReviewOperator": {
            "category": "llm",
            "description": "Reviews code execution output and provides structured evaluation",
            "inputs": [
                {
                    "name": "prompt_context",
                    "type": "Dict[str, Any]",
                    "description": "Context dictionary containing task, code, and output",
                    "required": True,
                    "fields": {
                        "task": "str - The task description",
                        "code": "str - The code that was executed",
                        "output": "str - The execution output or error",
                    }
                }
            ],
            "outputs": "Structured review result",
            "output_type": "ReviewResult",
            "output_format": "ReviewResult from dslighting.core.types with fields: is_buggy (bool), summary (str), metric_value (Optional[float]), lower_is_better (bool)",
            "async": True,
            "requires_services": ["LLMService"],
            "example": """
from dslighting.operators import ReviewOperator
from dslighting.services import LLMService

llm_service = LLMService(model="gpt-4o")
operator = ReviewOperator(llm_service=llm_service)

# Input
context = {
    "task": "Predict bike rental demand",
    "code": "model.fit(X_train, y_train)",
    "output": "Training completed with RMSE: 0.45"
}

# Call
result = await operator(prompt_context=context)

# Output structure:
# ReviewResult(
#     is_buggy=False,
#     summary="Model trained successfully with good performance",
#     metric_value=0.45,
#     lower_is_better=True
# )
            """,
        },
        "SummarizeOperator": {
            "category": "llm",
            "description": "Generates a concise summary of execution context or results",
            "inputs": [
                {
                    "name": "context",
                    "type": "str",
                    "description": "The context or events to summarize",
                    "required": True,
                }
            ],
            "outputs": "A concise text summary",
            "output_type": "str",
            "output_format": "str - The summarized text",
            "async": True,
            "requires_services": ["LLMService"],
            "example": """
from dslighting.operators import SummarizeOperator
from dslighting.services import LLMService

llm_service = LLMService(model="gpt-4o")
operator = SummarizeOperator(llm_service=llm_service)

# Input
context = '''
Phase 1: Data exploration completed. Found 10 features, 2 missing values.
Phase 2: Preprocessing applied. Missing values imputed.
Phase 3: Model trained with accuracy 0.85.
'''

# Call
summary = await operator(context=context)

# Output: "Completed data exploration, preprocessing, and model training.
#          Found 10 features with 2 missing values which were imputed.
#          Final model achieved 85% accuracy."
            """,
        },
        # Code Operators
        "ExecuteAndTestOperator": {
            "category": "code",
            "description": "Executes code in a sandboxed environment and runs tests",
            "inputs": [
                {
                    "name": "code",
                    "type": "str",
                    "description": "The Python code to execute",
                    "required": True,
                }
            ],
            "outputs": "Execution output and test results",
            "output_type": "Dict[str, Any]",
            "output_format": "Dict[str, Any] with keys: 'output' (str) - execution output, 'success' (bool) - whether execution succeeded, 'error' (Optional[str]) - error message if failed",
            "async": True,
            "requires_services": ["SandboxService"],
            "example": """
from dslighting.operators import ExecuteAndTestOperator
from dslighting.services import SandboxService

sandbox = SandboxService()
operator = ExecuteAndTestOperator(sandbox_service=sandbox)

# Input
code = '''
import pandas as pd
df = pd.read_csv("data.csv")
print(df.head())
'''

# Call
result = await operator(code=code)

# Output structure:
# {
#     "output": "   col1  col2\\n0     1     2\\n...",
#     "success": True,
#     "error": None
# }
            """,
        },
        # Orchestration Operators
        "Pipeline": {
            "category": "orchestration",
            "description": "Execute operators sequentially, passing output of one as input to next",
            "inputs": [
                {
                    "name": "operators",
                    "type": "List[Operator]",
                    "description": "List of operators to execute in sequence",
                    "required": True,
                }
            ],
            "outputs": "Final output from the last operator",
            "output_type": "Any",
            "output_format": "Any - The output type depends on the last operator in the pipeline",
            "async": True,
            "requires_services": "Depends on component operators",
            "example": """
from dslighting.operators import Pipeline, PlanOperator, GenerateCodeAndPlanOperator

pipeline = Pipeline([
    plan_op,
    code_op,
    execute_op
])

# Execute sequentially
result = await pipeline(input_data)
            """,
        },
        "Parallel": {
            "category": "orchestration",
            "description": "Execute multiple operators in parallel",
            "inputs": [
                {
                    "name": "operators",
                    "type": "List[Operator]",
                    "description": "List of operators to execute in parallel",
                    "required": True,
                }
            ],
            "outputs": "List of results from all operators",
            "output_type": "List[Any]",
            "output_format": "List[Any] - Results in the same order as input operators. Each element's type depends on the corresponding operator's output type",
            "async": True,
            "requires_services": "Depends on component operators",
            "example": """
from dslighting.operators import Parallel

parallel_ops = Parallel([op1, op2, op3])
results = await parallel_ops(input_data)
# results: [result1, result2, result3]
            """,
        },
        "Conditional": {
            "category": "orchestration",
            "description": "Execute different operators based on a condition function",
            "inputs": [
                {
                    "name": "condition_func",
                    "type": "Callable",
                    "description": "Function that returns True/False to decide which branch to execute",
                    "required": True,
                },
                {
                    "name": "if_op",
                    "type": "List[Operator]",
                    "description": "Operators to execute if condition is True",
                    "required": False,
                },
                {
                    "name": "else_op",
                    "type": "List[Operator]",
                    "description": "Operators to execute if condition is False",
                    "required": False,
                }
            ],
            "outputs": "Output from the executed branch",
            "output_type": "Any",
            "output_format": "Any - The output type depends on which branch was executed and the last operator in that branch",
            "async": True,
            "requires_services": "Depends on component operators",
            "example": """
from dslighting.operators import Conditional

def has_data(data):
    return len(data) > 0

conditional = Conditional(
    condition_func=has_data,
    if_op=[process_op],
    else_op=[error_op]
)

result = await conditional(data)
            """,
        },
    }

    if operator_name in operators_info:
        info = operators_info[operator_name].copy()
        info["name"] = operator_name
        return info
    else:
        return {
            "name": operator_name,
            "error": f"Operator '{operator_name}' not found. Use list_available_operators() to see all available operators.",
        }


# Add discovery functions to __all__
__all__.extend([
    "list_available_operators",
    "get_operator_info",
])
