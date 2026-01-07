from typing import Dict

from dsat.utils.context import MAX_HISTORY_CHARS, MAX_OUTPUT_CHARS, truncate_output
from dsat.prompts.common import _dict_to_str, _get_common_guidelines, create_draft_prompt

def create_improve_prompt(task_context: Dict, memory_summary: str, previous_code: str, previous_analysis: str, previous_plan: str = "", previous_output: str = "") -> str:
    """Creates the system prompt for improving an existing solution."""
    safe_previous_code = truncate_output(previous_code, MAX_OUTPUT_CHARS)
    safe_previous_analysis = truncate_output(previous_analysis, MAX_OUTPUT_CHARS)
    safe_previous_plan = truncate_output(previous_plan, MAX_OUTPUT_CHARS)
    safe_previous_output = truncate_output(previous_output, MAX_OUTPUT_CHARS)
    prompt_dict = {
        "Role": "You are an expert AI Developer tasked with improving a previous solution.",
        "Task Goal and Data Overview": task_context.get("goal_and_data", "N/A"),
        "CRITICAL I/O REQUIREMENTS (MUST BE FOLLOWED)": task_context.get("io_instructions", "N/A"),
        "Memory of Past Attempts": memory_summary,
        "Previous Successful Solution": {
            "Plan": safe_previous_plan,
            "Analysis": safe_previous_analysis,
            "Execution Output (Summarized)": safe_previous_output,
            "Code": f"```python\n{safe_previous_code}\n```",
        },
        "Instructions": {
            "Goal": "Propose a single, atomic improvement and implement the complete, updated code. Ensure the improved code still adheres to the CRITICAL I/O REQUIREMENTS.",
            "Improvement Guideline": "Focus on one specific change to the approach, algorithm, data processing pipeline, or parameters to better meet the task requirements.",
            **_get_common_guidelines()
        }
    }
    return _dict_to_str(prompt_dict)

def create_debug_prompt(task_context: Dict, buggy_code: str, error_history: str, previous_plan: str = "", memory_summary: str = "") -> str:
    """Creates the system prompt for debugging a failed solution."""
    safe_buggy_code = truncate_output(buggy_code, MAX_OUTPUT_CHARS)
    safe_error_history = truncate_output(error_history, MAX_HISTORY_CHARS)
    safe_previous_plan = truncate_output(previous_plan, MAX_OUTPUT_CHARS)
    prompt_dict = {
        "Role": "You are an expert Python programmer debugging a data science script.",
        "Task Goal and Data Overview": task_context.get("goal_and_data", "N/A"),
        "CRITICAL I/O REQUIREMENTS (MUST BE FOLLOWED)": task_context.get("io_instructions", "N/A"),
        "Memory of Past Attempts": memory_summary,
        "Most Recent Failed Attempt": {
            "Plan": safe_previous_plan,
            "Code": f"```python\n{safe_buggy_code}\n```",
        },
        "History of Failures (Oldest to Newest)": safe_error_history,
        "Instructions": {
            "Goal": "Analyze the full history of failures for this task. Identify the root cause, propose a fix, and implement the complete, corrected code.",
            "Debugging Guideline": "Your plan should state the root cause and the fix. The new code must be a complete, runnable script.",
            **_get_common_guidelines()
        }
    }
    return _dict_to_str(prompt_dict)
