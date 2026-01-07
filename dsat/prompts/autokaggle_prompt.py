from typing import Dict, Any, List
import json
from dsat.services.states.autokaggle_state import TaskContract, AutoKaggleState, PhaseMemory
from dsat.models.formats import StepPlan
from dsat.utils.context import MAX_OUTPUT_CHARS, truncate_output


def get_deconstructor_prompt(description: str, schema: Dict) -> str:
    return f"""
# TASK
You are an expert AI system designer. Your job is to analyze the user's request, the provided Comprehensive Data Exploration Report, AND the CRITICAL I/O REQUIREMENTS, and deconstruct it into a structured JSON Task Contract according to the schema.

# USER REQUEST, DATA REPORT, AND I/O REQUIREMENTS
"{description}"

# INSTRUCTIONS
1. Analyze the 'COMPREHENSIVE DATA EXPLORATION REPORT (Ground Truth)'.
2. Reconcile the findings in the data report with the 'USER DESCRIPTION'.
3. Populate the 'input_files' field accurately.
4. **CRITICAL: Determine the output files.** You MUST use the filename specified in the 'CRITICAL I/O REQUIREMENTS' section for the 'output_files' field. This requirement overrides any other filename mentioned elsewhere.
5. Extract the overall goal, type, outputs, and metrics from the user request, informed by the insights in the data report.

# RESPONSE JSON SCHEMA (Task Contract)
{json.dumps(schema, indent=2)}

# RESPONSE
Provide ONLY the JSON object that conforms to the schema.
"""


def get_phase_planner_prompt(contract: TaskContract) -> str:
    return f"""
# TASK
You are an expert project manager. Based on the provided Task Contract, break down the project into a sequence of high-level, logical phases.

# TASK CONTRACT
{contract.model_dump_json(indent=2)}

# INSTRUCTIONS
- The phases should be a logical progression from start to finish.
- Each phase should represent a distinct stage of work.
- The workflow must adapt dynamically based on the specific task type ('{contract.task_type}') and the `task_goal`. Do not assume a standard ML pipeline (e.g., do not include "Build Model" unless the task explicitly requires it).
- Do not be overly specific. These are high-level phases.

# RESPONSE FORMAT
Provide ONLY a JSON object with a single key "phases" containing a list of strings.
Example: {{"phases": ["Phase 1 Goal", "Phase 2 Goal", "Phase 3 Goal"]}}
"""


def _summarize_phase_history_and_artifacts(state: AutoKaggleState) -> str:
    """Helper function to summarize phase history AND available artifacts."""
    history_summary_parts = []
    if not state.phase_history:
        history_summary = "This is the first phase. No previous phases to report."
    else:
        for ph in state.phase_history:
            artifacts_list = "\\n".join([f"- ./{key}" for key in ph.output_artifacts.keys()])
            history_summary_parts.append(
                f"## Report for Phase: {ph.phase_goal}\\n"
                f"{ph.final_report}\\n"
                f"**Generated Artifacts:**\\n{artifacts_list if artifacts_list else 'None'}"
            )
        history_summary = "\\n\\n".join(history_summary_parts)
    
    # NEW: Add a clear summary of all available artifacts
    available_artifacts_str = "\\n".join([f"- {fname}" for fname in state.global_artifacts.keys()])
    if not available_artifacts_str:
        available_artifacts_str = "None"
        
    return f"""
# PREVIOUSLY COMPLETED PHASES SUMMARY
{history_summary}

# CUMULATIVE ARTIFACTS AVAILABLE IN CWD
```
{available_artifacts_str}
```
"""


def get_step_planner_prompt(state: AutoKaggleState, phase_goal: str) -> str:
    history_summary = _summarize_phase_history_and_artifacts(state)

    return f"""
# TASK
You are a meticulous planner. Your task is to create a detailed, step-by-step plan for the developer to execute the CURRENT PHASE. You must also specify ALL input artifacts to be used and ALL output artifacts to be generated.

# COMPREHENSIVE DATA REPORT AND OVERALL GOAL
{state.full_task_description}

# OVERALL TASK CONTRACT
{state.contract.model_dump_json(indent=2)}

# CRITICAL I/O REQUIREMENTS
{state.io_instructions}

{history_summary}

# CURRENT PHASE GOAL
"{phase_goal}"

# INSTRUCTIONS
1.  **Analyze Available Artifacts**: Review the list of available artifacts. Your plan MUST use these as inputs where appropriate (e.g., use 'train_preprocessed.csv' for model training).
2.  **Create Plan**: Create a detailed, numbered list of actions for the developer. Be specific.
3.  **Specify Inputs**: In the `input_artifacts` field of your JSON response, list the EXACT filenames of all artifacts your plan requires.
4.  **Specify Outputs**: In the `output_files` field, list the EXACT filenames of all new artifacts the plan will create (e.g., models, reports, processed data). It is CRITICAL to include files for saving state, like models (`.pkl`, `.joblib`) or scalers.

# RESPONSE JSON SCHEMA
Provide ONLY a JSON object that conforms to the following schema.
```json
{json.dumps(StepPlan.model_json_schema(), indent=2)}
```
"""


