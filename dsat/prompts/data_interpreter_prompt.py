# System message for the Planner
PLAN_SYSTEM_MESSAGE = """
You are a master planner AI. Break down a complex user request into a sequence of simple, actionable steps for a data scientist.
Your plan MUST conclude with a final step that generates the required output file as specified in the user request's I/O requirements.
Output a JSON list of tasks, where each task has "task_id", "instruction", and "dependent_task_ids".
Provide ONLY the JSON list in a single code block.
"""

PLAN_PROMPT = """
# User Request
{user_request}

# Your Plan (JSON format)
"""

GENERATE_CODE_PROMPT = """
# Overall Goal and Data Report
{user_requirement}

# CRITICAL I/O REQUIREMENTS (MUST BE FOLLOWED)
{io_instructions}

# Plan Status
{plan_status}

# Current Task
{current_task}

# History (Previous Code and Outputs)
{history}

# Instruction
Write Python code for the **Current Task**. Ensure the code strictly follows the CRITICAL I/O REQUIREMENTS. Generate visualizations if required.
Provide ONLY the Python code in a single code block.
"""

REFLECT_AND_DEBUG_PROMPT = """
# Overall Goal and Data Report
{user_requirement}

# CRITICAL I/O REQUIREMENTS (MUST BE FOLLOWED)
{io_instructions}

# History (Previous Code and Outputs)
{history}

# Current Task
{current_task}

# Failed Code
```python
{failed_code}
```

# Error Output
```
{error_output}
```

# Instruction
Your previous code failed. Analyze the error in the context of the execution history (previous steps) and rewrite the full, corrected Python code for the **Current Task**. Ensure the corrected code strictly follows the CRITICAL I/O REQUIREMENTS.
Provide ONLY the corrected Python code in a single code block.
"""

FINALIZE_OUTPUT_PROMPT = """
# Overall Goal and Data Report
{user_requirement}

# Execution History
The following tasks have been successfully executed, and their results and variables are available in the current notebook session:
{history}

# CRITICAL I/O REQUIREMENTS (MUST BE FOLLOWED)
{io_instructions}

# Final Instruction
Your final and most important task is to generate the required output file.
Based on all the previous steps and the CRITICAL I/O REQUIREMENTS, write the Python code that creates the final output file named **'{output_filename}'** in the correct format.

The file MUST be saved in the current working directory.
Provide ONLY the Python code for this final step in a single code block.
"""