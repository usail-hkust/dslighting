from typing import Dict, List, Optional

def _dict_to_str(d: Dict, indent=0) -> str:
    """Helper to format dictionaries into a readable string for prompts."""
    lines = []
    for k, v in d.items():
        prefix = ' ' * (indent * 2)
        if isinstance(v, dict):
            lines.append(f"{prefix}{k}:")
            lines.append(_dict_to_str(v, indent + 1))
        elif isinstance(v, list):
            lines.append(f"{prefix}{k}:")
            for item in v:
                lines.append(' ' * ((indent + 1) * 2) + f"- {item}")
        else:
            lines.append(f"{prefix}{k}: {v}")
    return "\n".join(lines)

def _get_common_guidelines() -> Dict:
    """Returns a dictionary of common instructions for all prompts."""
    return {
        "Response Format": (
            "Your response MUST start with a brief natural language plan (3-5 sentences), "
            "followed by a single, complete Python code block wrapped in ```python ... ```. "
            "Do not include any other text or headings."
        ),
        "Implementation Guidelines": [
            "The code must be a self-contained, single-file Python script.",
            "If the task involves modeling or optimization, print key metrics (e.g., validation scores) to standard output. Otherwise, ensure the output clearly presents the findings or results.",
            "Follow the CRITICAL I/O REQUIREMENTS provided in the task description precisely for all file operations.",
            "Do not use interactive elements like `input()` or `matplotlib.pyplot.show()`."
        ]
    }

def create_draft_prompt(
    task_context: Dict,
    memory_summary: str,
    retrieved_knowledge: Optional[str] = None,
    extra_context: Optional[str] = None
) -> str:
    """
    Creates the system prompt for generating an initial solution draft.

    Args:
        task_context: MLE standard format dict with keys:
            - goal_and_data: Task description and data overview (DO NOT modify)
            - io_instructions: I/O requirements (DO NOT modify)
        memory_summary: Summary of previous attempts
        retrieved_knowledge: Optional knowledge from RAG/system
        extra_context: Optional additional context (e.g., data insights, analysis results)

    Returns:
        Formatted prompt string

    Note:
        IMPORTANT: Always keep task_context in MLE standard format.
        Use extra_context parameter to add additional information.
        This ensures compatibility with MLE data parsing and grading systems.
    """
    prompt_dict = {
        "Role": "You are an expert Data Scientist and AI Engineer.",
        "Task Goal and Data Overview": task_context.get("goal_and_data", "N/A"),
        "Memory of Past Attempts": memory_summary,
        "Retrieved Knowledge": retrieved_knowledge or "No relevant knowledge was retrieved for this task.",
    }

    # Add extra context if provided (before I/O requirements)
    if extra_context:
        prompt_dict["Additional Context"] = extra_context

    # CRITICAL I/O REQUIREMENTS should come AFTER Additional Context but BEFORE Instructions
    # This ensures model sees data insights first, then I/O constraints, then implementation guidelines
    prompt_dict["CRITICAL I/O REQUIREMENTS (MUST BE FOLLOWED)"] = task_context.get("io_instructions", "N/A")

    prompt_dict["Instructions"] = {
        "Goal": "Propose a simple but effective plan and implement it in Python" + (
            ", incorporating insights from the retrieved knowledge and additional context if applicable." if (retrieved_knowledge or extra_context) else "."
        ),
        "Design Guideline": "Your first solution should be straightforward and robust. Focus on correctly addressing the core requirements based on the data report AND the CRITICAL I/O REQUIREMENTS." + (
            " Consider the additional context provided above if applicable." if extra_context else ""
        ),
        **_get_common_guidelines()
    }

    return _dict_to_str(prompt_dict)