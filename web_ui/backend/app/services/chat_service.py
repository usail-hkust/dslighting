# web_ui/backend/app/services/chat_service.py

import os
import re
import json
import logging
import shutil
import traceback
import anyio
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..core.config import DATA_DIR, BENCHMARKS_DIR, LOGS_DIR
from ..core.utils import get_active_run_id, transform_report_links
from ..utils.context_manager import truncate_error, truncate_output, format_error_for_agent, MAX_OUTPUT_CHARS, MAX_ERROR_CHARS
from ..prompts.agent_prompts import (
    create_data_prep_prompt,
    create_data_analyst_prompt, create_debugger_system_prompt,
    create_debugger_user_prompt, create_syntax_error_user_prompt,
    create_blueprint_prompt
)
from ..models.llm_formats import (
    CodeResponse, ReportResponse, ChatResponse,
    QAResponse, ProblemRefinementResponse, RubricRefinementResponse, CodeImprovementResponse
)
from .llm_factory import get_llm
from .chat_logic import (
    _read_eda_context, _summarize_debug_history,
    _run_active_exploration, _generate_task_blueprint, _refine_task_blueprint,
    _verify_prepared_data, _judge_blueprint_approval, _update_chat_summary
)
from .agent_dispatcher import AgentDispatcher, get_enhanced_debug_context
from .agent_registry import AgentType
from dsat.services.workspace import WorkspaceService
from dsat.services.sandbox import SandboxService
from dsat.services.data_analyzer import DataAnalyzer

logger = logging.getLogger(__name__)

async def run_chat_pipeline(
    task_id: str,
    user_msg: str,
    chat_status_dict: Dict[str, str],
    updated_blueprint: Optional[Dict[str, Any]] = None,
    selected_data_view: str = "data",
    subtask: Optional[str] = None,
    report_scope: Optional[str] = None,
    custom_prompt: Optional[str] = None
):
    """
    Main chat pipeline with comprehensive error handling to ensure
    user always receives a response, even on failures.
    """
    try:
        return await _run_chat_pipeline_impl(
            task_id,
            user_msg,
            chat_status_dict,
            updated_blueprint,
            selected_data_view,
            subtask,
            report_scope,
            custom_prompt
        )
    except Exception as e:
        # Top-level error handler: ensure user always gets a response
        logger.error(f"❌ Unhandled error in chat pipeline: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")

        # Determine error type and provide helpful message
        error_message = str(e)

        # Categorize error for better user feedback
        if "timeout" in error_message.lower() or "ECONNABORTED" in error_message:
            user_friendly = "❌ **请求超时**：处理时间过长，后端已中止。请尝试简化请求或稍后重试。"
        elif "connection" in error_message.lower() or "ECONNREFUSED" in error_message:
            user_friendly = "❌ **连接失败**：无法连接到后端服务。请检查后端是否正在运行。"
        elif "memory" in error_message.lower():
            user_friendly = "❌ **内存不足**：处理的数据量过大。请尝试处理较小的数据集或简化分析。"
        elif "api" in error_message.lower() or "key" in error_message.lower():
            user_friendly = "❌ **API 错误**：LLM 服务配置问题。请检查 API 密钥配置。"
        else:
            user_friendly = f"❌ **处理失败**：{error_message}\n\n请尝试重新表述您的请求或联系技术支持。"

        # Return error response to user
        return {
            "role": "assistant",
            "content": user_friendly,
            "updated_content": {
                "error": error_message,
                "error_type": type(e).__name__
            }
        }


def collect_run_artifacts(task_name: str, task_id: str) -> tuple[str, str]:
    """
    Collect EDA results and code from sandbox directory.

    Args:
        task_name: Name of the task/subtask (e.g., subtask name or task_id)
        task_id: Main task ID for finding the run directory

    Returns:
        Tuple of (eda_context, code_context) strings
    """
    from pathlib import Path as PathLib

    # Find the run directory
    runs_base = LOGS_DIR  # LOGS_DIR points to /path/to/dslighting/runs
    run_pattern = f"dsat_run_{task_id}_*"

    # If task_name is different from task_id (i.e., it's a subtask)
    if task_name != task_id:
        run_pattern = f"dsat_run_{task_id}_{task_name}_*"

    # Find matching run directories
    matching_dirs = list(runs_base.glob(run_pattern))

    if not matching_dirs:
        logger.warning(f"No run directory found for pattern: {run_pattern}")
        return "", ""

    # Use the most recent run directory
    run_dir = max(matching_dirs, key=lambda p: p.stat().st_mtime)
    logger.info(f"📂 Using run directory: {run_dir}")

    sandbox_path = run_dir / "sandbox"
    if not sandbox_path.exists():
        logger.warning(f"Sandbox directory not found: {sandbox_path}")
        return "", ""

    # Collect EDA results
    eda_context = ""
    eda_dir = sandbox_path / "eda" / "raw"
    if eda_dir.exists():
        logger.info(f"📊 Collecting EDA from: {eda_dir}")
        eda_items = []
        for file in sorted(eda_dir.iterdir()):
            if file.is_file() and not file.name.startswith('.'):
                # For text files, read content
                if file.suffix in ['.txt', '.md']:
                    try:
                        content = file.read_text(encoding='utf-8', errors='ignore')
                        eda_items.append(f"### {file.name}\n{content}\n")
                    except Exception as e:
                        logger.warning(f"Failed to read {file.name}: {e}")
                # For images, just list them
                elif file.suffix in ['.png', '.jpg', '.jpeg', '.gif']:
                    # Get relative path from sandbox for markdown links
                    rel_path = file.relative_to(sandbox_path)
                    eda_items.append(f"### {file.name}\n![{file.stem}]({rel_path})\n")

        if eda_items:
            eda_context = "\n".join(eda_items)
            logger.info(f"✅ Collected {len(eda_items)} EDA artifacts")
    else:
        logger.info(f"📭 No EDA directory found at: {eda_dir}")

    # Collect code history
    code_context = ""
    code_history_dir = sandbox_path / "code_history"
    if code_history_dir.exists():
        logger.info(f"💻 Collecting code history from: {code_history_dir}")
        code_items = []
        for file in sorted(code_history_dir.iterdir()):
            if file.is_file() and file.suffix == '.py':
                try:
                    content = file.read_text(encoding='utf-8', errors='ignore')
                    # Truncate if too long
                    if len(content) > 5000:
                        content = content[:5000] + "\n\n... (truncated)"
                    code_items.append(f"### {file.name}\n```python\n{content}\n```\n")
                except Exception as e:
                    logger.warning(f"Failed to read {file.name}: {e}")

        if code_items:
            code_context = "\n".join(code_items)
            logger.info(f"✅ Collected {len(code_items)} code history files")
    else:
        logger.info(f"📭 No code_history directory found at: {code_history_dir}")

    return eda_context, code_context


