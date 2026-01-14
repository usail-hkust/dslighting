# web_ui/backend/app/services/chat_logic.py

import re
import json
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from .llm_factory import get_llm
from ..models.llm_formats import ExplorationAction, DataLoadingGuide, FileLoadingInfo, DebugSummary, TaskBlueprint, BlueprintApproval, ChatSummary
from ..prompts.agent_prompts import (
    create_explorer_system_prompt,
    create_explorer_user_prompt, create_explorer_fix_prompt,
    create_final_guide_generator_prompt,
    create_summarizer_prompt,
    create_chat_summarizer_prompt,
    create_blueprint_prompt,
    create_blueprint_refinement_prompt,
    create_blueprint_judge_prompt
)
# ... (middle functions unchanged) ...
async def _update_chat_summary(old_summary: str, user_msg: str, assistant_res: str) -> str:
    """Uses LLM to update the persistent conversation summary."""
    llm = await get_llm()
    prompt = create_chat_summarizer_prompt(old_summary, user_msg, assistant_res)
    try:
        res_model = await llm.call_with_json(prompt, output_model=ChatSummary)
        
        # Format as the user expects (Markdown-like bullet points)
        summary = "**Current Task State:**\n"
        for item in res_model.current_task_state:
            summary += f"- {item}\n"
            
        summary += "\n**User Specific Requirements:**\n"
        for item in res_model.user_specific_requirements:
            summary += f"- {item}\n"
            
        return summary.strip()
    except Exception as e:
        logger.error(f"Failed to update chat summary: {e}")
        return old_summary # Fallback

from dsat.services.sandbox import SandboxService

logger = logging.getLogger(__name__)

async def _generate_task_blueprint(user_msg: str, base_context: str) -> TaskBlueprint:
    """Generates a structured plan/blueprint for the data task."""
    llm = await get_llm()
    prompt = create_blueprint_prompt(user_msg, base_context)
    blueprint = await llm.call_with_json(prompt, output_model=TaskBlueprint)
    return blueprint

async def _refine_task_blueprint(user_feedback: str, old_blueprint: TaskBlueprint, base_context: str) -> TaskBlueprint:
    """Refines an existing blueprint based on user feedback."""
    llm = await get_llm()
    prompt = create_blueprint_refinement_prompt(user_feedback, old_blueprint.model_dump_json(), base_context)
    blueprint = await llm.call_with_json(prompt, output_model=TaskBlueprint)
    return blueprint

async def _judge_blueprint_approval(user_msg: str) -> BlueprintApproval:
    """Uses an LLM agent to judge if the user approved the blueprint."""
    llm = await get_llm()
    prompt = create_blueprint_judge_prompt(user_msg)
    approval = await llm.call_with_json(prompt, output_model=BlueprintApproval)
    return approval

import pandas as pd
# ... (rest of imports) ...
def _verify_prepared_data(sandbox_dir: Path) -> Optional[str]:
    """Basic check to ensure the output directory exists and is not empty."""
    # Check for both old (prepared_data) and new (prepared/public & prepared/private) structures
    prep_dir_old = sandbox_dir / "prepared_data"
    prep_dir_new_public = sandbox_dir / "prepared" / "public"
    prep_dir_new_private = sandbox_dir / "prepared" / "private"

    # Check old structure first (for backwards compatibility)
    if prep_dir_old.exists():
        files = [f for f in prep_dir_old.iterdir() if f.is_file() and not f.name.startswith(".")]
        if files:
            return None  # Old structure is valid

    # Check new structure
    if not (prep_dir_new_public.exists() or prep_dir_new_private.exists()):
        return "CRITICAL: Neither 'prepared_data/' nor 'prepared/public|private/' directories were created."

    # Check if there's at least one file in the new structure
    all_files = []
    if prep_dir_new_public.exists():
        all_files.extend([f for f in prep_dir_new_public.iterdir() if f.is_file() and not f.name.startswith(".")])
    if prep_dir_new_private.exists():
        all_files.extend([f for f in prep_dir_new_private.iterdir() if f.is_file() and not f.name.startswith(".")])

    if not all_files:
        return "CRITICAL: 'prepared/' directory is empty. No files were generated."

    return None  # Success

def _read_eda_context(sandbox_dir: Path, selected_data_view: str = "data") -> str:
    # Determine EDA subdirectory based on data view
    # selected_data_view="data" -> eda/raw/, selected_data_view="prepared_data" -> eda/prepared/
    eda_subdir = "prepared" if selected_data_view == "prepared_data" else "raw"
    eda_dir = sandbox_dir / "eda" / eda_subdir

    if not eda_dir.exists(): return f"No previous EDA results for {selected_data_view}."

    context = []

    # Find all image-txt pairs
    image_files = sorted(eda_dir.rglob("*.png"))
    if image_files:
        context.append(f"## Generated Visualizations ({len(image_files)} plots)")

        for img_path in image_files:
            # Look for corresponding txt file
            txt_path = img_path.with_suffix('.txt')

            img_info = f"\n### {img_path.name}"
            if txt_path.exists():
                try:
                    description = txt_path.read_text().strip()
                    img_info += f"\n**Description**: {description}"
                except Exception as e:
                    img_info += f"\n**Description**: [Error reading: {e}]"
            else:
                img_info += f"\n**Description**: No description available"

            context.append(img_info)

    # Also include general stats if available
    stats_file = eda_dir / "summary.json"
    if stats_file.exists():
        try:
            stats = stats_file.read_text()
            context.append(f"\n## Statistical Summary\n{stats}")
        except Exception:
            pass

    return "\n".join(context) if context else f"No previous statistical context for {selected_data_view}."

