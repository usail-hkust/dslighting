import os
import shutil
import traceback
import yaml
import logging
import asyncio
import uuid
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from ..core.config import DATA_DIR, BENCHMARKS_DIR, BASE_DIR, LOGS_DIR
from ..models.schemas import TaskMetadata
from ..models.llm_formats import ComplianceCheck, CodeResponse
from .llm_factory import get_llm
from dsat.services.data_analyzer import DataAnalyzer
from dsat.services.workspace import WorkspaceService
from dsat.services.sandbox import SandboxService

logger = logging.getLogger(__name__)

# Global tracker
TASK_GENERATION_STATUS = {}

def update_status(task_id: str, status: str, detail: str):
    """Updates in-memory status and writes to description.md for frontend visibility."""
    TASK_GENERATION_STATUS[task_id] = {"status": status, "detail": detail}
    
    # Write to description.md for real-time frontend feedback
    desc_path = BENCHMARKS_DIR / task_id / "description.md"
    os.makedirs(desc_path.parent, exist_ok=True)
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_line = f"- `[{timestamp}]` {detail}\n"
    
    try:
        # If it's a fresh file or placeholder, start with a header
        current_content = desc_path.read_text() if desc_path.exists() else ""
        if "# Task Initialization" not in current_content:
            new_content = f"# Task Initialization: {task_id}\n\n{log_line}"
        else:
            new_content = current_content + log_line
            
        with open(desc_path, "w") as f:
            f.write(new_content)
    except Exception as e:
        logger.error(f"Failed to write status to description: {e}")

def sync_analyze_and_copy(task_id: str, raw_path: Path):
    """Synchronous part of task analysis to be run in a thread."""
    comp_dir = BENCHMARKS_DIR / task_id
    p_pub = DATA_DIR / task_id / "prepared" / "public"
    p_priv = DATA_DIR / task_id / "prepared" / "private"
    os.makedirs(p_pub, exist_ok=True)
    os.makedirs(p_priv, exist_ok=True)
    
    csvs = list(raw_path.glob("*.csv")) or list(raw_path.rglob("*.csv"))
    
    if csvs:
        found_sample = False
        for csv in csvs:
            # 1. Copy everything to public for general access
            shutil.copy(csv, p_pub / csv.name)
            
            # 2. Identify answer file
            if "answer" in csv.name.lower() or "solution" in csv.name.lower():
                shutil.copy(csv, p_priv / "answer.csv")
            
            # 3. Identify sample submission file
            if not found_sample and ("sample" in csv.name.lower() or "submission" in csv.name.lower()):
                shutil.copy(csv, p_pub / "sampleSubmission.csv")
                found_sample = True
        
        # 4. Fallback for answer.csv
        if not (p_priv / "answer.csv").exists():
            # If no answer provided, we use the first CSV as dummy answer (to allow grading initialization)
            shutil.copy(csvs[0], p_priv / "answer.csv")
            
        # 5. Fallback for sampleSubmission.csv (CRITICAL for Agent Run)
        if not (p_pub / "sampleSubmission.csv").exists():
            # Try to create sample from test.csv or any csv
            test_candidates = [c for c in csvs if "test" in c.name.lower()]
            base_for_sample = test_candidates[0] if test_candidates else csvs[0]
            try:
                import pandas as pd
                df = pd.read_csv(base_for_sample, nrows=5)
                # Create a simple 2-column sample if possible, or just copy the whole thing
                df.head(5).to_csv(p_pub / "sampleSubmission.csv", index=False)
                logger.info(f"Generated default sampleSubmission.csv from {base_for_sample.name}")
            except:
                shutil.copy(base_for_sample, p_pub / "sampleSubmission.csv")
        
        # 6. Ensure leaderboard.csv exists in task root (mlebench requirement)
        leaderboard_path = BENCHMARKS_DIR / task_id / "leaderboard.csv"
        if not leaderboard_path.exists():
            # For custom tasks, we use sampleSubmission.csv or answer.csv as a starting leaderboard
            src_for_lb = p_pub / "sampleSubmission.csv"
            if src_for_lb.exists():
                shutil.copy(src_for_lb, leaderboard_path)
                logger.info(f"Created initial leaderboard.csv for {task_id}")

    analyzer = DataAnalyzer()
    data_report = analyzer.analyze_data(p_pub)
    return data_report, p_pub, p_priv, comp_dir

