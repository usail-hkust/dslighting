# web_ui/backend/app/prompts/agent_prompts.py

from typing import Dict, List, Optional, Any
from dsat.prompts.common import _dict_to_str

# Universal JSON Format Requirement (Simplified - No Schema Conflicts)
JSON_FORMAT_REQUIREMENT = """
# RESPONSE FORMAT (CRITICAL)

You MUST respond with a valid JSON object ONLY.

**Requirements:**
- Output ONLY the raw JSON object
- NO markdown code blocks (```json or ```)
- NO conversational filler
- NO additional text before or after the JSON

The system will automatically validate your response against the required schema.
"""

def _get_execution_environment() -> Dict:
    return {
        "Persistent Process": "Code runs in a persistent Python process. Variables are preserved between steps.",
        "Self-Correction": "If execution fails, you will receive the error log. You must then output the COMPLETE corrected script again.",
        "Visualization Protocol": (
            "1. NEVER use plt.show().\n"
            "2. MIRROR DATA SOURCE: If analyzing files in 'raw/', save plots to 'eda/raw/'. If analyzing 'prepared_data/', save to 'eda/prepared/'.\n"
            "3. You MUST run `os.makedirs('eda/raw', exist_ok=True)` or `os.makedirs('eda/prepared', exist_ok=True)` in your code before saving.\n"
            "4. FOR EACH PLOT, save a companion text file (e.g., 'eda/raw/plot1.txt' or 'eda/prepared/plot1.txt') with a concise statistical insight."
        ),
        "No Chatter": "Do not include conversational filler. Respond ONLY with the requested JSON."
    }

def create_data_prep_prompt(base_context: str, blueprint_json: str) -> str:
    prompt_dict = {
        "Role": "Data Preparation Specialist",
        "Goal": "Transform raw data into prepared datasets following the established blueprint manifest.",
        "The Contract (manifest.json)": blueprint_json,
        "Mandatory Protocols": {
            "Input Paths": "Read raw data from 'raw/' directory (e.g., pd.read_csv('raw/train.csv')).",
            "Output Paths": "Write prepared data to 'prepared/' directory structure (e.g., prepared/public/train.csv, prepared/private/answer.csv).",
            "Atomic Writing": "1. Clear existing prepared data. 2. Implement transformation logic. 3. Write ALL files at once.",
            "Directory Creation": "Always create directories: os.makedirs('prepared/public', exist_ok=True) and os.makedirs('prepared/private', exist_ok=True).",
            "READ-ONLY Manifest": "A 'manifest.json' exists at the root. DO NOT TOUCH, OVERWRITE, OR RECREATE IT. It is your read-only source of truth.",
            "ID & Alignment": "ALL output files (train, test, answer, sampleSubmission) MUST include a unique 'id' column to ensure samples are correctly indexed and aligned."
        },
        "Data Context & Schema": base_context,
        "Execution Environment": _get_execution_environment()
    }
    return _log_format(prompt_dict)

def create_blueprint_prompt(user_msg: str, base_context: str) -> str:
    prompt_dict = {
        "Role": "Data Architect",
        "Goal": "Design a 'Blueprint' for a data science task based on raw data and user requirements.",
        "User Request": user_msg,
        "Data Context": base_context,
        "Instruction": [
            "Propose a rigorous data preparation plan.",
            "MANDATORY FILE LAYOUT: Your 'output_layout' MUST contain EXACTLY these 4 keys and NO OTHERS: 'train', 'test', 'answer', 'sampleSubmission'.",
            "MANDATORY: Define a unique 'id' column for all files to ensure alignment.",
            "OUTPUT PATH CONVENTION: Use 'prepared/public/' for train/test (public data) and 'prepared/private/' for answer (private data).",
            "Output strictly in JSON using the TaskBlueprint schema."
        ],
        "Layout Examples (Adapt to Modality)": {
            "Tabular/Text (CSV)": {
                "train": "prepared/public/train.csv",
                "test": "prepared/public/test.csv",
                "answer": "prepared/private/answer.csv",
                "sampleSubmission": "prepared/public/sampleSubmission.csv"
            },
            "Image/Audio (Folders)": {
                "train": "prepared/public/train/",
                "test": "prepared/public/test/",
                "answer": "prepared/private/answer.csv",
                "sampleSubmission": "prepared/public/sampleSubmission.csv"
            },
            "Object Detection": {
                "train": "prepared/public/train_images/",
                "test": "prepared/public/test_images/",
                "answer": "prepared/private/annotations.json",
                "sampleSubmission": "prepared/public/results_template.json"
            }
        }
    }
    return _log_format(prompt_dict)