async def _summarize_debug_history(history: List[Dict[str, str]], user_task: str, chat_summary: str = "") -> str:
    """Summarizes failed attempts to help the next debugging turn."""
    if not history: return "No previous attempts."
    llm = await get_llm()
    
    history_text = ""
    for i, entry in enumerate(history):
        code_lines = entry['code'].splitlines()
        truncated_code = "\n".join(code_lines[:50]) + ("\n..." if len(code_lines) > 50 else "")
        history_text += f"--- ATTEMPT {i+1} ---\n[CODE]:\n{truncated_code}\n\n[ERROR]:\n{entry['error']}\n\n"
    
    # Inject chat summary into the user task context for the summarizer
    full_context_task = f"Context: {chat_summary}\nTask: {user_task}"
    prompt = create_summarizer_prompt(history_text, full_context_task)
    
    # Using call_with_json for structured summary
    res_model = await llm.call_with_json(prompt, output_model=DebugSummary)
    
    summary = f"{res_model.concise_summary}\n\nKey Mistakes:\n"
    for m in res_model.mistakes_identified:
        summary += f"- {m}\n"
    summary += f"\nRecommendation: {res_model.next_step_recommendation}"
    return summary

async def _run_active_exploration(sandbox: SandboxService, error_msg: str, base_context: str, chat_summary: str = "") -> str:
    """Agentic Data Exploration loop to understand data schema and fix loading issues."""
    llm = await get_llm()
    exploration_history = []
    max_turns = 5
    
    current_exploration_context = "No exploration performed yet."
    
    for turn in range(max_turns):
        # Inject chat summary into the error message context for the explorer
        contextual_error = f"Context: {chat_summary}\nError: {error_msg}"
        user_prompt = create_explorer_user_prompt(contextual_error, current_exploration_context, base_context)
        system_prompt = create_explorer_system_prompt()
        
        # Structured call
        res_model = await llm.call_with_json(user_prompt, output_model=ExplorationAction, system_message=system_prompt)
        if res_model.is_done:
            break

        code = res_model.code.strip()

        # Auto-inject common imports
        auto_imports = """
import os
import pandas as pd
import numpy as np
import json
"""
        enhanced_code = auto_imports + "\n" + code
        res = sandbox.run_script(enhanced_code)

        # Mini-Debug for Explorer (Structured)
        if not res.success:
            fix_prompt = create_explorer_fix_prompt(res.stderr, code)
            res_model = await llm.call_with_json(fix_prompt, output_model=ExplorationAction, system_message=system_prompt)
            code = res_model.code.strip()
            enhanced_code = auto_imports + "\n" + code
            res = sandbox.run_script(enhanced_code)

        obs = f"--- EXPLORATION TURN {turn+1} ---\n[STDOUT]: {res.stdout[:1000]}\n[STDERR]: {res.stderr[:500]}"
        exploration_history.append(obs)
        current_exploration_context = "\n\n".join(exploration_history)

    # Final Stage: Generate the Authoritative Guide (Structured)
    guide_prompt = create_final_guide_generator_prompt(current_exploration_context, base_context)
    guide_model = await llm.call_with_json(guide_prompt, output_model=DataLoadingGuide)

    # Format the guide as a clear, file-by-file loading guide
    guide_text = "## 📋 Data Loading Guide\n\n"

    # Add overall insights first
    if guide_model.overall_insights:
        guide_text += f"### Overall Insights\n{guide_model.overall_insights}\n\n"

    # Add file-specific instructions
    guide_text += "### File-by-File Loading Instructions\n\n"
    for i, file_info in enumerate(guide_model.files, 1):
        guide_text += f"#### {i}. {file_info.file_path}\n\n"
        guide_text += f"**Type**: {file_info.file_type}\n\n"
        guide_text += f"**Structure**: {file_info.data_structure}\n\n"
        guide_text += f"**Loading Parameters**:\n```json\n{json.dumps(file_info.suggested_parameters, indent=2)}\n```\n\n"
        if file_info.critical_insights:
            guide_text += f"**Critical Insights**: {file_info.critical_insights}\n\n"
        guide_text += "---\n\n"

    # Add loading example
    if guide_model.loading_example:
        guide_text += f"### Loading Example Code\n```python\n{guide_model.loading_example}\n```\n"

    return guide_text