async def _check_compliance_with_llm(data_report: str, user_comment: str = "") -> Dict[str, Any]:
    """
    Asks the LLM if the dataset structure is valid for a competition.
    Returns: {"compliant": bool, "reason": str}
    """
    llm = await get_llm()
    prompt = (
        f"Analyze the following dataset structure for a Machine Learning Competition:\n\n{data_report}\n\n"
        f"**USER CONTEXT/INTENT**: {user_comment}\n\n"
        "**Compliance Rules:**\n"
        "1. MUST have Training Data (`train.csv` or `train/` folder).\n"
        "2. MUST have Test Data (`test.csv` or `test/` folder).\n"
        "3. MUST have Ground Truth (`answer.csv` or `solution.csv`).\n"
        "4. MUST have Submission Template (`sampleSubmission.csv` or `sample_submission.csv`).\n"
        "5. `test` and `sample` must appear consistent (though you can't check rows here, check existence).\n\n"
        "Output JSON ONLY: `{\"compliant\": boolean, \"reason\": \"string\"}`. "
        "If compliant, reason is 'OK'. If not, explain EXACTLY what is missing or wrong."
    )
    try:
        # Use structured output for robust compliance checking
        res_model = await llm.call_with_json(prompt, output_model=ComplianceCheck)
        return res_model.model_dump()
    except Exception as e:
        logger.error(f"Compliance check failed: {e}")
        return {"compliant": False, "reason": f"System error: {str(e)}"}

async def _enforce_compliance_repair(task_id: str, p_pub: Path, p_priv: Path, data_report: str, issue_reason: str, user_comment: str = ""):
    """
    Executes an iterative repair loop to force-generate valid Train/Test/Answer/Sample artifacts.
    Treats existing files as RAW inputs that may need complete re-processing/splitting.
    """
    logger.info(f"Initiating Iterative Repair for {task_id}. Issue: {issue_reason}")
    TASK_GENERATION_STATUS[task_id] = {"status": "processing", "detail": f"Auto-repairing dataset (Iterative)..."}
    
    run_id = f"dsat_repair_{task_id}_{uuid.uuid4().hex[:8]}"
    ws = WorkspaceService(run_id, base_dir=str(LOGS_DIR))
    sandbox = SandboxService(ws, auto_matplotlib=True)  # Enable matplotlib for Web UI visualization
    
    max_retries = 3
    attempt = 0
    feedback_context = ""
    
    try:
        # Link RAW data. We treat everything in p_pub as potential raw input.
        ws.link_data_to_workspace(p_pub)
        
        while attempt < max_retries:
            attempt += 1
            logger.info(f"Repair Attempt {attempt}/{max_retries}")
            
            llm = await get_llm()
            system_prompt = (
                "You are a Senior Data Engineer. Your ONE Goal is to produce 4 standardized artifacts from the provided raw data.\n"
                "\n"
                "### REQUIRED ARTIFACTS (Adapt based on Data Modality):\n"
                "1. **Training Data** (`train`): \n"
                "   - **Tabular**: `train.csv` (Features + Labels)\n"
                "   - **Image**: `train/` directory (e.g., `train/img_01.jpg`) + `train.csv` (filename->label map)\n"
                "   - **Audio**: `train/` directory (e.g., `train/audio_01.wav`) + `train.csv` (filename->label map)\n"
                "   - **NLP/Text**: `train.jsonl` (one JSON object per line) OR `train.csv` (text column)\n"
                "   - **Video/3D**: `train/` directory containing media files\n"
                "2. **Test Data** (`test`):\n"
                "   - **Tabular**: `test.csv` (Features ONLY)\n"
                "   - **Unstructured**: `test/` directory (Raw files to predict, e.g., `test/img_01.jpg`)\n"
                "3. **Ground Truth** (`answer.csv`):\n"
                "   - MUST contain **Test IDs/Filenames** and **Hidden Labels**.\n"
                "   - Format: `filename,label` (for unstructured) or `id,target` (for tabular).\n"
                "4. **Submission Template** (`sampleSubmission.csv`):\n"
                "   - MUST contain **Test IDs/Filenames** matching `test` set 1:1.\n"
                "   - Fill prediction column with defaults (0, empty string, etc).\n"
                "\n"
                "**CRITICAL RULES**: \n"
                "- **Detect Modality**: If input is a folder of images/wavs, KEEP them as folders. Do NOT try to read pixels/audio into a single CSV cell.\n"
                "- **Consistency**: `sampleSubmission.csv` row count MUST equal `test` file count.\n"
                "- Output ONLY Python code."
            )
            
            user_prompt = (
                f"**Data Overview**:\n{data_report}\n\n"
                f"**USER INTENT**: {user_comment}\n\n"
                f"**COMPLIANCE ISSUE**: {issue_reason}\n\n"
                f"**PREVIOUS FEEDBACK**: {feedback_context}\n\n"
                "Write a Python script to fix this. Load the available files, process them (split/clean), and save the 4 required artifacts."
            )
            
            # Use structured output for code generation
            res_model = await llm.call_with_json(user_prompt, output_model=CodeResponse, system_message=system_prompt)
            
            # Extract code, cleaning up markdown if the model included it inside the JSON string
            code = res_model.code.strip()
            if code.startswith("```"):
                code = re.sub(r"^```(?:python|py)?\n", "", code)
                code = re.sub(r"\n```$", "", code)
                code = code.strip()

            if not code:
                feedback_context = "Error: You provided an empty code block."
                continue

            # Auto-inject common imports
            auto_imports = """
import os
import pandas as pd
import numpy as np
import json
"""
            enhanced_code = auto_imports + "\n" + code
            res = sandbox.run_script(enhanced_code)
            
            # --- VALIDATION PHASE ---
            sb_dir = ws.get_path("sandbox_workdir")
            found_artifacts = [f.name for f in sb_dir.iterdir()]
            required = ["train.csv", "test.csv", "sampleSubmission.csv", "answer.csv"]
            missing = [r for r in required if r not in found_artifacts]
            
            if res.success and not missing:
                # SUCCESS! Sync and Break
                logger.info("Repair successful! All artifacts generated.")
                
                # Sync logic
                promoted_items = []
                for item in sb_dir.iterdir():
                    if item.name in required or item.name == "leaderboard.csv":
                        dest_dir = p_priv if item.name == "answer.csv" else p_pub
                        if item.name == "leaderboard.csv": dest_dir = BENCHMARKS_DIR / task_id
                        
                        os.makedirs(dest_dir, exist_ok=True)
                        dest_path = dest_dir / item.name
                        
                        if item.is_dir():
                            if dest_path.exists(): shutil.rmtree(dest_path)
                            shutil.copytree(item, dest_path)
                        else:
                            shutil.copy2(item, dest_path)
                        promoted_items.append(item.name)
                
                # Cleanup garbage in public dir
                for existing in list(p_pub.iterdir()):
                    if existing.name not in promoted_items:
                         if existing.is_file(): os.remove(existing)
                         elif existing.is_dir(): shutil.rmtree(existing)
                         
                return # Done
            
            else:
                # FAILURE - Prepare feedback for next loop
                error_msg = res.stderr[-500:] if res.stderr else "Unknown runtime error"
                feedback_context = (
                    f"Execution Failed or Incomplete.\n"
                    f"Stdout: {res.stdout[-300:]}\n"
                    f"Stderr: {error_msg}\n"
                    f"Missing Artifacts: {missing}\n"
                    "Please fix the code."
                )
                logger.warning(f"Attempt {attempt} failed: {feedback_context}")

        logger.error("Auto-repair failed after max retries.")
        
    except Exception as e:
        logger.error(f"Compliance repair crashed: {e}")
    finally:
        ws.cleanup()