def create_blueprint_refinement_prompt(user_feedback: str, old_blueprint: str, base_context: str) -> str:
    prompt_dict = {
        "Role": "Data Architect",
        "Goal": "Refine the existing blueprint based on user feedback.",
        "Data Context": base_context,
        "Original Blueprint": old_blueprint,
        "User Feedback": user_feedback,
        "Instruction": [
            "Revise the plan to address the feedback.",
            "STRICT REQUIREMENT: Ensure 'output_layout' still has exactly 4 keys: 'train', 'test', 'answer', 'sampleSubmission'.",
            "OUTPUT PATH CONVENTION: Use 'prepared/public/' for train/test (public data) and 'prepared/private/' for answer (private data).",
            "Output strictly in JSON using the TaskBlueprint schema."
        ]
    }
    return _log_format(prompt_dict)

def create_data_analyst_prompt(base_context: str, file_tree: str = "") -> str:
    prompt_dict = {
        "Role": "ANALYST SPECIALIST - Data Exploration and Visualization Expert",
        "Goal": "Explore, clean, and visualize data patterns.",
        "Current Working Directory Layout": file_tree,
        "Path Selection Rules": [
            "1. Check the 'Current Working Directory Layout' above.",
            "2. If 'prepared/public/' directory exists (containing train.csv/test.csv), YOU MUST ANALYZE THOSE FILES.",
            "3. Only analyze files in 'raw/' if 'prepared/' is empty or missing.",
            "4. Use relative paths in your code:",
            "   - For prepared data: pd.read_csv('prepared/public/train.csv')",
            "   - For raw data: pd.read_csv('raw/train.csv')",
            "5. The workspace has simplified symlinks:",
            "   - raw/ -> points to actual raw data directory",
            "   - prepared/public/ -> points to actual prepared public data",
            "   - prepared/private/ -> points to actual prepared private data (answers)"
        ],
        "Visualization MANDATORY REQUIREMENTS": [
            "CRITICAL: EVERY visualization MUST have a MEANINGFUL TITLE that describes the chart.",
            "Examples of good titles:",
            "  - 'Temperature Distribution in Training Data'",
            "  - 'Correlation Heatmap: Feature Relationships'",
            "  - 'Bike Rental Count by Season'",
            "  - 'Daily Average Bike Counts Over Time'",
            "",
            "NEVER use generic titles like:",
            "  - 'Plot', 'Figure 1', 'Chart', 'Distribution'",
            "",
            "Title format guidelines:",
            "  - Be specific about what data is shown",
            "  - Mention the key variable or relationship",
            "  - Use clear, descriptive language",
            "  - Keep titles concise (under 80 characters)",
            "",
            "EXAMPLE CODE:",
            "  ```python",
            "  # Good title",
            "  plt.title('Temperature Distribution in Training Data')",
            "  plt.xlabel('Temperature (°C)')",
            "  plt.ylabel('Frequency')",
            "  ",
            "  # Bad title",
            "  plt.title('Distribution')  # Too generic!",
            "  ```",
            "",
            "When creating multi-panel figures:",
            "  - Use plt.suptitle() for the overall figure title",
            "  - Use ax.set_title() for each subplot",
            "  - Make each subplot title specific to what it shows"
        ],
        "Statistical Analysis REQUIREMENTS": [
            "CRITICAL: You MUST PRINT statistical information to help the Summary Agent understand your analysis.",
            "",
            "ALWAYS print these key statistics:",
            "  - For numerical columns: mean, std, min, max, median",
            "  - For categorical columns: value counts, unique values",
            "  - For correlations: correlation matrix or key correlation values",
            "  - For time series: trends, seasonality patterns",
            "",
            "EXAMPLE:",
            "  ```python",
            "  # Print statistics for understanding",
            "  print('Temperature statistics:')",
            "  print(f'Mean: {df[\"temp\"].mean():.2f}')",
            "  print(f'Std: {df[\"temp\"].std():.2f}')",
            "  print(f'Min: {df[\"temp\"].min():.2f}')",
            "  print(f'Max: {df[\"temp\"].max():.2f}')",
            "  print(f'Median: {df[\"temp\"].median():.2f}')",
            "  ",
            "  print('Season distribution:')",
            "  print(df['season'].value_counts())",
            "  ",
            "  # Key correlations",
            "  print('Correlation with count:')",
            "  corr = df.corr()['count'].sort_values(ascending=False)",
            "  print(corr.head())",
            "  ```",
            "",
            "Why this matters:",
            "  - The Summary Agent reads these printed statistics",
            "  - Helps provide detailed, data-driven responses to users",
            "  - Makes visualizations more informative"
        ],
        "Instructions": "Perform EDA using Python. YOU MUST ALWAYS GENERATE AND EXECUTE CODE. Provide solution in JSON with 'thought' and 'code' fields.",
        "Data Context & Schema": base_context,
        "Execution Environment": _get_execution_environment()
    }
    return _log_format(prompt_dict)