def get_developer_prompt(state: AutoKaggleState, phase_goal: str, plan: str, attempt_history: List) -> str:
    history_summary = _summarize_phase_history_and_artifacts(state)
    
    error_context = ""
    if attempt_history:
        history_str_parts = []
        # Iterate over all previous attempts to build a comprehensive history
        for attempt in reversed(attempt_history): # Show most recent failure first
            safe_validation = truncate_output(json.dumps(attempt.validation_result), MAX_OUTPUT_CHARS)
            safe_error = truncate_output(attempt.execution_error or "No runtime error.", MAX_OUTPUT_CHARS)
            safe_code = truncate_output(attempt.code or "", MAX_OUTPUT_CHARS)
            history_str_parts.append(f"""
---
### FAILED ATTEMPT {attempt.attempt_number + 1}
#### Reviewer's Suggestion: "{attempt.review_suggestion}"
#### Validation Failure: {safe_validation}
#### Execution Error:
```
{safe_error}
```
#### Previous Code for this Attempt:
```python
{safe_code}
```
---
""")
        
        error_context = f"""
# PREVIOUS ATTEMPTS FAILED
Your previous attempts to complete this phase failed. Analyze the full history below (most recent first) to write a corrected version and avoid repeating mistakes.
{''.join(history_str_parts)}
"""

    return f"""
# TASK
You are an expert developer. Your task is to write a complete Python script to execute the provided plan for the current phase.

# COMPREHENSIVE DATA REPORT AND OVERALL GOAL
{state.full_task_description}

# OVERALL TASK CONTRACT
{state.contract.model_dump_json(indent=2)}

# CRITICAL I/O REQUIREMENTS
{state.io_instructions}

{history_summary}

# CURRENT PHASE GOAL
"{phase_goal}"

# DETAILED PLAN FOR THIS PHASE
{plan}

{error_context}

# INSTRUCTIONS
- Your script MUST load any necessary input artifacts listed in the "CUMULATIVE ARTIFACTS AVAILABLE" section using their exact filenames.
- Your script MUST generate and save all output files specified in the plan. Use libraries like `joblib` or `pickle` to save Python objects like models or scalers.
- All file operations must be relative to the current working directory.

# RESPONSE FORMAT
Provide ONLY the complete, runnable Python code in a single code block. Do not add explanations.
"""


def get_validator_prompt(contract: TaskContract, filename: str, content_snippet: str) -> str:
    return f"""
# TASK

You are an automated QA agent. Validate if the generated file conforms to the Task Contract.

# TASK CONTRACT

{contract.model_dump_json(indent=2)}

# GENERATED FILE: {filename}

# FILE CONTENT (first 20 lines):

{content_snippet}

# VALIDATION

Based on the contract, does this file meet the requirements for '{filename}'? Check format, content, data types, and any other constraints mentioned in the contract's description for this file.

# RESPONSE FORMAT

Respond with a single JSON object: {{"passed": <true_or_false>, "reason": "A detailed explanation."}}
"""


def get_reviewer_prompt(phase_goal: str, dev_result: Dict, plan: str = "") -> str:
    safe_code = truncate_output(dev_result.get('code', '# N/A'), MAX_OUTPUT_CHARS)
    safe_error = truncate_output(dev_result.get('error') or "None", MAX_OUTPUT_CHARS)
    safe_validation = truncate_output(json.dumps(dev_result.get('validation_result')), MAX_OUTPUT_CHARS)
    return f"""
# TASK

You are a meticulous reviewer. Assess the developer's work for the given phase. Provide a score (1-5) and a constructive suggestion for improvement if the score is below 4.

# CURRENT PHASE GOAL

"{phase_goal}"

# PLAN BEING EXECUTED

{plan}

# DEVELOPER'S WORK

  - **Code:**
```python
{safe_code}
```

  - **Code Execution Status:** {"Success" if dev_result['status'] else "Failed"}
  - **Execution Error:** {safe_error}
  - **Validation Result:** {safe_validation}

# INSTRUCTIONS

  - If the code failed to execute, the score must be low (1 or 2). Your suggestion should focus on fixing the error.
  - If the phase is an early one like "Explore Data" or "Prepare Data", DO NOT penalize the developer for not creating the final output file specified in the contract. The validation check for that file might fail, which is acceptable at this stage. Focus on whether the code successfully achieved the phase's specific goal.
  - If the code executed and passed relevant validations for this phase, evaluate the approach. Is it a good way to achieve the phase goal? Score 3-5.
  - A score of 5 requires a truly excellent and efficient implementation.

# RESPONSE FORMAT

Provide ONLY a JSON object: {{"score": <1_to_5>, "suggestion": "Your suggestion here."}}
"""


def get_summarizer_prompt(state: AutoKaggleState, phase_memory: PhaseMemory) -> str:
    attempt_summary = ""
    for attempt in phase_memory.attempts:
        attempt_summary += f"\\n### Attempt {attempt.attempt_number + 1} (Score: {attempt.review_score})\\n- Suggestion: {attempt.review_suggestion}\\n"

    return f"""
# TASK

You are a technical writer. Summarize the work done in the completed phase into a concise report.

# OVERALL TASK CONTRACT

{state.contract.model_dump_json(indent=2)}

# CURRENT PHASE GOAL

"{phase_memory.phase_goal}"

# ATTEMPT HISTORY FOR THIS PHASE

{attempt_summary}

# FINAL SUCCESSFUL CODE

```python
{phase_memory.attempts[-1].code if phase_memory.attempts else 'No code available'}
```

# INSTRUCTIONS

Synthesize all information into a report covering:

1.  The main objective of this phase.
2.  The final approach taken to achieve it.
3.  Key findings or results from the code execution.
4.  How this phase's outcome contributes to the overall project goal.

# RESPONSE FORMAT

Provide the summary as a comprehensive report in Markdown.
"""
