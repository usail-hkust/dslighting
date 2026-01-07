from typing import Dict
from dsat.prompts.common import create_draft_prompt

def create_stepwise_code_prompt(goal: str, plan: str, history: str, current_step: str, io_instructions: str) -> str:
    """Creates a prompt for generating code for a single step in a complex plan."""
    return (
        f"You are executing a complex data science plan step-by-step.\n\n"
        f"# OVERALL GOAL\n{goal}\n\n"
        f"# CRITICAL I/O REQUIREMENTS (MUST BE FOLLOWED)\n{io_instructions}\n\n"
        f"# OVERALL PLAN\n{plan}\n\n"
        f"# PREVIOUSLY EXECUTED STEPS (CODE & OUTPUT)\n{history}\n\n"
        f"# CURRENT STEP TO IMPLEMENT\n{current_step}\n\n"
        "Your task is to write the Python code ONLY for the CURRENT STEP. The code will be executed in a Jupyter-like environment, so you can assume variables from previous steps are in memory. Ensure your code adheres to the I/O requirements."
    )


def create_stepwise_debug_prompt(goal: str, plan: str, history: str, current_step: str, failed_code: str, error_history: str, io_instructions: str) -> str:
    """Creates a prompt for debugging a failed step in a stepwise execution."""
    return (
        f"You are debugging a complex data science plan being executed step-by-step.\n\n"
        f"# OVERALL GOAL\n{goal}\n\n"
        f"# CRITICAL I/O REQUIREMENTS (MUST BE FOLLOWED)\n{io_instructions}\n\n"
        f"# OVERALL PLAN\n{plan}\n\n"
        f"# PREVIOUSLY EXECUTED STEPS (CODE & OUTPUT)\n{history}\n\n"
        f"# FAILED STEP INSTRUCTION\n{current_step}\n\n"
        f"# MOST RECENT FAILED CODE\n```python\n{failed_code}\n```\n\n"
        f"# HISTORY OF FAILED ATTEMPTS FOR THIS STEP\n{error_history}\n\n"
        "Your task is to analyze the full history of errors for this step and provide the corrected Python code ONLY for the FAILED STEP. Assume variables from previous steps are still in memory. Ensure your corrected code adheres to the I/O requirements."
    )