def create_intent_router_prompt() -> str:
    prompt_dict = {
        "Role": "Action Router",
        "Goal": "Select the BEST output tag for the user request.",
        "Tags": {
            "<DATA_ANALYSIS_CODE>": "Data exploration, visualization, stats. Use this if the user asks to 'generate a report' but analysis is needed first.",
            "<DATA_PREPARATION_CODE>": "Feature engineering, train/test/answer splitting.",
            "<UPDATE_REPORT>": "Writing analysis notes/EDA logs based on EXISTING analysis results."
        }
    }
    return _log_format(prompt_dict)

def create_explorer_system_prompt() -> str:
    prompt_dict = {
        "Role": "Data Exploration Expert",
        "Goal": "Understand the EXACT structure and format of any data files in the workspace (Tabular, Images, Audio, Text, etc.).",
        "Methods": [
            "Traverse directories and identify file types/extensions.",
            "Detect encodings and separators for text/CSV files.",
            "Inspect metadata (e.g., image dimensions, audio sample rates, text length).",
            "Verify column names, data types, and data consistency."
        ]
    }
    return _log_format(prompt_dict)

def create_explorer_user_prompt(error_msg: str, history: str, base_context: str) -> str:
    prompt_dict = {
        "Status": "Debugging data loading issue.",
        "Initial Data Context & Schema": base_context,
        "Failed Task Error": error_msg,
        "Previous Exploration Logs": history,
        "Instruction": "Propose next inspection step to verify data schema. Respond in the required JSON format."
    }
    return _log_format(prompt_dict)

def create_explorer_fix_prompt(error_msg: str, failed_code: str) -> str:
    prompt_dict = {
        "Status": "The exploration script failed.",
        "Execution Error": error_msg,
        "Failed Code": failed_code,
        "Instruction": "Fix the exploration script. Respond in the same JSON format (thought, code, is_done)."
    }
    return _log_format(prompt_dict)

def create_debugger_system_prompt() -> str:
    prompt_dict = {
        "Role": "Expert Python Debugger with Data Schema Intelligence",
        "Goal": "Fix code errors using comprehensive data context, error logs, and schema information.",
        "Capabilities": [
            "Data-Aware Debugging: Uses file tree structure and data schema to fix path/column errors",
            "Schema Intelligence: Understands data types, column names, and file formats",
            "Loading Guide: Follows correct data loading patterns for different file types",
            "Inter-Agent Communication: Can leverage DataExplorer agent insights for complex schema issues"
        ],
        "Debugging Strategy": [
            "1. Analyze the error message to identify the root cause",
            "2. Check the file structure - verify paths exist and are correct",
            "3. Review data schema - verify column names, types, and formats",
            "4. Use the Data Loading Guide if provided - it contains correct loading patterns",
            "5. Fix paths: Use relative paths like 'raw/file.csv' or 'prepared/public/file.csv'",
            "6. Fix columns: Match exact column names from schema (case-sensitive)",
            "7. Fix types: Ensure data types match the schema (dtypes, parse_dates, etc.)"
        ],
        "Common Data Issues to Handle": {
            "Path Errors": "FileNotFoundError, directory errors -> Use correct relative paths from workspace root",
            "Column Errors": "KeyError, missing columns -> Check schema for exact column names",
            "Type Errors": "dtype errors, parse errors -> Use correct pd.read_csv parameters",
            "Encoding Errors": "Unicode/encoding errors -> Specify correct encoding parameter",
            "Schema Mismatches": "Shape errors, alignment errors -> Verify train/test split consistency"
        }
    }
    return _log_format(prompt_dict)

