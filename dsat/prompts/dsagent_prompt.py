PLAN_PROMPT_TEMPLATE = """
You are a helpful AI expert assistant, responsible for decision making on the action plans.

# Task Objective and Data Report
{research_problem}

# CRITICAL I/O REQUIREMENTS (MUST BE FOLLOWED)
{io_instructions}

# Current Progress Log
{running_log}

# Relevant Past Experience Case
{case}

Based on all this information, provide a short, precise but detailed instruction summary on the action plan for the next step. Ensure the plan considers the CRITICAL I/O REQUIREMENTS.
"""

PROGRAMMER_PROMPT_TEMPLATE = """
You are a helpful AI-oriented programming expert.

# Overall Task Objective and Data Report
{research_problem}

# CRITICAL I/O REQUIREMENTS (MUST BE FOLLOWED)
{io_instructions}

# Current Progress Log (history of actions)
{running_log}

Given this python script:
```python
{code}
```

Now please edit this script according to the following instructions:

```instruction
{plan}
```

Provide the **full** code after the edit, ensuring it aligns with the overall goal, the CRITICAL I/O REQUIREMENTS, and lessons learned from the progress log.
"""

DEBUGGER_PROMPT_TEMPLATE = """
You are a helpful AI-oriented programming expert.

# Overall Task Objective and Data Report
{research_problem}

# CRITICAL I/O REQUIREMENTS (MUST BE FOLLOWED)
{io_instructions}

# Current Progress Log (history of actions)
{running_log}

The instruction for modification was:

```instruction
{plan}
```

This is the current python code:

```python
{code}
```

However, there are some bugs in this version. Here is the execution log:

```log
{error_log}
```

Please revise the script to fix these bugs and provide the **full** corrected code, ensuring it aligns with the overall goal, the CRITICAL I/O REQUIREMENTS, and lessons learned from the progress log.
"""

LOGGER_PROMPT_TEMPLATE = """
Given the instructions, execution log, and code difference of the last action:
[Instructions]: {plan}
[Execution Log]: {execution_log}
[Code Difference]: {diff}
[Progress Log]: {running_log}

Summarize the progress of the last step and append it to the progress log in this format:
[Action Summary]: Summarize what action was taken in the last step.
[Action Result]: Summarize the outcome of the action and whether it successfully achieved the objective defined in the [Instructions].
"""