from .rule_agent import generate_grading_rubric

async def analyze_and_register(task_id: str, raw_path: Path, task_comment: str = "", task_mode: str = "standard_ml"):
    """
    Automated data analysis and registration. 
    Supports 'standard_ml' and 'open_ended' modes.
    """
    loop = asyncio.get_event_loop()
    try:
        update_status(task_id, "processing", f"Initializing analysis environment ({task_mode})...")
        
        # Run sync operations in thread pool
        data_report, p_pub, p_priv, comp_dir = await loop.run_in_executor(None, sync_analyze_and_copy, task_id, raw_path)
        
        logger.info(f"Initial raw analysis complete for {task_id}. Waiting for User EDA.")

        # --- METADATA GENERATION ---
        llm = await get_llm()
        update_status(task_id, "processing", "Generating initial task description...")
        
        prompt = f"Analyze this uploaded data:\n{data_report}\n\nUser Comment: {task_comment}\n\nGenerate a preliminary description. If the data is raw/unclear, state that."
        meta = await llm.call_with_json(prompt, output_model=TaskMetadata)
        
        # Save results
        os.makedirs(comp_dir, exist_ok=True)
        
        description_text = f"# {meta.title}\n\n{meta.description}\n\n"
        
        if task_mode == "open_ended":
            description_text += "### 🌟 Open-Ended Task\n"
            description_text += "> This is an open-ended exploration task. Evaluation is based on the Rubric below.\n"
            
            # Generate Rubric
            update_status(task_id, "processing", "Generating grading rubric...")
            rubric_content = await generate_grading_rubric(meta.description)
            with open(comp_dir / "rubric.md", "w") as f:
                f.write(rubric_content)
                
            # Copy generic grade.py
            template_path = BASE_DIR / "dsat" / "templates" / "open_ended" / "grade_template.py"
            if template_path.exists():
                shutil.copy(template_path, comp_dir / "grade.py")
            else:
                logger.error(f"Grade template not found at {template_path}")
                
        else:
            description_text += "### ⚠️ Task Definition Pending\n"
            description_text += "> The dataset has been uploaded but not yet standardized.\n"
            description_text += "> Please use **Copilot EDA Mode** to clean data, define targets, and generate the competition files."
        
        with open(comp_dir / "description.md", "w") as f:
            f.write(description_text)
            
        with open(comp_dir / "report.md", "w") as f:
            f.write(f"# Initial Data Scan: {meta.title}\n\n{data_report}")
            
        # Write config based on mode
        config = {
            "id": task_id,
            "name": meta.title,
            "description": "description.md",
            "competition_type": task_mode,
            "raw_dir": f"{task_id}/raw",
            "public_dir": f"{task_id}/prepared/public",
            "private_dir": f"{task_id}/prepared/private"
        }
        
        if task_mode == "open_ended":
            # For open-ended, we rely on the file-based grade.py we just copied
            # We point to it using the specific import syntax expected by mlebench registry
            config["preparer"] = f"file:{comp_dir}/prepare.py:prepare" # Placeholder, user might need to create this via EDA or we provide dummy
            config["grader"] = {
                "name": "LLMJudge",
                "grade_fn": f"file:{comp_dir}/grade.py:grade"
            }
            # Provide dummy prepare.py if missing so it doesn't crash loading
            if not (comp_dir / "prepare.py").exists():
                with open(comp_dir / "prepare.py", "w") as f:
                    f.write("def prepare(raw, public, private):\n    pass\n")
            
            # Open-ended usually doesn't have strict metric like RMSE
            config["metric"] = "LLM Score"
            
            # Dataset pointers (using raw as placeholder since open-ended might not strictly follow split)
            config["dataset"] = {
                "answers": f"{task_id}/raw/answer.csv", # Placeholder
                "sample_submission": f"{task_id}/raw/sampleSubmission.csv", # Placeholder
                "gold_submission": f"{task_id}/raw/answer.csv" # Placeholder
            }
            
        else:
            # Standard ML
            config["metric"] = meta.metric
            config["task_type"] = meta.task_type
            
        with open(comp_dir / "config.yaml", "w") as f:
            yaml.dump(config, f)
            
        # Ensure leaderboard exists
        if not (comp_dir / "leaderboard.csv").exists():
             with open(comp_dir / "leaderboard.csv", "w") as f:
                f.write("score,teamName\n0.0,Baseline")

        # Register in root config
        root_cfg_path = BASE_DIR / "config.yaml"
        if root_cfg_path.exists():
            with open(root_cfg_path, "r") as f:
                root_cfg = yaml.safe_load(f) or {}
            if "competitions" not in root_cfg:
                root_cfg["competitions"] = []
            
            # Check if exists to update or append
            existing_ids = []
            new_list = []
            
            # Rebuild list to avoid duplicates and update mode
            entry_added = False
            
            for entry in root_cfg["competitions"]:
                eid = entry if isinstance(entry, str) else entry["id"]
                if eid == task_id:
                    # Update this entry
                    if task_mode == "open_ended":
                        new_list.append({"id": task_id, "mode": "open_ended"})
                    else:
                        new_list.append(task_id) # Standard string
                    entry_added = True
                else:
                    new_list.append(entry)
            
            if not entry_added:
                if task_mode == "open_ended":
                    new_list.append({"id": task_id, "mode": "open_ended"})
                else:
                    new_list.append(task_id)
            
            root_cfg["competitions"] = new_list
            
            with open(root_cfg_path, "w") as f:
                yaml.dump(root_cfg, f, sort_keys=False)
            
        update_status(task_id, "completed", "Upload complete. Ready for EDA.")
        
    except Exception as e:
        update_status(task_id, "error", f"Fatal Error: {str(e)}")
        logger.error(f"Analysis failed for {task_id}: {str(e)}")
        traceback.print_exc()