def create_debugger_user_prompt(summary: str, guide: str, user_msg: str, code: str, error_msg: str) -> str:
    prompt_dict = {
        "Session": "DEBUGGING SESSION WITH ENHANCED DATA CONTEXT",
        "Debugging Progress Summary": summary,
        "Data Context & Loading Guide": guide if guide else "No additional context available",
        "Original Task": user_msg,
        "Failed Code": code,
        "Execution Error": error_msg,
        "Debugging Instructions": [
            "1. Review the Data Context & Loading Guide above - it contains correct file paths and schema",
            "2. Identify the error type: path error, schema error, encoding error, or logic error",
            "3. Fix the code using correct paths from the context (e.g., 'raw/train.csv', 'prepared/public/train.csv')",
            "4. Use correct column names from the schema (case-sensitive)",
            "5. Apply correct loading parameters (encoding, parse_dates, etc.)",
            "6. Provide the COMPLETE fixed code in the 'code' field"
        ],
        "Output Format": "JSON with 'thought' (explanation) and 'code' (complete fixed script) fields"
    }
    return _log_format(prompt_dict)

def create_syntax_error_user_prompt(summary: str, error_msg: str) -> str:
    prompt_dict = {
        "Session": "SYNTAX ERROR FIX",
        "Debugging Progress Summary": summary,
        "Execution Error": error_msg,
        "Instruction": "Fix syntax errors. Provide solution in JSON with 'thought' and 'code' fields."
    }
    return _log_format(prompt_dict)

def create_summarizer_prompt(history_text: str, user_task: str) -> str:
    prompt_dict = {
        "Role": "Debugging Analyst",
        "Task": user_task,
        "Failure History": history_text,
        "Required JSON Fields": {
            "concise_summary": "2-3 sentence overview.",
            "mistakes_identified": "List of specific errors.",
            "next_step_recommendation": "Technical guidance."
        }
    }
    return _log_format(prompt_dict)

def create_final_guide_generator_prompt(logs: str, base_context: str) -> str:
    prompt_dict = {
        "Role": "Data Loading Authority",
        "Initial Context": base_context,
        "Exploration Logs": logs,
        "Goal": "Provide a comprehensive, file-by-file 'Data Loading & Schema Guide' for another model. Each file must have its own specific loading instructions.",
        "CRITICAL Requirements": [
            "You MUST provide file-specific loading instructions.",
            "Each file should have its own entry with: file_path, file_type, suggested_parameters, data_structure, critical_insights.",
            "suggested_parameters must be specific to each file (e.g., different parse_dates for different files).",
            "data_structure should list actual column names and data types for that file.",
            "critical_insights should highlight file-specific issues (missing values, encoding, outliers).",
            "Provide a loading_example showing how to load ALL files with their specific parameters."
        ],
        "Required JSON Fields": {
            "files": "List of FileLoadingInfo objects. Each file gets its own detailed entry with: file_path (relative path), file_type (csv/json/parquet/etc), suggested_parameters (file-specific), data_structure (columns/dtypes/shapes), critical_insights (file-specific issues).",
            "overall_insights": "Cross-file insights: relationships between files, train/test splits, shared schemas, data lineage, or any patterns across multiple files.",
            "loading_example": "A concrete code example showing how to load all files using the suggested parameters. Example: 'train_df = pd.read_csv(\"raw/train.csv\", encoding=\"utf-8\", parse_dates=[\"datetime\"]); test_df = pd.read_csv(\"raw/test.csv\", encoding=\"utf-8\", parse_dates=[\"datetime\"])'"
        },
        "Output Format": "Structured JSON where each file has clear, specific loading instructions that can be directly used by another model."
    }
    return _log_format(prompt_dict)