async def _run_chat_pipeline_impl(
    task_id: str,
    user_msg: str,
    chat_status_dict: Dict[str, str],
    updated_blueprint: Optional[Dict[str, Any]] = None,
    selected_data_view: str = "data",
    subtask: Optional[str] = None,
    report_scope: Optional[str] = None,
    custom_prompt: Optional[str] = None
):
    """
    Implementation of chat pipeline.
    """
    run_id = get_active_run_id(task_id)
    ws = WorkspaceService(run_id, base_dir=str(LOGS_DIR))
    sandbox = SandboxService(ws, auto_matplotlib=True)  # Enable matplotlib for Web UI visualization
    sandbox_dir = ws.get_path("sandbox_workdir")
    bench_dir = BENCHMARKS_DIR / task_id
    llm = await get_llm()

    current_prompt = ""
    summary_file = sandbox_dir / ".chat_summary.txt"
    chat_summary = summary_file.read_text() if summary_file.exists() else "No previous history."

    # Helper to wrap prompt with context
    def wrap_with_context(latest_msg: str) -> str:
        return f"# CONVERSATION CONTEXT (SUMMARY)\n{chat_summary}\n\n# LATEST USER INPUT\n{latest_msg}"

    # 1. Sync Data - Create simplified symlink structure for frontend users
    # Real data location: data/competitions/{task_id}/raw/ and data/competitions/{task_id}/prepared/
    # Workspace structure:
    #   workspace/
    #   ├── raw/              -> symlink to real raw/
    #   └── prepared/         -> symlink to real prepared/
    #       ├── public/      -> symlink to real public/
    #       └── private/     -> symlink to real private/

    # A. Create 'raw/' symlink in workspace
    real_raw_dir = DATA_DIR / task_id / "raw"
    workspace_raw_link = sandbox_dir / "raw"

    if real_raw_dir.exists():
        # Remove existing file/directory/symlink
        if workspace_raw_link.exists():
            if workspace_raw_link.is_dir() and not workspace_raw_link.is_symlink():
                # It's a real directory, use rmtree
                shutil.rmtree(workspace_raw_link)
            else:
                # It's a file or symlink, use unlink
                workspace_raw_link.unlink()
        os.symlink(real_raw_dir, workspace_raw_link)
        logger.info(f"Created symlink: raw -> {real_raw_dir}")

    # B. Create 'prepared/' symlink structure
    real_prepared_dir = DATA_DIR / task_id / "prepared"
    workspace_prepared_link = sandbox_dir / "prepared"

    if real_prepared_dir.exists():
        # Remove existing file/directory/symlink
        if workspace_prepared_link.exists():
            if workspace_prepared_link.is_dir() and not workspace_prepared_link.is_symlink():
                # It's a real directory, use rmtree
                shutil.rmtree(workspace_prepared_link)
            else:
                # It's a file or symlink, use unlink
                workspace_prepared_link.unlink()
        os.symlink(real_prepared_dir, workspace_prepared_link)
        logger.info(f"Created symlink: prepared -> {real_prepared_dir}")

        # Create prepared/public and prepared/private symlinks
        for subdir in ["public", "private"]:
            real_subdir = real_prepared_dir / subdir
            workspace_subdir_link = sandbox_dir / "prepared" / subdir

            if real_subdir.exists():
                # Remove existing file/directory/symlink
                if workspace_subdir_link.exists():
                    if workspace_subdir_link.is_dir() and not workspace_subdir_link.is_symlink():
                        # It's a real directory, use rmtree
                        shutil.rmtree(workspace_subdir_link)
                    else:
                        # It's a file or symlink, use unlink
                        workspace_subdir_link.unlink()
                # Create symlink (parent 'prepared/' already exists as symlink)
                try:
                    os.symlink(real_subdir, workspace_subdir_link)
                    logger.info(f"Created symlink: prepared/{subdir} -> {real_subdir}")
                except FileExistsError:
                    # Symlink might already exist from previous run
                    if not workspace_subdir_link.is_symlink():
                        # If it's a real directory, log warning
                        logger.warning(f"Cannot create symlink at {workspace_subdir_link}: exists as directory")
                    else:
                        logger.info(f"Symlink already exists: prepared/{subdir} -> {real_subdir}")
                except Exception as e:
                    logger.error(f"Failed to create symlink prepared/{subdir}: {e}")

    # C. Determine which path to analyze
    if selected_data_view == "prepared_data":
        analyze_path = sandbox_dir / "prepared" / "public"
    else:
        analyze_path = sandbox_dir / "raw"

    data_report = DataAnalyzer().analyze_data(analyze_path)

    # Fix the directory name in the report to show simplified paths
    if selected_data_view == "prepared_data":
        data_report = data_report.replace("./\n", "prepared/public/\n")
    else:
        data_report = data_report.replace("./\n", "raw/\n")

    # D. Generate RESTRICTED File Tree for Context
    def _get_sandbox_tree(root: Path) -> str:
        tree_lines = []
        for path in sorted(root.rglob("*")):
            if path.name.startswith("."): continue
            if "env" in path.parts or "__pycache__" in path.parts: continue

            rel_path = path.relative_to(root)

            # Filter based on selected view
            if selected_data_view == "prepared_data":
                # Only show prepared/ and its subdirectories
                if not str(rel_path).startswith("prepared"): continue
            else:
                # Only show raw/
                if not str(rel_path).startswith("raw"): continue
                # Don't show prepared/ in raw mode
                if str(rel_path).startswith("prepared"): continue

            depth = len(rel_path.parts)
            indent = "    " * (depth - 1)
            tree_lines.append(f"{indent}├── {path.name}")
        return "\n".join(tree_lines) if tree_lines else "No files found."

    file_tree = _get_sandbox_tree(sandbox_dir)

    eda_context = _read_eda_context(sandbox_dir, selected_data_view)
    # Read task description for model mode context
    task_description = ""
    desc_path = bench_dir / "description.md"
    if desc_path.exists():
        task_description = desc_path.read_text()

    base_context = f"## DATA SCHEMA ({selected_data_view} view):\n{data_report}\n\n## FILE SYSTEM SNAPSHOT:\n{file_tree}\n\n## EDA CONTEXT:\n{eda_context}"

    # Add task description to context for model mode
    if task_description and "[CHAT_MODE]" in user_msg:
        base_context += f"\n\n## TASK DESCRIPTION:\n{task_description}"

    # 2. Mode Detection - Frontend has already routed to specific modules
    is_prep_mode = "[DATA_PREP_MODE]" in user_msg
    is_eda_mode = "[EDA_MODE]" in user_msg
    is_chat_mode = "[CHAT_MODE]" in user_msg
    is_report_mode = "[REPORT_MODE]" in user_msg

    logger.info(f"Mode detection: is_prep_mode={is_prep_mode}, is_eda_mode={is_eda_mode}, is_chat_mode={is_chat_mode}, is_report_mode={is_report_mode}")

    # State tracking files (only for DATA_PREP_MODE blueprint loop)
    blueprint_file = sandbox_dir / ".pending_blueprint.json"
    turns_file = sandbox_dir / ".blueprint_turns"
    goal_file = sandbox_dir / ".original_goal"

    system_prompt = ""
    current_prompt = ""
    is_prep_task = False

    # Initialize updated_content early to avoid scope issues
    updated_content = {}

    # DATA_PREP_MODE: Blueprint flow
    if is_prep_mode:
        logger.info("Processing DATA_PREP_MODE request")

        # Check if we are in an active blueprint loop
        if blueprint_file.exists():
            is_prep_task = True
            logger.info("Active blueprint loop detected - setting is_prep_task=True")
            try:
                from ..models.llm_formats import TaskBlueprint
                blueprint = TaskBlueprint.model_validate_json(blueprint_file.read_text())
                turns = int(turns_file.read_text()) if turns_file.exists() else 0

                is_confirmed = False
                if updated_blueprint:
                    logger.info("Using user-edited blueprint from frontend.")
                    blueprint = TaskBlueprint.model_validate(updated_blueprint)
                    is_confirmed = True
                else:
                    # Standard confirmation check via Judge Agent
                    chat_status_dict[task_id] = "Judging approval..."
                    approval = await _judge_blueprint_approval(user_msg)
                    is_confirmed = approval.is_approved

                if is_confirmed:
                    logger.info("Blueprint confirmed. Moving to implementation.")
                    manifest_content = blueprint.model_dump_json(indent=2)
                    (sandbox_dir / "manifest.json").write_text(manifest_content)

                    original_goal = goal_file.read_text() if goal_file.exists() else user_msg
                    system_prompt = create_data_prep_prompt(base_context, manifest_content)
                    current_prompt = f"# TASK DESCRIPTION\n{original_goal}\n\n# USER CONFIRMATION/FEEDBACK\n{user_msg}"

                    blueprint_file.unlink()
                    if turns_file.exists(): turns_file.unlink()
                    if goal_file.exists(): goal_file.unlink()
                elif turns >= 3:
                    logger.warning("Max refinement reached. Forcing implementation.")
                    manifest_content = blueprint.model_dump_json(indent=2)
                    (sandbox_dir / "manifest.json").write_text(manifest_content)

                    original_goal = goal_file.read_text() if goal_file.exists() else user_msg
                    system_prompt = create_data_prep_prompt(base_context, manifest_content)
                    current_prompt = f"# TASK DESCRIPTION\n{original_goal}\n\n# USER FEEDBACK\n{user_msg}"

                    blueprint_file.unlink()
                    if turns_file.exists(): turns_file.unlink()
                    if goal_file.exists(): goal_file.unlink()
                else:
                    # Refinement
                    chat_status_dict[task_id] = f"Refining blueprint (Turn {turns+1})..."
                    blueprint = await _refine_task_blueprint(user_msg, blueprint, base_context)
                    blueprint_file.write_text(blueprint.model_dump_json())
                    turns_file.write_text(str(turns + 1))

                    assistant_res = _format_blueprint_display(blueprint, turns + 1)
                    # Update Summary for next turn
                    new_summary = await _update_chat_summary(chat_summary, user_msg, assistant_res)
                    summary_file.write_text(new_summary)

                    return {
                        "role": "assistant",
                        "content": assistant_res,
                        "updated_content": {"blueprint": blueprint.model_dump()}
                    }
            except Exception as e:
                logger.error(f"Blueprint state error: {traceback.format_exc()}")
                blueprint_file.unlink(missing_ok=True)

        # No active blueprint - generate new one
        if not system_prompt:
            chat_status_dict[task_id] = "Architecting blueprint..."
            from ..models.llm_formats import TaskBlueprint
            blueprint = await _generate_task_blueprint(user_msg, base_context)

            # Initialize State (Save Original Goal)
            blueprint_file.write_text(blueprint.model_dump_json())
            turns_file.write_text("0")
            goal_file.write_text(user_msg)

            return {
                "role": "assistant",
                "content": _format_blueprint_display(blueprint, 0),
                "updated_content": {"blueprint": blueprint.model_dump()}
            }

    # EDA_MODE: Direct code generation (no intent routing needed)
    elif is_eda_mode:
        logger.info("Processing EDA_MODE request - generating analysis code")
        system_prompt = create_data_analyst_prompt(base_context, file_tree)

    # CHAT_MODE: Model training assistant
    elif is_chat_mode:
        logger.info("Processing CHAT_MODE request - model training assistant")

        # Extract assistant_mode if present
        assistant_mode = None
        mode_match = re.search(r'\[ASSISTANT_MODE:(\w+)\]', user_msg)
        if mode_match:
            assistant_mode = mode_match.group(1)
            # Remove the mode tag from the message
            user_msg = re.sub(r'\[ASSISTANT_MODE:\w+\]\s*', '', user_msg)
            logger.info(f"🎯 Detected assistant mode: {assistant_mode}")

        # Import model training agents
        from app.prompts.agent_prompts import (
            create_model_qa_prompt,
            create_problem_refinement_prompt,
            create_rubric_refinement_prompt,
            create_model_code_improvement_prompt
        )

        # Load task description and rubric for context
        task_desc_path = DATA_DIR / task_id / "description.md"
        rubric_path = DATA_DIR / task_id / "rubric.md"

        task_description = task_desc_path.read_text(encoding='utf-8') if task_desc_path.exists() else ""
        rubric = rubric_path.read_text(encoding='utf-8') if rubric_path.exists() else ""

        # Get latest model code if available
        model_code_path = sandbox_dir / "code_history" / "model_code_001.py"
        model_code = model_code_path.read_text(encoding='utf-8') if model_code_path.exists() else ""

        # Get artifacts info
        artifacts_dir = sandbox_dir / "artifacts"
        artifacts_info = ""
        if artifacts_dir.exists():
            artifact_files = list(artifacts_dir.iterdir())
            artifacts_info = f"Artifacts directory contains {len(artifact_files)} files."

        # Route to appropriate agent based on mode
        if assistant_mode == "refine_problem":
            # Load current description
            logger.info("📝 Refining problem definition")
            system_prompt = create_problem_refinement_prompt(task_description, user_msg)

        elif assistant_mode == "refine_rubric":
            # Load current rubric
            logger.info("📊 Refining evaluation rubric")
            system_prompt = create_rubric_refinement_prompt(rubric, task_description, user_msg)

        elif assistant_mode == "improve_code":
            # Load current code
            logger.info("💻 Improving model code")
            if not model_code:
                return {
                    "content": "⚠️ **暂无代码可改进**：请先生成模型训练代码，然后再使用此功能。"
                }
            system_prompt = create_model_code_improvement_prompt(model_code, task_description, rubric, user_msg)

        else:  # qa mode or default
            # Q&A assistant
            logger.info("💬 Q&A mode")
            system_prompt = create_model_qa_prompt(task_description, rubric, user_msg)

    # REPORT_MODE: Report generation
    elif is_report_mode:
        logger.info("Processing REPORT_MODE request - generating report")

        # Read current report content (Priority: Sandbox -> Data Dir)
        current_report = ""
        
        # 1. Try Sandbox (Primary)
        sandbox_report_path = sandbox_dir / "report.md"
        if subtask and report_scope != "global":
             sandbox_report_path = sandbox_dir / subtask / "report.md"
        
        # 2. Try Data Dir (Fallback/Legacy)
        if report_scope == "global" or not subtask:
            legacy_report_path = DATA_DIR / task_id / "report.md"
        else:
            legacy_report_path = DATA_DIR / task_id / subtask / "report.md"

        if sandbox_report_path.exists():
            current_report = sandbox_report_path.read_text(encoding='utf-8')
            logger.info(f"Found existing report in Sandbox with {len(current_report)} characters")
        elif legacy_report_path.exists():
            current_report = legacy_report_path.read_text(encoding='utf-8')
            logger.info(f"Found existing report in Data Dir (Legacy) with {len(current_report)} characters")
        else:
            logger.info(f"No existing report found.")

        # ------------------------------------------------------------------
        # SMART PATCHING LOGIC
        # ------------------------------------------------------------------
        
        # 1. Parse sections if report exists
        sections = {}
        section_order = []
        if current_report:
            # Split by headers (## or ###)
            # Regex captures the header line and the following content until next header
            # Note: This is a simplified parser. It assumes standard Markdown headers.
            # We use a lookahead to split but keep delimiters
            
            # Find all headers (## or ###)
            # We capture the header title to use as key
            
            last_pos = 0
            last_header = "PREAMBLE"
            
            for match in header_pattern.finditer(current_report):
                # Content before this header belongs to previous header
                content = current_report[last_pos:match.start()].strip()
                if content or last_header == "PREAMBLE":
                    sections[last_header] = content
                    section_order.append(last_header)
                
                # Update current header
                level = match.group(1)
                title = match.group(2).strip()
                last_header = f"{level} {title}"
                last_pos = match.start()
                
            # Add the last section
            if last_pos < len(current_report):
                sections[last_header] = current_report[last_pos:]
                section_order.append(last_header)
                
        # 2. Determine Intent (Global vs Local)
        target_section = "GLOBAL"
        if current_report and len(sections) > 1:
            # Ask LLM which section the user wants to modify
            intent_prompt = f"""
Current Report Sections:
{json.dumps(section_order, indent=2)}

User Request: "{user_msg}"

Identify the SPECIFIC section the user wants to modify. 
If the user wants to modify a specific section, return the exact section header string from the list above.
If the user wants to rewrite the whole report, add a new section, or if it's ambiguous, return "GLOBAL".

Output ONLY the section header string or "GLOBAL". No JSON, no markdown.
"""
            try:
                target_section = await llm.call(intent_prompt)
                target_section = target_section.strip().replace('"', '')
                # Fuzzy match if exact match fails
                if target_section not in sections and target_section != "GLOBAL":
                    # Try to find best match
                    for s in section_order:
                        if target_section.lower() in s.lower() or s.lower() in target_section.lower():
                            target_section = s
                            break
                    else:
                        target_section = "GLOBAL" # Fallback
            except Exception as e:
                logger.warning(f"Intent detection failed: {e}. Falling back to GLOBAL.")
                target_section = "GLOBAL"

        logger.info(f"🎯 Targeted Section for Update: '{target_section}'")

        # 3. Construct Prompt based on Strategy
        if target_section != "GLOBAL" and target_section in sections:
            # LOCAL UPDATE STRATEGY
            logger.info("⚡ Executing LOCAL PATCH strategy")
            
            # Gather EDA and Code context for grounding
            # We reuse the collect_run_artifacts helper
            # If subtask exists, use it; otherwise use task_id for both params
            target_scope_id = subtask if subtask else task_id
            local_eda_context, local_code_context = collect_run_artifacts(target_scope_id, task_id)
            
            section_content = sections[target_section]
            
            # Context is now focused
            system_prompt = "You are a technical editor. Rewrite the provided report section based on user instructions."
            
            current_prompt = f"""
## FULL REPORT CONTEXT (REFERENCE ONLY)
{current_report}

## AVAILABLE ANALYSIS ARTIFACTS (EDA & CODE)
Use these results to ground your writing. You can reference images using their paths (e.g. `![Description](eda/raw/plot.png)`).

### EDA Results
{local_eda_context if local_eda_context else "No EDA results available."}

### Code History
{local_code_context if local_code_context else "No code history available."}

## ORIGINAL SECTION CONTENT (TARGET FOR EDIT)
{section_content}

## USER INSTRUCTION
{user_msg}

## TASK
Rewrite the TARGET section above to satisfy the user's request. 
- You have access to the full report and analysis artifacts. Use them to ensure accuracy.
- If the user asks to add analysis results, pick relevant insights/images from the ARTIFACTS section.
- ONLY output the rewritten content for the target section ({target_section}).
- Keep the header ({target_section}) if appropriate, or modify it if requested.
- Maintain the same markdown format.
"""
            # Mark that we are doing a patch
            chat_status_dict[task_id] = f"Updating section: {target_section}..."
            
        else:
            # GLOBAL STRATEGY (Fallback or New Report)
            logger.info("🌍 Executing GLOBAL REWRITE strategy")
            
            # (Keep existing context gathering logic for global rewrite)
            report_context = base_context
            
            # ... [Code for context gathering same as before] ...
            # Reuse the existing global context gathering logic
            # For brevity in this replacement, I'll assume we re-use the block below or 
            # I need to ensure the `report_context` variable is populated.
            
            # Let's collect context again briefly to be safe (since I'm replacing the block)
            # No subtask specified - collect from main task (simplified for patch)
            main_eda_context, main_code_context = collect_run_artifacts(task_id, task_id)
            report_context += f"\n\n## ANALYSIS RESULTS\n{main_eda_context}\n{main_code_context}"
            
            if current_report:
                report_context += f"\n\n## CURRENT REPORT\n{current_report}"
                
            system_prompt = "Lead Researcher: Generate/Update full technical report."
            current_prompt = f"""
{report_context}

User Instruction: {user_msg}

Return the COMPLETE updated report in Markdown format.
"""
            chat_status_dict[task_id] = "Generating full report..."

        # 4. Execute LLM
        # We use ChatResponse model for simplicity, expecting code/text in response
        try:
            # For local patch, we might not want JSON structure overhead, but to keep pipeline consistent:
            res_model = await llm.call_with_json(
                current_prompt + "\n\nOutput JSON with 'response' field containing the markdown text.", 
                output_model=ChatResponse, 
                system_message=system_prompt
            )
            
            new_content = res_model.response
            thought = res_model.thought
            
            # 5. Apply Patch or Global Update
            final_report_text = ""
            
            if target_section != "GLOBAL" and target_section in sections:
                # LOCAL PATCH
                sections[target_section] = new_content
                
                # Rebuild full report
                for header in section_order:
                    if header == "PREAMBLE":
                        final_report_text += sections[header]
                    else:
                        # Ensure proper spacing and avoid redundant header checks
                        content = sections[header].strip()
                        if not content.startswith("#"):
                             final_report_text += "\n\n" + header + "\n" + content
                        else:
                             final_report_text += "\n\n" + content
                             
                final_report_text = final_report_text.strip()
                completion_msg = f"✅ **章节已更新**\n\n已修改章节：`{target_section}`"
                final_response = f"{thought}\n\n{completion_msg}"
                
            else:
                # GLOBAL REWRITE
                final_report_text = new_content
                completion_msg = "✅ **报告已重新生成**\n\n完整的技术报告已保存。您可以切换到「报告」标签查看详情。"
                final_response = f"{thought}\n\n{completion_msg}"

            # DIRECT SAVE logic (UPDATED: Save to Sandbox Workspace ONLY)
            if report_scope == "global" or not subtask:
                report_save_path = sandbox_dir / "report.md"
            else:
                report_save_path = sandbox_dir / subtask / "report.md"
                
            # Create parent directory if needed
            report_save_path.parent.mkdir(parents=True, exist_ok=True)

            # Write report to file
            with open(report_save_path, "w", encoding="utf-8") as f:
                f.write(final_report_text)

            logger.info(f"✅ Report saved to WORKSPACE: {report_save_path}")

            # Populate updated_content for frontend
            updated_content["report"] = final_report_text
            logger.info(f"📤 REPORT MODE: updated_content['report'] set with {len(final_report_text)} characters")

            # Update Chat Summary (Background)
            async def update_summary_background_report():
                try:
                    new_summary = await _update_chat_summary(chat_summary, user_msg, final_response)
                    summary_file.write_text(new_summary)
                    logger.info("📝 Chat summary updated successfully (background/report)")
                except Exception as e:
                    logger.warning(f"Failed to update chat summary (background/report): {e}")

            asyncio.create_task(update_summary_background_report())

            # Return immediately to prevent double execution/overwrite
            return {
                "role": "assistant",
                "content": transform_report_links(final_response, task_id),
                "updated_content": updated_content
            }
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise e
            
    # Fallback: General assistant
    
    # 3. Debug Detection - Check if this is a debug/fix request BEFORE execution
    # PRIMARY indicators: explicit fix/debug keywords
    primary_debug = (
        "修复" in user_msg or "fix" in user_msg.lower() or
        "调试" in user_msg or "debug" in user_msg.lower() or
        "帮我审查" in user_msg or "审查并优化" in user_msg
    )

    # SECONDARY indicators: code block with error (strong signal)
    secondary_debug = (
        "```" in user_msg and ("错误" in user_msg or "error" in user_msg.lower() or "stderr" in user_msg.lower())
    )

    # TERTIARY indicators: code block without task description (likely fix request)
    has_code_block = "```" in user_msg
    has_task_description = any(word in user_msg for word in [
        "生成", "可视化", "分析", "统计", "图表", "模型", "预测",
        "generate", "visualize", "analyze", "plot", "model", "predict"
    ])

    # Double guarantee: If has code but NO task description, it's likely a fix request
    tertiary_debug = has_code_block and not has_task_description

    is_debug_request = primary_debug or secondary_debug or tertiary_debug

    if is_debug_request:
        logger.info(f"🔧 DEBUG REQUEST DETECTED (primary={primary_debug}, secondary={secondary_debug}, tertiary={tertiary_debug})")

    # Initialize debug history early (needed for debug requests)
    debug_history = []

    # Initialize Agent Dispatcher for inter-agent communication
    # Determine caller agent based on current mode
    if is_prep_mode:
        caller_agent = AgentType.DATA_PREP
    elif is_eda_mode:
        caller_agent = AgentType.ANALYST
    elif is_chat_mode:
        caller_agent = AgentType.ANALYST  # Model training uses analyst capabilities
    elif is_report_mode:
        caller_agent = AgentType.REPORTER
    else:
        caller_agent = AgentType.DATA_EXPLORER  # Default

    dispatcher = AgentDispatcher(sandbox, sandbox_dir, base_context, caller_agent=caller_agent)
    logger.info(f"🤖 Agent Dispatcher initialized with caller: {caller_agent.value}")

    # 4. Execution Logic
    if is_report_mode:
        chat_status_dict[task_id] = "Analyzing data and generating report..."
    elif is_debug_request:
        chat_status_dict[task_id] = "Debugging code..."
    else:
        chat_status_dict[task_id] = "Thinking..."

    # For debug requests, get enhanced data context
    enhanced_data_context = ""
    if is_debug_request:
        logger.info("🔧 Debug request - gathering enhanced data context")
        try:
            # Extract error message if present for context gathering
            error_match = re.search(r'错误信息：\s*```\n?(.*?)\n?```', user_msg, re.DOTALL)
            debug_error = error_match.group(1).strip() if error_match else ""

            # Get enhanced debug context with file tree, schema, and loading guide
            enhanced_data_context = await get_enhanced_debug_context(
                dispatcher,
                debug_error or "No specific error",
                chat_summary
            )
            logger.info("✅ Enhanced data context gathered for debug agent")
        except Exception as e:
            logger.warning(f"⚠️ Failed to gather enhanced context: {e}")
            enhanced_data_context = ""

    # Adjust system prompt for debug requests
    if is_debug_request and is_eda_mode:
        # For debug requests in EDA mode, use debugger prompt with enhanced context
        logger.info("🔧 Debug request detected in EDA mode - using enhanced debugger flow")
        # Extract code and error from user message if present
        debug_code = None
        debug_error = None

        # Try to extract code from markdown blocks
        code_match = re.search(r'```python\n(.*?)\n```', user_msg, re.DOTALL)
        if code_match:
            debug_code = code_match.group(1).strip()

        # Try to extract error message
        error_match = re.search(r'错误信息：\s*```\n?(.*?)\n?```', user_msg, re.DOTALL)
        if error_match:
            debug_error = error_match.group(1).strip()

        if debug_code and debug_error:
            # Direct fix request with code and error
            debug_history.append({"code": debug_code, "error": debug_error})
            summary = await _summarize_debug_history(debug_history, user_msg)
            system_prompt = create_debugger_system_prompt()
            # Include enhanced data context (file tree, schema, loading guide)
            current_prompt = create_debugger_user_prompt(
                summary,
                enhanced_data_context,  # Pass the loading guide and schema info
                user_msg,
                debug_code,
                debug_error
            )
        elif debug_code:
            # Code review request (no error)
            current_prompt = f"""Please review and optimize the following code:

## Current Data Context
{enhanced_data_context}

## Code to Review
```python
{debug_code}
```

Provide feedback on correctness, performance, and potential improvements.
If the code is correct, say so. If there are improvements, provide the optimized code."""
        else:
            # Generic debug request with enhanced context
            current_prompt = f"""{wrap_with_context(user_msg)}

## Enhanced Data Context (File Tree & Schema)
{enhanced_data_context}

Use this information to help debug any data-related issues."""
    elif is_debug_request and is_prep_mode:
        # For debug requests in Prep mode
        logger.info("🔧 Debug request detected in DATA_PREP_MODE - using enhanced debugger flow")
        current_prompt = f"""{wrap_with_context(user_msg)}

## Enhanced Data Context (File Tree & Schema)
{enhanced_data_context}

Use this information to help debug data preparation issues."""
    else:
        # Normal request - use the mode-specific prompt
        current_prompt = current_prompt or wrap_with_context(user_msg)

    # Add universal JSON format reminder for all tasks (simplified, no schema conflicts)
    json_reminder = """

**CRITICAL RESPONSE FORMAT:**
You MUST respond with a valid JSON object ONLY.
- NO markdown code blocks
- NO conversational filler
- Output ONLY the raw JSON object

The system will validate your response against the required schema automatically.
"""
    current_prompt += json_reminder

    final_response = ""
    # Initialize updated_content only if not already set by report mode
    if 'updated_content' not in locals():
        updated_content = {}

    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        logger.info(f"Starting execution turn {retry_count + 1}/{max_retries}")
        try:
            # Normalized check for roles (Case-Insensitive)
            upper_prompt = (system_prompt or "").upper()
            is_code_task = any(kw in upper_prompt for kw in ["SPECIALIST", "ANALYST", "DEBUGGER"])
            is_report_task = any(kw in upper_prompt for kw in ["WRITER", "RESEARCHER"])

            # Check if this is a model training assistant mode request
            if is_chat_mode and assistant_mode:
                logger.info(f"🎯 Processing model training assistant mode: {assistant_mode}")

                # Set status based on assistant mode
                if assistant_mode == "qa":
                    chat_status_dict[task_id] = "Analyzing question..."
                elif assistant_mode == "refine_problem":
                    chat_status_dict[task_id] = "Refining problem definition..."
                elif assistant_mode == "refine_rubric":
                    chat_status_dict[task_id] = "Refining evaluation rubric..."
                elif assistant_mode == "improve_code":
                    chat_status_dict[task_id] = "Analyzing and improving code..."
                else:
                    chat_status_dict[task_id] = "Processing..."

                if assistant_mode == "qa":
                    res_model = await llm.call_with_json(current_prompt, output_model=QAResponse, system_message=system_prompt)
                    final_response = res_model.answer
                    code = None

                elif assistant_mode == "refine_problem":
                    res_model = await llm.call_with_json(current_prompt, output_model=ProblemRefinementResponse, system_message=system_prompt)
                    thought = res_model.thought
                    refined_description = res_model.refined_description

                    # Save the refined description to file
                    task_desc_path = DATA_DIR / task_id / "description.md"
                    task_desc_path.parent.mkdir(parents=True, exist_ok=True)
                    task_desc_path.write_text(refined_description, encoding='utf-8')
                    logger.info(f"✅ Saved refined description to {task_desc_path}")

                    # Update response
                    updated_content["description"] = refined_description
                    final_response = f"{thought}\n\n✅ **问题描述已更新**\n\n改进后的描述已保存。主要改进点：\n{thought}"

                elif assistant_mode == "refine_rubric":
                    res_model = await llm.call_with_json(current_prompt, output_model=RubricRefinementResponse, system_message=system_prompt)
                    thought = res_model.thought
                    refined_rubric = res_model.refined_rubric

                    # Save the refined rubric to file
                    rubric_path = DATA_DIR / task_id / "rubric.md"
                    rubric_path.parent.mkdir(parents=True, exist_ok=True)
                    rubric_path.write_text(refined_rubric, encoding='utf-8')
                    logger.info(f"✅ Saved refined rubric to {rubric_path}")

                    # Update response
                    updated_content["rubric"] = refined_rubric
                    final_response = f"{thought}\n\n✅ **评分标准已更新**\n\n改进后的标准已保存。主要改进点：\n{thought}"

                elif assistant_mode == "improve_code":
                    res_model = await llm.call_with_json(current_prompt, output_model=CodeImprovementResponse, system_message=system_prompt)
                    thought = res_model.thought
                    improved_code = res_model.improved_code
                    changes = res_model.changes

                    # Save the improved code to code_history
                    code_history_dir = sandbox_dir / "code_history"
                    code_history_dir.mkdir(parents=True, exist_ok=True)

                    # Find next available number
                    existing_codes = list(code_history_dir.glob("model_code_*.py"))
                    if existing_codes:
                        numbers = []
                        for f in existing_codes:
                            match = re.search(r'model_code_(\d+)\.py', f.name)
                            if match:
                                numbers.append(int(match.group(1)))
                        next_num = max(numbers) + 1 if numbers else 1
                    else:
                        next_num = 1

                    # Save with metadata
                    model_code_filename = f"model_code_{next_num:03d}.py"
                    model_code_filepath = code_history_dir / model_code_filename

                    import datetime
                    header = f'''# Code Type: MODEL TRAINING (IMPROVED)
# Mode: Code Improvement
# Model: {llm.model_name if hasattr(llm, 'model_name') else 'Unknown'}
# Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Task ID: {task_id}

'''
                    model_code_filepath.write_text(header + improved_code)
                    logger.info(f"✅ Saved improved code to {model_code_filepath}")

                    # Update response
                    updated_content["model_code"] = improved_code
                    updated_content["model_code_path"] = str(model_code_filepath)

                    # Format changes as bullet points
                    changes_text = "\n".join([f"- {c}" for c in changes])
                    final_response = f"{thought}\n\n✅ **代码已改进**\n\n改进内容：\n{changes_text}\n\n```python\n{improved_code}\n```"

                # Break retry loop for assistant modes
                break

            elif is_code_task:
                logger.info("Calling LLM with JSON format (Code)...")
                res_model = await llm.call_with_json(current_prompt, output_model=CodeResponse, system_message=system_prompt)
                thought = res_model.thought
                code = res_model.code.strip()
                final_response = f"{thought}\n\n```python\n{code}\n```"
            elif is_report_task:
                logger.info("Calling LLM with JSON format (Report)...")
                chat_status_dict[task_id] = "Generating report..."
                res_model = await llm.call_with_json(current_prompt, output_model=ReportResponse, system_message=system_prompt)
                thought = res_model.thought
                content = res_model.report_content.strip()
                # Wrap in tags for compatibility with existing parsing logic
                final_response = f"{thought}\n\n✅ **报告已生成**\n\n完整的技术报告已保存。您可以切换到「报告」标签查看详情。\n\n<UPDATE_REPORT>{content}</UPDATE_REPORT>"
                code = None # No code in report task
                logger.info("✅ Report generation complete")
            else:
                logger.info("Calling LLM with JSON format (Chat)...")
                res_model = await llm.call_with_json(current_prompt, output_model=ChatResponse, system_message=system_prompt)
                thought = res_model.thought
                response_text = res_model.response
                code = res_model.code.strip() if res_model.code else None

                # Format response
                if code:
                    final_response = f"{thought}\n\n{response_text}\n\n```python\n{code}\n```"
                else:
                    final_response = f"{thought}\n\n{response_text}"
        except Exception as e:
            logger.error(f"LLM call failed: {traceback.format_exc()}")
            raise e

        # Handle Reporting/Goal updates immediately if present in text
        m_goal = re.search(r"<UPDATE_DESCRIPTION>(.*?)</UPDATE_DESCRIPTION>", final_response, re.DOTALL)
        m_report = re.search(r"<UPDATE_REPORT>(.*?)</UPDATE_REPORT>", final_response, re.DOTALL)

        if m_report:
            chat_status_dict[task_id] = "Saving report..."
            report_text = m_report.group(1).strip()
            logger.info(f"📝 Found UPDATE_REPORT tag with {len(report_text)} characters")
            logger.info(f"📊 Report save parameters: report_scope={report_scope}, subtask={subtask}")

            # Determine save path based on scope
            if report_scope == "global":
                # Global report - always save to task root
                report_save_path = DATA_DIR / task_id / "report.md"
                logger.info(f"💾 Saving GLOBAL report to: {report_save_path}")
            elif subtask:
                # Single mode with subtask - save to subtask directory
                report_save_path = DATA_DIR / task_id / subtask / "report.md"
                logger.info(f"💾 Saving SUBTASK report to: {report_save_path}")
            else:
                # Single mode WITHOUT subtask - this is ambiguous
                # For backwards compatibility, save to task root but with a warning
                report_save_path = DATA_DIR / task_id / "report.md"
                logger.warning(f"⚠️ Single report mode without subtask - saving to: {report_save_path}")
                logger.warning(f"⚠️ This means both 'single' and 'global' will use the same file!")
                logger.warning(f"⚠️ To separate them, please create subtasks first")

            # Create parent directory if needed
            report_save_path.parent.mkdir(parents=True, exist_ok=True)

            # Write report to file
            with open(report_save_path, "w", encoding="utf-8") as f:
                f.write(report_text)

            logger.info(f"✅ Report saved to {report_save_path}")

            # Add to updated_content for frontend callback
            updated_content["report"] = report_text

            # Also add to BENCHMARKS_DIR
            benchmark_report_path = BENCHMARKS_DIR / task_id / "report.md"
            if report_scope != "global" and subtask:
                benchmark_report_path = BENCHMARKS_DIR / task_id / subtask / "report.md"

            benchmark_report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(benchmark_report_path, "w", encoding="utf-8") as f:
                f.write(report_text)

            logger.info(f"✅ Report also saved to benchmark directory: {benchmark_report_path}")

        if m_goal:
            c = m_goal.group(1).strip()
            with open(bench_dir/"description.md", "w") as f: f.write(c)
            updated_content["description"] = c

        if not code:
            if is_code_task:
                error_hint = "CRITICAL: No 'code' field found in your JSON response. Please provide the implementation."
                current_prompt += f"\n\n{error_hint}"
                retry_count += 1
                continue
            elif is_report_task:
                # Report tasks don't need code, just break the loop
                logger.info("✅ Report task complete - no code execution needed")
                break
            else:
                # Non-code tasks (like Q&A) also don't need code
                break

        updated_content["eda_code"] = code

        # For debug requests, skip execution - return the fixed code directly
        if is_debug_request:
            logger.info("✅ Debug request - skipping execution, returning fixed code")

            # Get response_text for debugging (it may not exist in all code paths)
            response_text = locals().get('response_text', '')
            logger.info(f"🔧 Final response type: ChatResponse with code={bool(code)}, response_text length={len(response_text) if response_text else 0}")

            # For debug requests, use the code directly from LLM response
            if code:
                fixed_code = code.strip()
                updated_content["eda_code"] = fixed_code
                logger.info(f"🔧 Using code from LLM response ({len(fixed_code)} chars)")
            else:
                # Fallback: try to extract code from response_text if it contains code block
                code_match = re.search(r'```python\n(.*?)\n```', response_text or "", re.DOTALL)
                if code_match:
                    fixed_code = code_match.group(1).strip()
                    updated_content["eda_code"] = fixed_code
                    logger.info(f"🔧 Extracted code from response_text ({len(fixed_code)} chars)")
                else:
                    logger.warning("⚠️ No code found in debug response!")
                    fixed_code = ""

            # Mark response as debug result for frontend auto-update
            updated_content["is_debug_result"] = True

            # Set success flag
            updated_content["debug_success"] = True

            logger.info(f"🔧 Debug complete: returning fixed code ({len(fixed_code) if fixed_code else 0} chars)")
            break

        # Syntax Check
        try:
            import ast
            ast.parse(code)
        except SyntaxError as e:
            error_msg = f"SyntaxError: {e.msg} at line {e.lineno}"
            logger.warning(f"Syntax error in generated code: {error_msg}")
            debug_history.append({"code": code, "error": error_msg})
            summary = await _summarize_debug_history(debug_history, user_msg)
            system_prompt = create_debugger_system_prompt()
            current_prompt = create_syntax_error_user_prompt(summary, error_msg)
            retry_count += 1
            continue

        # Execution
        logger.info(f"Executing sandbox script (Turn {retry_count+1})...")
        chat_status_dict[task_id] = f"Executing (Attempt {retry_count+1})..."

        verification_error = None

        # Auto-inject common imports and matplotlib auto-save for EDA tasks
        eda_subdir = "prepared" if selected_data_view == "prepared_data" else "raw"
        auto_imports_template = """
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import re
import sys
from io import StringIO

# Counter for generating unique filenames
_plot_counter = [0]
# Store statistical output for descriptions
_statistical_output = []

# Hook print to capture statistical output
_original_print = print
def capture_print(*args, **kwargs):
    output = ' '.join(str(arg) for arg in args)
    _statistical_output.append(output)
    _original_print(*args, **kwargs)

def sanitize_filename(name):
    '''Convert title to safe filename'''
    # Remove special chars, replace spaces with underscores
    clean = re.sub(r'[<>:"/\\\\|?*]', '', name)
    clean = clean.replace(' ', '_').replace('__', '_')
    # Limit length
    return clean[:50] if clean else "plot_{}".format(_plot_counter[0])

def extract_stats_from_execution():
    '''Extract statistical information from captured output'''
    if not _statistical_output:
        return ""

    # Join all output with newlines preserved for better parsing
    all_output = '\\n'.join(_statistical_output)

    # Extract common statistical patterns
    stats_found = []

    # Pattern 1: mean, std, min, max, median with colons (e.g., "mean: 20.23")
    for stat in ['mean', 'std', 'min', 'max', 'median', 'variance']:
        pattern = r'{}\\s*:\\s*([\\-0-9.]+)'.format(stat)
        matches = re.findall(pattern, all_output, re.IGNORECASE)
        if matches:
            stats_found.append("{}: {}".format(stat.capitalize(), ', '.join(matches[:5])))

    # Pattern 2: value pairs like "season: 0.161" or "holiday: -0.008"
    # This captures key-value pairs with numeric values
    value_pairs = re.findall(r'(\\w+)\\s*:\\s*([\\-0-9.]+)', all_output)
    if value_pairs:
        # Group by correlation-like patterns
        corr_pairs = [(k, v) for k, v in value_pairs if abs(float(v)) <= 1.0 and k.lower() not in ['count', 'nunique']]
        if corr_pairs:
            corr_str = ', '.join(["{}={}".format(k, v) for k, v in corr_pairs[:10]])
            stats_found.append("Correlations/coefficients: {}".format(corr_str))

    # Pattern 3: count/nunique patterns
    count_patterns = re.findall(r'(count|nunique)\\s*[:=]\\s*(\\d+)', all_output, re.IGNORECASE)
    if count_patterns:
        count_str = ', '.join(["{}={}".format(k, v) for k, v in count_patterns[:5]])
        stats_found.append("Counts: {}".format(count_str))

    # Pattern 4: percentage patterns (e.g., "25%", "0.25%")
    percentages = re.findall(r'([\\.0-9]+)%?', all_output)
    if percentages:
        stats_found.append("Percentages: {}%".format(', '.join(percentages[:5])))

    # Pattern 5: correlation matrix or mentions
    if 'correlation' in all_output.lower():
        # Look for correlation statements like "correlation between X and Y is 0.5"
        corr_statements = re.findall(r'correlation\\s+(?:between\\s+\\w+\\s+and\\s+\\w+\\s+)?is\\s+([\\-0-9.]+)', all_output, re.IGNORECASE)
        if corr_statements:
            stats_found.append("Correlation values: {}".format(', '.join(corr_statements[:3])))

    # Pattern 6: shape information like "(1000, 10)" or "1000 rows x 10 columns"
    shapes = re.findall(r'\\((\\d+)\\s*,\\s*(\\d+)\\)|(\\d+)\\s+rows?\\s*x\\s*(\\d+)\\s+columns?', all_output)
    if shapes:
        shapes_formatted = []
        for s in shapes[:3]:
            if s[0] and s[1]:
                shapes_formatted.append("({}, {})".format(s[0], s[1]))
            elif s[2] and s[3]:
                shapes_formatted.append("({}, {})".format(s[2], s[3]))
        if shapes_formatted:
            stats_found.append("Data shapes: {}".format(', '.join(shapes_formatted)))

    # Pattern 7: value_counts output patterns (e.g., "1    2685")
    value_counts = re.findall(r'^(\\d+)\\s+(\\d+)$', all_output, re.MULTILINE)
    if len(value_counts) > 0 and len(value_counts) <= 20:
        # Only capture if it looks like value_counts output (small number of entries)
        vc_str = ', '.join(["{}={}".format(k, v) for k, v in value_counts[:6]])
        stats_found.append("Value distribution: {}".format(vc_str))

    return '. '.join(stats_found) if stats_found else ""

def generate_figure_description(fig, index):
    '''Generate detailed description from figure with statistical context'''
    parts = []

    # Get figure title
    title = ""
    if fig._suptitle:
        title = fig._suptitle.get_text()

    # Analyze subplots
    num_subplots = len(fig.axes)
    if num_subplots > 1:
        parts.append("Multi-panel visualization with {} subplots".format(num_subplots))

    # Analyze each subplot
    chart_types = []
    axis_info = []

    for i, ax in enumerate(fig.axes):
        # Get subplot title
        ax_title = ax.get_title()
        if ax_title and ax_title not in title:
            chart_types.append("Subplot {}: {}".format(i + 1, ax_title))

        # Get axis labels
        xlabel = ax.get_xlabel()
        ylabel = ax.get_ylabel()
        if xlabel or ylabel:
            label_parts = []
            if ylabel:
                label_parts.append("Y-axis: {}".format(ylabel))
            if xlabel:
                label_parts.append("X-axis: {}".format(xlabel))
            if label_parts:
                axis_info.append(", ".join(label_parts))

        # Detect chart type by checking content
        if hasattr(ax, 'images') and ax.images:
            chart_types.append("Heatmap or color-coded visualization")
        elif hasattr(ax, 'collections') and ax.collections:
            for col in ax.collections:
                if hasattr(col, 'get_array'):
                    chart_types.append("Scatter plot or contour visualization")
                    break
        elif hasattr(ax, 'patches') and len(ax.patches) > 1:
            chart_types.append("Bar chart or box plot")
        elif hasattr(ax, 'lines') and ax.lines:
            chart_types.append("Line plot or time series")

    # Build description
    if title:
        parts.insert(0, "**{}**".format(title))

    if chart_types:
        parts.append("Chart types: " + "; ".join(chart_types[:3]))

    if axis_info:
        parts.append("Axes: " + "; ".join(axis_info[:2]))

    # Add statistical information if available
    stats = extract_stats_from_execution()
    if stats:
        parts.append("Statistical insights: " + stats)

    return ". ".join(parts) if parts else "Visualization {} - Generated chart".format(index + 1)

def auto_save_figures():
    '''Auto-save all matplotlib figures with intelligent descriptions'''
    import json
    eda_dir = os.path.join(os.getcwd(), 'eda', '{EDA_SUBDIR_VALUE}')
    os.makedirs(eda_dir, exist_ok=True)

    fig_nums = plt.get_fignums()
    if len(fig_nums) > 0:
        for i, fig_id in enumerate(fig_nums):
            fig = plt.figure(fig_id)
            if fig.axes:
                # Generate meaningful filename from title
                title = ""
                if fig._suptitle:
                    title = fig._suptitle.get_text()
                elif len(fig.axes) > 0 and fig.axes[0].get_title():
                    title = fig.axes[0].get_title()

                base_name = sanitize_filename(title) if title else "figure_{}".format(_plot_counter[0])
                filename = "{}.png".format(base_name)
                filepath = os.path.join(eda_dir, filename)

                # Check if filename already exists, add counter if needed
                counter = 0
                while os.path.exists(filepath):
                    counter += 1
                    filename = "{}_{}.png".format(base_name, counter)
                    filepath = os.path.join(eda_dir, filename)

                # Save figure
                fig.savefig(filepath, bbox_inches='tight', dpi=100)

                # Generate detailed description with statistics
                description = generate_figure_description(fig, _plot_counter[0])

                # Save description to txt file
                txt_filename = filename.replace('.png', '.txt')
                txt_filepath = os.path.join(eda_dir, txt_filename)
                with open(txt_filepath, 'w', encoding='utf-8') as f:
                    f.write(description)

                _plot_counter[0] += 1
                plt.close(fig)

# Hook print to capture statistical output during code execution
print = capture_print

_original_show = plt.show
plt.show = auto_save_figures
"""
        # Now format with eda_subdir value (without repr to avoid extra quotes)
        auto_imports = auto_imports_template.replace('{EDA_SUBDIR_VALUE}', eda_subdir)
        enhanced_code = auto_imports + "\n" + code

        # Record existing images before execution to avoid returning historical images
        eda_dir = sandbox_dir / "eda" / eda_subdir
        existing_images = set()
        if eda_dir.exists():
            existing_images = {str(img_path) for img_path in eda_dir.rglob("*.png")}
            logger.info(f"Found {len(existing_images)} existing images before execution")

        # Run synchronous sandbox call in a separate thread to avoid blocking the event loop
        res = await anyio.to_thread.run_sync(sandbox.run_script, enhanced_code)

        # NEW: Integrity Verification for Prep Tasks
        if res.success and is_prep_task:
            verification_error = _verify_prepared_data(sandbox_dir)
            if verification_error:
                logger.warning(f"Data verification failed: {verification_error}")
                res.success = False
                res.stderr = verification_error # Feed back to debugger

        # Find generated images in EDA subdirectory with descriptions
        # Only return NEW images generated in this execution (not historical ones)
        images = []
        if eda_dir.exists():
            # Recursively find all PNGs in eda subdirectory
            all_images = list(eda_dir.rglob("*.png"))
            new_images = [img_path for img_path in all_images if str(img_path) not in existing_images]

            logger.info(f"Total images: {len(all_images)}, New images: {len(new_images)}")

            for img_path in new_images:
                # Calculate relative path from sandbox root for the URL
                # e.g., eda/raw/plot.png -> /outputs/.../sandbox/eda/raw/plot.png
                rel_path = img_path.relative_to(sandbox_dir)
                img_url = f"/outputs/{run_id}/sandbox/{rel_path}"

                # Read corresponding txt description if exists
                txt_path = img_path.with_suffix('.txt')
                description = None
                if txt_path.exists():
                    try:
                        description = txt_path.read_text().strip()
                    except Exception as e:
                        logger.warning(f"Failed to read {txt_path}: {e}")

                # Store as dict with url and description
                images.append({
                    "url": img_url,
                    "description": description or "No description available"
                })

        # Apply intelligent truncation to stdout/stderr to prevent context overflow
        truncated_stdout = truncate_output(res.stdout, "stdout")
        truncated_stderr = truncate_output(res.stderr, "stderr")

        if len(res.stdout) > MAX_OUTPUT_CHARS:
            logger.info(f"stdout truncated from {len(res.stdout)} to {len(truncated_stdout)} chars")
        if len(res.stderr) > MAX_OUTPUT_CHARS:
            logger.info(f"stderr truncated from {len(res.stderr)} to {len(truncated_stderr)} chars")

        updated_content["eda_execution_result"] = {
            "stdout": truncated_stdout,
            "stderr": truncated_stderr,
            "images": images,
            "truncated": len(res.stdout) > MAX_OUTPUT_CHARS or len(res.stderr) > MAX_OUTPUT_CHARS
        }

        # Save code to workspace file
        try:
            code_history_dir = sandbox_dir / "code_history"
            code_history_dir.mkdir(parents=True, exist_ok=True)

            # Determine code type based on mode
            if is_prep_task:
                code_type = "prep"
            elif is_eda_mode:
                code_type = "explore"
            else:
                code_type = "chat"

            # Find next available number
            existing_codes = list(code_history_dir.glob(f"{code_type}_code_*.py"))
            if existing_codes:
                numbers = []
                for f in existing_codes:
                    match = re.search(rf'{code_type}_code_(\d+)\.py', f.name)
                    if match:
                        numbers.append(int(match.group(1)))
                next_num = max(numbers) + 1 if numbers else 1
            else:
                next_num = 1

            # Save with formatted number (e.g., explore_code_001.py)
            code_filename = f"{code_type}_code_{next_num:03d}.py"
            code_filepath = code_history_dir / code_filename

            # Write code with header
            import datetime
            header = f'''# Code Type: {code_type.upper()}
# Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Source: Chat Conversation

'''
            code_filepath.write_text(header + code)
            logger.info(f"💾 Saved chat code to workspace: {code_filepath}")
        except Exception as e:
            logger.warning(f"Failed to save code to workspace: {e}")

        if res.success:
            logger.info("Execution successful.")

            # For ALL modes with execution results, run the Summary Agent to provide better user response
            if updated_content.get("eda_execution_result"):
                try:
                    from ..agents.agent_orchestrator import AgentOrchestrator
                    orchestrator = AgentOrchestrator(llm, task_id)

                    # Extract original user question (remove mode prefix)
                    original_question = user_msg
                    for prefix in ["[EDA_MODE] ", "[DATA_PREP_MODE] ", "[CHAT_MODE] ", "[REPORT_MODE] "]:
                        if original_question.startswith(prefix):
                            original_question = original_question.replace(prefix, "", 1).strip()
                            break

                    # Run summary agent
                    logger.info(f"Calling Summary Agent for all modes. Original question: {original_question[:100]}")
                    summary_response = await orchestrator.run_eda_summary_flow(
                        user_question=original_question,
                        execution_result=updated_content["eda_execution_result"],
                        base_context=base_context,
                        chat_status_dict=chat_status_dict
                    )

                    # Replace the generic response with the summary
                    final_response = summary_response
                    logger.info(f"Summary Agent completed successfully. Response length: {len(final_response)} chars")
                    logger.info(f"First 500 chars of summary: {final_response[:500]}")

                except Exception as e:
                    logger.warning(f"Summary Agent failed, using generic response: {e}")
                    logger.warning(traceback.format_exc())
                    # Keep the original final_response if summary fails
            else:
                logger.info("No execution result available, skipping Summary Agent")

            # Success logic (Metadata extraction using manifest)
            manifest_file = sandbox_dir / "manifest.json"
            if is_prep_task and manifest_file.exists():
                metadata_code = f"""
import pandas as pd
import json
import os
def get_summary():
    with open('manifest.json', 'r') as f:
        manifest = json.load(f)
    files = manifest.get('files', {{}})
    summary = {{}}
    for key, rel_path in files.items():
        if os.path.exists(rel_path) and rel_path.endswith('.csv'):
            df = pd.read_csv(rel_path)
            summary[key] = {{"columns": list(df.columns), "shape": df.shape}}
    print(json.dumps(summary))
get_summary()
"""
                meta_res = await anyio.to_thread.run_sync(sandbox.run_script, metadata_code)
                if meta_res.success:
                    try: updated_content["data_metadata"] = json.loads(meta_res.stdout)
                    except: pass
            break
        else:
            logger.warning("Execution failed. Triggering expert inspection...")

            # Apply intelligent truncation to stderr to prevent context overflow
            truncated_stderr = truncate_error(res.stderr, exc_type=getattr(res, 'exc_type', None))
            logger.info(f"Error truncated from {len(res.stderr)} to {len(truncated_stderr)} chars for agent context")

            # FAILURE -> Feedback loop
            debug_history.append({"code": code, "error": truncated_stderr})

            # Agentic Data Exploration Expert Phase (Now with Context)
            # Only run explorer if it's NOT a verification error (which implies output structure issues, not input data issues)
            data_guide = "No exploration needed for verification errors."
            if not verification_error:
                chat_status_dict[task_id] = "Agentic data exploration..."
                data_guide = await _run_active_exploration(sandbox, truncated_stderr, base_context, chat_summary=chat_summary)

            # Debug Summarizer (Now with Context)
            summary = await _summarize_debug_history(debug_history, user_msg, chat_summary=chat_summary)

            system_prompt = create_debugger_system_prompt()
            # Combine Context + Debug Info for the Final Fixer
            full_debug_context = f"# CONVERSATION CONTEXT\n{chat_summary}\n\n# USER INPUT\n{user_msg}"
            current_prompt = create_debugger_user_prompt(
                summary=summary, guide=data_guide, user_msg=full_debug_context,
                code=code, error_msg=truncated_stderr
            )
            retry_count += 1

    # Remove XML-style tags from final_response (but keep the content)
    display_text = re.sub(r"<.*?>.*?</.*?>", "✅ Action Completed", final_response, flags=re.DOTALL)
    logger.info(f"Generated display_text. Length: {len(display_text)} chars")
    logger.info(f"First 300 chars of display_text: {display_text[:300]}")

    # Safety check: Ensure display_text is not empty
    if not display_text or display_text.strip() == "":
        logger.warning("display_text is empty! Using fallback message.")
        if updated_content.get("eda_execution_result"):
            exec_result = updated_content["eda_execution_result"]
            if exec_result.get("images") and len(exec_result["images"]) > 0:
                display_text = f"✅ **代码执行成功**：已生成 {len(exec_result['images'])} 个可视化图表。请查看「代码执行」标签查看详细信息。"
            elif exec_result.get("success"):
                display_text = "✅ **代码执行成功**：请查看「代码执行」标签查看输出结果。"
            else:
                display_text = "⚠️ **代码执行完成**：请查看「代码执行」标签查看详细信息。"
        elif updated_content.get("prep_complete"):
            display_text = "✅ **数据准备完成**：已生成处理后的数据文件。请查看「数据预览」标签。"
        else:
            display_text = "✅ **操作完成**：请查看相关标签查看结果。"
        logger.info(f"Using fallback display_text: {display_text}")

    # Add completion status message at the end for user feedback
    if is_debug_request:
        completion_message = "\n\n---\n\n✅ **代码修复完成**：修复后的代码已自动保存，您可以在「代码执行」标签中查看并运行。"
        display_text += completion_message
    elif is_prep_task and updated_content.get("prep_complete"):
        # Check what files were generated for a more specific message
        prep_dir = sandbox_dir / "prepared_data"
        prep_dir_new_public = sandbox_dir / "prepared" / "public"
        prep_dir_new_private = sandbox_dir / "prepared" / "private"

        generated_files = []
        if prep_dir.exists():
            generated_files = list(prep_dir.glob("*"))
        if prep_dir_new_public.exists():
            generated_files.extend(list(prep_dir_new_public.glob("*")))
        if prep_dir_new_private.exists():
            generated_files.extend(list(prep_dir_new_private.glob("*")))

        # Filter out directories and hidden files
        generated_files = [f for f in generated_files if f.is_file() and not f.name.startswith(".")]

        if generated_files:
            # Count file types
            file_types = {}
            for f in generated_files:
                ext = f.suffix.lower() if f.suffix else "no_extension"
                file_types[ext] = file_types.get(ext, 0) + 1

            # Create a descriptive message
            type_descriptions = []
            for ext, count in file_types.items():
                if ext == ".csv":
                    type_descriptions.append(f"{count} 个 CSV 文件")
                elif ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]:
                    type_descriptions.append(f"{count} 个图像文件")
                elif ext in [".mp3", ".wav", ".flac", ".aac"]:
                    type_descriptions.append(f"{count} 个音频文件")
                elif ext in [".txt", ".json", ".xml"]:
                    type_descriptions.append(f"{count} 个文本/配置文件")
                elif ext == "no_extension":
                    type_descriptions.append(f"{count} 个无扩展名文件")
                else:
                    type_descriptions.append(f"{count} 个 {ext} 文件")

            files_desc = "、".join(type_descriptions)
            completion_message = f"\n\n---\n\n✅ **数据准备完成**：已生成 {files_desc}。"
        else:
            completion_message = "\n\n---\n\n✅ **数据准备完成**：数据处理完成。"
        display_text += completion_message
    elif updated_content.get("eda_execution_result"):
        exec_result = updated_content["eda_execution_result"]
        if exec_result.get("success"):
            if exec_result.get("images") and len(exec_result["images"]) > 0:
                completion_message = f"\n\n---\n\n✅ **代码执行成功**：已生成 {len(exec_result['images'])} 个可视化图表。"
                display_text += completion_message
            else:
                completion_message = "\n\n---\n\n✅ **代码执行成功**：分析完成，请查看上方输出结果。"
                display_text += completion_message
        elif exec_result.get("stderr"):
            completion_message = "\n\n---\n\n⚠️ **代码执行出错**：请查看错误信息，或使用「AI修复」按钮自动修复。"
            display_text += completion_message

    # FINAL: Update and Save Summary (async background task - don't block response)
    async def update_summary_background():
        try:
            new_summary = await _update_chat_summary(chat_summary, user_msg, display_text)
            summary_file.write_text(new_summary)
            logger.info("📝 Chat summary updated successfully (background)")
        except Exception as e:
            logger.warning(f"Failed to update chat summary (background): {e}")

    # Start background task without awaiting
    asyncio.create_task(update_summary_background())
    logger.info("📝 Chat summary update started in background")

    # Log updated_content for debugging
    logger.info(f"📦 Returning updated_content keys: {list(updated_content.keys())}")
    if "eda_code" in updated_content:
        logger.info(f"  - eda_code: {len(updated_content['eda_code'])} chars")
    if "is_debug_result" in updated_content:
        logger.info(f"  - is_debug_result: {updated_content['is_debug_result']}")
    if "debug_success" in updated_content:
        logger.info(f"  - debug_success: {updated_content['debug_success']}")

    # Include chat_summary in response for frontend persistence
    updated_content["chat_summary"] = chat_summary

    # Debug: Log updated_content before returning
    if "report" in updated_content:
        logger.info(f"✅ FINAL: Returning updated_content with 'report' ({len(updated_content['report'])} characters)")
    else:
        logger.warning(f"⚠️ FINAL: updated_content does NOT contain 'report'. Keys: {list(updated_content.keys())}")

    return {
        "role": "assistant",
        "content": transform_report_links(display_text.strip(), task_id),
        "updated_content": updated_content
    }

def _format_blueprint_display(blueprint: Any, turn: int) -> str:

    header = "### 🏗️ Data Preparation Blueprint" if turn == 0 else f"### 🔄 Refined Blueprint (Turn {turn})"

    

    layout_str = ""

    if hasattr(blueprint, 'output_layout'):

        layout_items = [f"- `{k}`: `{v}`" for k, v in blueprint.output_layout.items()]

        layout_str = "\n**Expected File Layout**:\n" + "\n".join(layout_items)



    features = "\n".join([f"- {p}" for p in blueprint.feature_engineering_plan])



    return f"""{header}

I've analyzed your data and proposed the following plan:



**Modality**: {blueprint.modality}

**Task**: {blueprint.task_type}

**Target**: `{blueprint.target_column_or_label}`

**Split**: {blueprint.splitting_strategy}

{layout_str}



**Feature Engineering**:

{features}



**Rationale**: {blueprint.justification}



---

**Does this look correct?** If yes, please reply with **"Confirmed"** to start implementation. If not, provide your feedback.

"""


