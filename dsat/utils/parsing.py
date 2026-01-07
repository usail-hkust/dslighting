"""
Helper functions for parsing structured content from raw LLM text responses.
"""
import re

def parse_plan_and_code(response: str) -> tuple[str, str]:
    """
    Extracts a natural language plan and a Python code block from an LLM's response.
    Assumes a format where the plan precedes the code block.

    Args:
        response: The raw text response from the LLM.

    Returns:
        A tuple containing the extracted plan and code.
        Returns a default error message for code if not found.
    """
    # Use a non-greedy match for the plan to capture everything before the first code block.
    plan_match = re.search(r"(.*?)```(?:python|py)?", response, re.DOTALL)
    if plan_match:
        plan = plan_match.group(1).strip()
    else:
        # If no code block is found, assume the entire response is the plan.
        plan = response.strip()

    code_match = re.search(r"```(?:python|py)?\n(.*?)\n```", response, re.DOTALL)
    if code_match:
        code = code_match.group(1).strip()
    else:
        # Fallback if the code block is malformed or missing
        code = "# ERROR: Could not parse code block from LLM response."

    return plan, code