def create_chat_summarizer_prompt(old_summary: str, last_user_msg: str, last_assistant_res: str) -> str:
    prompt_dict = {
        "Role": "Context Manager",
        "Goal": "Maintain a concise, high-density summary of the conversation history.",
        "Previous Summary": old_summary or "No previous history.",
        "Last Interaction": {
            "User": last_user_msg,
            "Assistant": last_assistant_res
        },
        "Instruction": [
            "Update the summary to include new goals, decisions, or constraints from the last interaction.",
            "Remove redundant fillers (like 'ok', 'confirmed').",
            "Keep it under 300 words.",
            "Focus on the 'Current Task State' and 'User Specific Requirements'."
        ]
    }
    return _log_format(prompt_dict)

def create_blueprint_judge_prompt(user_msg: str) -> str:
    prompt_dict = {
        "Role": "Blueprint Approval Judge",
        "Goal": "Determine if the user is satisfied with the proposed plan or if they want revisions.",
        "User Message": user_msg,
        "Instruction": "Analyze the sentiment and content of the user message. Output strictly in JSON using the BlueprintApproval schema."
    }
    return _log_format(prompt_dict)

def create_eda_summary_prompt(
    user_question: str,
    execution_output: str,
    images_info: List[Dict[str, str]],
    base_context: str
) -> str:
    """
    Prompt for the EDA Summary Agent - summarizes execution results and answers user questions.

    Args:
        user_question: The original user question
        execution_output: stdout from code execution
        images_info: List of dicts with 'url', 'filename', 'description' for each image
        base_context: Data schema and file system context
    """
    # Build image context for the agent
    image_context = ""
    if images_info:
        image_context = "\n## GENERATED VISUALIZATIONS\n\n"
        for i, img in enumerate(images_info):
            filename = img.get('filename', f'plot_{i+1}.png')
            description = img.get('description', 'No description available')
            image_context += f"### Visualization {i+1}: {filename}\n"
            image_context += f"**Description**: {description}\n\n"

    prompt_dict = {
        "Role": "Data Analysis Results Summarizer",
        "Goal": "Analyze the code execution results and provide a clear, helpful response to the user's question.",
        "User Question": user_question,
        "Execution Output": execution_output or "(No output)",
        "Visualizations": image_context.strip() or "(No visualizations generated)",
        "Instructions": [
            "Analyze the execution output and any generated visualizations.",
            "Provide a clear, concise answer to the user's question using Markdown format.",
            "Highlight key insights, patterns, or findings from the analysis.",
            "If visualizations were generated, describe what they show and the key insights from each chart.",
            "Use the image descriptions provided to understand what each visualization displays.",
            "Be specific and data-driven in your response.",
            "If appropriate, suggest next steps or additional analyses.",
            "Format your response in clear Markdown with headings, bullet points, and emphasis where appropriate.",
            "IMPORTANT: Return your response as plain text Markdown, NOT JSON."
        ],
        "Data Context": base_context
    }
    # For EDA summary, we want plain text response, not JSON
    return "# RESPONSE FORMAT\n\nYou MUST respond with plain text Markdown only. Do NOT output JSON.\n\n# TASK\n\n" + _dict_to_str(prompt_dict)

def _log_format(d: Dict) -> str:
    """Format prompt dictionary with universal JSON format requirement."""
    content = _dict_to_str(d)
    return JSON_FORMAT_REQUIREMENT + "\n\n# TASK\n\n" + content

# =============================================================================
# MODEL TRAINING AGENTS
# =============================================================================

def create_model_qa_prompt(task_description: str, rubric: str, user_question: str) -> str:
    """Pure Q&A agent for model training questions."""
    prompt_dict = {
        "Role": "Machine Learning Training Assistant",
        "Goal": "Answer user questions about model training, data preparation, and evaluation.",
        "Task Description": task_description,
        "Evaluation Criteria": rubric if rubric else "No rubric defined yet.",
        "User Question": user_question,
        "Instructions": [
            "Provide clear, actionable answers.",
            "Reference the task description and evaluation criteria.",
            "If asking about code improvements, suggest the <MODEL_CODE_IMPROVEMENT> tag.",
            "Respond in JSON with 'answer' (string) field."
        ],
        "Response Format": {
            "answer": "Your detailed response to the user's question."
        }
    }
    return _log_format(prompt_dict)

def create_problem_refinement_prompt(current_description: str, user_feedback: str) -> str:
    """Agent to improve/refine the problem definition."""
    prompt_dict = {
        "Role": "Problem Definition Specialist",
        "Goal": "Refine and improve the task description based on user feedback.",
        "Current Description": current_description,
        "User Feedback": user_feedback,
        "Instructions": [
            "Analyze the current task description.",
            "Incorporate user feedback to improve clarity, specificity, and completeness.",
            "Ensure the description is actionable for ML agents.",
            "Maintain technical accuracy.",
            "Respond in JSON with 'thought' (analysis) and 'refined_description' (improved description) fields."
        ],
        "Refinement Guidelines": [
            "Add specific success criteria if missing.",
            "Clarify data sources and formats.",
            "Define evaluation metrics explicitly.",
            "Specify constraints and requirements.",
            "Make the problem statement unambiguous."
        ],
        "Response Format": {
            "thought": "Your analysis of what needs improvement.",
            "refined_description": "The improved task description."
        }
    }
    return _log_format(prompt_dict)

def create_rubric_refinement_prompt(current_rubric: str, task_description: str, user_feedback: str) -> str:
    """Agent to improve/refine the evaluation rubric."""
    prompt_dict = {
        "Role": "Evaluation Design Specialist",
        "Goal": "Refine and improve the grading rubric based on user feedback.",
        "Task Description": task_description,
        "Current Rubric": current_rubric,
        "User Feedback": user_feedback,
        "Instructions": [
            "Analyze the current rubric structure and criteria.",
            "Incorporate user feedback to make it more objective and measurable.",
            "Ensure criteria are clear, specific, and gradable.",
            "Maintain proper weight distribution (sum = 1.0).",
            "Respond in JSON with 'thought' (analysis) and 'refined_rubric' (improved rubric) fields."
        ],
        "Refinement Guidelines": [
            "Each criterion should have a clear weight (0.X).",
            "Include specific, measurable requirements.",
            "Provide evaluation guidelines for partial credit.",
            "Ensure coverage of all important aspects.",
            "Make rubric actionable for LLM evaluators."
        ],
        "Response Format": {
            "thought": "Your analysis of what needs improvement.",
            "refined_rubric": "The improved rubric in Markdown format."
        }
    }
    return _log_format(prompt_dict)

def create_model_code_improvement_prompt(current_code: str, task_description: str, rubric: str, user_feedback: str) -> str:
    """Agent to improve model training code."""
    prompt_dict = {
        "Role": "Machine Learning Code Improvement Specialist",
        "Goal": "Improve the model training code based on feedback and rubric.",
        "Task Description": task_description,
        "Evaluation Rubric": rubric if rubric else "No rubric provided.",
        "Current Code": current_code,
        "User Feedback": user_feedback,
        "Instructions": [
            "Analyze the current training code.",
            "Address user feedback (bugs, performance, clarity, etc.).",
            "Align code with rubric requirements.",
            "Follow best practices for ML workflows.",
            "Respond in JSON with 'thought' (analysis), 'improved_code' (complete code), and 'changes' (list of improvements) fields."
        ],
        "Improvement Guidelines": [
            "Fix any bugs or errors.",
            "Improve code structure and readability.",
            "Optimize performance if applicable.",
            "Add helpful comments.",
            "Ensure proper data handling.",
            "Include evaluation metric calculations."
        ],
        "Code Requirements": [
            "Must be complete and executable.",
            "Include necessary imports.",
            "Handle data loading correctly.",
            "Include model training and evaluation.",
            "Save results appropriately."
        ],
        "Response Format": {
            "thought": "Your analysis of what needs improvement.",
            "improved_code": "The complete improved Python code.",
            "changes": ["List of specific improvements made."]
        }
    }
    return _log_format(prompt_dict)
