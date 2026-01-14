import asyncio
import sys
import os
import shutil
import subprocess
import zipfile
import json
import logging
import traceback
import re
import time
import aiofiles
import anyio
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(BASE_DIR))

# Import modular components
from .core.config import DATA_DIR, BENCHMARKS_DIR, LOGS_DIR, BASE_DIR
from .core.utils import get_active_run_id, transform_report_links
from .models.schemas import Message, TaskMetadata
from .services.llm_factory import get_llm
from .services.task_service import analyze_and_register, TASK_GENERATION_STATUS
from .services.chat_service import run_chat_pipeline

# Import DSAT modules
from dsat.services.workspace import WorkspaceService
from dsat.services.sandbox import SandboxService
from dsat.services.data_analyzer import DataAnalyzer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="DSLighting Web UI")

# Mount runs directory
app.mount("/outputs", StaticFiles(directory=str(LOGS_DIR)), name="outputs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global trackers
ACTIVE_PROCESSES: Dict[str, subprocess.Popen] = {}
CHAT_STATUS: Dict[str, str] = {}

@app.get("/")
def read_root(): return {"status": "Running"}

@app.get("/workflows")
def list_workflows(): return {"workflows": ["aide", "automind", "dsagent", "data_interpreter", "autokaggle", "aflow", "deepanalyze"]}

@app.get("/models")
def list_models():
    configs_raw = os.getenv("LLM_MODEL_CONFIGS")
    models = []
    if configs_raw:
        try:
            configs = json.loads(configs_raw)
            if isinstance(configs, dict): models = list(configs.keys())
        except Exception: pass
    if not models: models = ["openai/deepseek-ai/DeepSeek-V3.1-Terminus"]
    return {"models": models}

@app.get("/tasks")
def list_tasks():
    if not DATA_DIR.exists(): return {"tasks": []}
    tasks = [d.name for d in DATA_DIR.iterdir() if d.is_dir()]
    return {"tasks": sorted(tasks)}

@app.get("/tasks/{task_id}")
def get_task_details(task_id: str):
    bench_task_dir = BENCHMARKS_DIR / task_id
    if not (DATA_DIR / task_id).exists(): raise HTTPException(404, "Not found")

    # 优先从 DATA_DIR 读取描述（用户编辑的源头）
    data_desc_path = DATA_DIR / task_id / "description.md"
    bench_desc_path = bench_task_dir / "description.md"

    if data_desc_path.exists():
        description = data_desc_path.read_text()
    elif bench_desc_path.exists():
        description = bench_desc_path.read_text()
    else:
        description = f"# {task_id}\n\n*Awaiting generation...*"

    run_id = get_active_run_id(task_id)
    task_dir = LOGS_DIR / run_id

    # Defaults
    report = "# Final Report\n\n*No final report yet.*"
    eda_report = "# EDA Exploration\n\n*No EDA logs yet.*"

    if (bench_task_dir / "report.md").exists(): report = (bench_task_dir / "report.md").read_text()
    ws_report_file = task_dir / "sandbox" / "report" / "eda_report.md"
    if ws_report_file.exists(): eda_report = ws_report_file.read_text()
    elif (bench_task_dir / "eda_report.md").exists(): eda_report = (bench_task_dir / "eda_report.md").read_text()

    # Check if process is still alive, remove from dictionary if dead
    is_running = False
    if task_id in ACTIVE_PROCESSES:
        proc = ACTIVE_PROCESSES[task_id]
        if proc.poll() is None:  # Process is still running
            is_running = True
        else:  # Process has ended
            logger.info(f"Cleaning up finished process for task {task_id}")
            del ACTIVE_PROCESSES[task_id]
    else:
        # Double-check: process might have ended but not been cleaned up
        # Check if there's a recent log file with activity
        log_files = list(LOGS_DIR.glob(f"{task_id}_*.log"))
        if log_files:
            latest_log = max(log_files, key=os.path.getmtime)
            # If log was modified in last 10 seconds, consider it running
            if time.time() - latest_log.stat().st_mtime < 10:
                is_running = True

    return {"id": task_id, "description": description, "report": transform_report_links(report, task_id), "eda_report": transform_report_links(eda_report, task_id), "is_analyzing": (bench_task_dir / ".analyzing").exists(), "is_running": is_running}

@app.post("/tasks/{task_id}/description/update")
async def update_description(task_id: str, payload: Dict[str, str]):
    """Update task description - saves to both DATA_DIR and BENCHMARKS_DIR."""
    try:
        content = payload.get("content", "")

        # Save to DATA_DIR (primary user edit location)
        data_desc_path = DATA_DIR / task_id / "description.md"
        os.makedirs(data_desc_path.parent, exist_ok=True)
        with open(data_desc_path, "w") as f:
            f.write(content)

        # Also save to BENCHMARKS_DIR to keep in sync
        bench_desc_path = BENCHMARKS_DIR / task_id / "description.md"
        os.makedirs(bench_desc_path.parent, exist_ok=True)
        with open(bench_desc_path, "w") as f:
            f.write(content)

        logger.info(f"Updated description for {task_id} in both DATA_DIR and BENCHMARKS_DIR")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Failed to update description: {e}")
        raise HTTPException(500, str(e))

@app.get("/tasks/{task_id}/chat_status")
async def get_chat_status(task_id: str):
    return {"status": CHAT_STATUS.get(task_id, "idle")}

@app.post("/tasks/{task_id}/chat")
async def chat(task_id: str, message: Message):
    if CHAT_STATUS.get(task_id) and CHAT_STATUS.get(task_id) != "idle":
        raise HTTPException(status_code=409, detail="A message is already being processed for this task.")

    CHAT_STATUS[task_id] = "Thinking..."
    try:
        result = await run_chat_pipeline(
            task_id,
            message.content,
            CHAT_STATUS,
            message.updated_blueprint,
            message.selected_data_view,
            message.subtask,
            message.report_scope,
            message.custom_prompt
        )
        return result
    except Exception as e:
        traceback.print_exc()
        return {"role": "assistant", "content": f"**Error**: {str(e)}"}
    finally:
        CHAT_STATUS[task_id] = "idle"

@app.post("/tasks/{task_id}/reset")
async def reset_task(task_id: str):
    try:
        base_p = DATA_DIR / task_id
        raw_p = base_p / "raw"
        pub_p = base_p / "prepared" / "public"
        priv_p = base_p / "prepared" / "private"
        if not raw_p.exists(): raise HTTPException(404, "Raw backup missing.")
        if pub_p.exists(): shutil.rmtree(pub_p)
        if priv_p.exists(): shutil.rmtree(priv_p)
        pub_p.mkdir(parents=True, exist_ok=True)
        priv_p.mkdir(parents=True, exist_ok=True)
        for item in raw_p.iterdir():
            if item.is_dir(): shutil.copytree(item, pub_p / item.name)
            else: shutil.copy2(item, pub_p / item.name)
        return {"status": "reset_successful"}
    except Exception as e: raise HTTPException(500, str(e))

@app.post("/tasks/{task_id}/clear_history")
async def clear_chat_history(task_id: str):
    """清除对话历史和总结文件"""
    try:
        run_id = get_active_run_id(task_id)
        ws = WorkspaceService(run_id, base_dir=str(LOGS_DIR))
        sandbox_dir = ws.get_path("sandbox_workdir")

        # 清除对话总结文件
        summary_file = sandbox_dir / ".chat_summary.txt"
        if summary_file.exists():
            summary_file.unlink()

        logger.info(f"Cleared chat history for task {task_id}")
        return {"status": "cleared"}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/tasks/{task_id}/eda/execute")
async def eda_execute(task_id: str, code: str = Form(...), view: str = Form("data")):
    try:
        run_id = get_active_run_id(task_id)
        ws = WorkspaceService(run_id, base_dir=str(LOGS_DIR))
        sandbox = SandboxService(ws)
        sandbox_dir = ws.get_path("sandbox_workdir")

        # Determine EDA subdirectory based on view
        # view="data" -> eda/raw/, view="prepared_data" -> eda/prepared/
        eda_subdir = "prepared" if view == "prepared_data" else "raw"
        eda_dir = sandbox_dir / "eda" / eda_subdir
        eda_dir.mkdir(parents=True, exist_ok=True)

        # 在代码中添加自动保存matplotlib图片和描述的逻辑
        auto_save_code = f"""
import matplotlib.pyplot as plt
import os

# 保存所有打开的matplotlib图片及描述
_original_show = plt.show
def auto_save_figures():
    eda_dir = os.path.join(os.getcwd(), 'eda', '{eda_subdir}')
    os.makedirs(eda_dir, exist_ok=True)

    # 保存所有未保存的图片
    fig_nums = plt.get_fignums()
    if len(fig_nums) > 0:
        for i, fig_id in enumerate(fig_nums):
            fig = plt.figure(fig_id)
            # 只保存用户显式创建的图片（不只是内部创建的）
            if fig.axes:
                timestamp = __import__('time').time()
                filename = f'plot_{{timestamp}}_{{i}}.png'
                filepath = os.path.join(eda_dir, filename)
                fig.savefig(filepath, bbox_inches='tight', dpi=100)
                plt.close(fig)

                # 自动生成对应的txt描述文件
                txt_filename = filename.replace('.png', '.txt')
                txt_filepath = os.path.join(eda_dir, txt_filename)
                if not os.path.exists(txt_filepath):
                    # 尝试从图表标题提取描述
                    desc = ""
                    if fig._suptitle:
                        desc = fig._suptitle.get_text()
                    elif len(fig.axes) > 0:
                        ax = fig.axes[0]
                        if ax.get_title():
                            desc = ax.get_title()
                        elif ax.get_ylabel():
                            desc = f"{{ax.get_ylabel()}} vs {{ax.get_xlabel()}}"

                    # 如果没有描述，使用默认值
                    if not desc:
                        desc = f"Visualization {{i+1}} - Generated plot"

                    # 保存描述到txt文件
                    with open(txt_filepath, 'w') as f:
                        f.write(desc)

# 覆盖plt.show，自动保存图片
def show_with_save(*args, **kwargs):
    auto_save_figures()

plt.show = show_with_save
"""
        enhanced_code = auto_save_code + "\n" + code

        res = sandbox.run_script(enhanced_code)

        # 查找所有生成的图片及对应的描述文件
        images = []
        for search_dir in [eda_dir, sandbox_dir]:
            if search_dir.exists():
                png_files = list(search_dir.glob("*.png"))
                for p in sorted(png_files, key=os.path.getmtime, reverse=True):
                    rel_path = p.relative_to(LOGS_DIR)
                    img_url = f"/outputs/{rel_path}"

                    # 尝试读取对应的txt描述文件
                    txt_path = p.with_suffix('.txt')
                    description = None
                    if txt_path.exists():
                        try:
                            description = txt_path.read_text().strip()
                        except Exception:
                            pass

                    images.append({
                        "url": img_url,
                        "description": description or "No description available"
                    })

        # 去重并保持顺序
        seen = set()
        unique_images = []
        for img in images:
            img_key = img["url"]
            if img_key not in seen:
                seen.add(img_key)
                unique_images.append(img)

        # Save code to workspace file with timestamp
        code_history_dir = sandbox_dir / "code_history"
        code_history_dir.mkdir(parents=True, exist_ok=True)

        # Determine code type and filename
        code_type = "explore" if view == "data" else "prep"
        timestamp = __import__('time').time()

        # Find next available number
        existing_codes = list(code_history_dir.glob(f"{code_type}_code_*.py"))
        
        # Check for duplicate content in the latest file
        is_duplicate = False
        next_num = 1
        
        if existing_codes:
            # Extract numbers from existing files
            file_map = {}
            for f in existing_codes:
                match = re.search(rf'{code_type}_code_(\d+)\.py', f.name)
                if match:
                    num = int(match.group(1))
                    file_map[num] = f
            
            if file_map:
                latest_num = max(file_map.keys())
                latest_file = file_map[latest_num]
                next_num = latest_num + 1
                
                try:
                    # Read latest file content
                    content = latest_file.read_text(encoding='utf-8')
                    
                    # Robust header stripping: Remove lines starting with specific metadata tags
                    def clean_code(c):
                        lines = c.splitlines()
                        cleaned = []
                        header_done = False
                        for line in lines:
                            # Skip header lines
                            if not header_done and (line.startswith("# Code Type:") or line.startswith("# Generated:") or line.startswith("# View:")):
                                continue
                            # Skip empty lines at the very beginning
                            if not header_done and not line.strip():
                                continue
                            header_done = True
                            cleaned.append(line)
                        return "\n".join(cleaned).strip()

                    stored_body = clean_code(content)
                    new_body = clean_code(code) # Also clean the input code just in case it has headers
                    
                    if stored_body == new_body:
                        is_duplicate = True
                        code_filename = latest_file.name
                        code_filepath = latest_file
                        logger.info(f"♻️ Code is identical to latest history ({code_filename}). Skipping save.")
                    else:
                        logger.info(f"📝 Code differs from {latest_file.name}. Saving new version.")
                        # Debug: Print difference length to log (avoid printing huge code)
                        # logger.info(f"Old len: {len(stored_body)}, New len: {len(new_body)}")
                except Exception as e:
                    logger.warning(f"Failed to compare code content: {e}")

        if not is_duplicate:
            # Save with formatted number (e.g., explore_code_001.py)
            code_filename = f"{code_type}_code_{next_num:03d}.py"
            code_filepath = code_history_dir / code_filename

            # Write code with header
            header = f'''# Code Type: {code_type.upper()}
# Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# View: {view}

'''
            code_filepath.write_text(header + code)
            logger.info(f"💾 Saved code to workspace: {code_filepath}")

        return {"success": res.success, "stdout": res.stdout, "stderr": res.stderr, "images": unique_images}
    except Exception as e: raise HTTPException(500, str(e))

@app.post("/tasks/{task_id}/model/execute")
async def model_execute(task_id: str, code: str = Form(...)):
    """Execute model training code (alias for EDA execute logic for now)."""
    return await eda_execute(task_id, code, view="data")

@app.get("/tasks/{task_id}/workspace/files")
async def get_workspace_files(task_id: str, view: str = "data"):
    try:
        # Switch to reading from the ACTIVE SANDBOX, not the static storage
        run_id = get_active_run_id(task_id)
        base_path = LOGS_DIR / run_id / "sandbox"

        files = []
        if not base_path.exists():
             return {"files": []}

        # New symlink structure:
        # - raw/ -> symlink to real raw data
        # - prepared/public/ -> symlink to real prepared public data
        # - prepared/private/ -> symlink to real prepared private data
        # - code_history/ -> saved code files

        # Only collect data files (CSV, JSON, etc.) - NOT code history files
        files = []

        if view == "prepared_data":
             # Show prepared/public/ directory
             target_path = base_path / "prepared" / "public"
             if not target_path.exists():
                 # Fallback: check for old prepared_data structure
                 target_path = base_path / "prepared_data"

             if target_path.exists():
                 for item in target_path.iterdir():
                     if not item.name.startswith("."):
                         files.append({"name": item.name, "size": f"{item.stat().st_size/1024:.1f} KB", "is_dir": item.is_dir(), "type": "data"})
        else:
             # Default "data" view: Show raw/ directory
             target_path = base_path / "raw"
             if not target_path.exists():
                 # Fallback: check for old data structure
                 target_path = base_path / "data"

             if target_path.exists():
                 for item in target_path.iterdir():
                     if not item.name.startswith("."):
                         files.append({"name": item.name, "size": f"{item.stat().st_size/1024:.1f} KB", "is_dir": item.is_dir(), "type": "data"})

        return {"files": files}
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return {"files": []}

@app.get("/tasks/{task_id}/workspace/code_history")
async def get_code_history_list(task_id: str):
    """Get list of code files from code_history directory"""
    try:
        run_id = get_active_run_id(task_id)
        base_path = LOGS_DIR / run_id / "sandbox"
        code_history_dir = base_path / "code_history"

        if not code_history_dir.exists():
            return {"files": []}

        files = []
        for item in sorted(code_history_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if not item.name.startswith(".") and item.suffix == ".py":
                files.append({
                    "name": item.name,
                    "size": f"{item.stat().st_size/1024:.1f} KB",
                    "is_dir": item.is_dir()
                })

        return {"files": files}
    except Exception as e:
        logger.error(f"Error listing code history: {e}")
        return {"files": []}

@app.get("/tasks/{task_id}/workspace/code/{filename}")
async def get_code_file(task_id: str, filename: str):
    """Read a code file from code_history directory"""
    try:
        run_id = get_active_run_id(task_id)
        base_path = LOGS_DIR / run_id / "sandbox"
        code_file = base_path / "code_history" / filename

        if not code_file.exists():
            raise HTTPException(404, f"Code file not found: {filename}")

        code_content = code_file.read_text()
        return {"code": code_content, "filename": filename}
    except Exception as e:
        logger.error(f"Error reading code file: {e}")
        raise HTTPException(500, str(e))

@app.get("/tasks/{task_id}/report")
async def get_report(task_id: str, response: Response):
    """Get the report for a task (global report)."""
    # Prevent caching
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    try:
        # Priority 1: Sandbox (Current active run)
        run_id = get_active_run_id(task_id)
        sandbox_report = LOGS_DIR / run_id / "sandbox" / "report.md"
        
        # Priority 2: Data Dir (Legacy/Persistent)
        data_report = DATA_DIR / task_id / "report.md"
        
        if sandbox_report.exists():
            logger.info(f"Serving report from Sandbox: {sandbox_report}")
            return {"report": sandbox_report.read_text(encoding='utf-8')}
        elif data_report.exists():
            logger.info(f"Serving report from Data Dir: {data_report}")
            return {"report": data_report.read_text(encoding='utf-8')}
            
        return {"report": ""}
    except Exception as e:
        logger.error(f"Failed to read report: {e}")
        return {"report": ""}

@app.post("/tasks/{task_id}/report/update")
async def update_report(task_id: str, update: Dict[str, Any]):
    """Update the global report for a task."""
    try:
        content = update.get("content", "")
        
        # Save to Sandbox (Active Run)
        run_id = get_active_run_id(task_id)
        sandbox_report = LOGS_DIR / run_id / "sandbox" / "report.md"
        os.makedirs(sandbox_report.parent, exist_ok=True)
        sandbox_report.write_text(content, encoding='utf-8')
        
        # Also sync to Data Dir for persistence
        data_report = DATA_DIR / task_id / "report.md"
        os.makedirs(data_report.parent, exist_ok=True)
        data_report.write_text(content, encoding='utf-8')

        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Failed to update report: {e}")
        raise HTTPException(500, str(e))

@app.get("/tasks/{task_id}/subtasks/{subtask_name}/report")
async def get_subtask_report(task_id: str, subtask_name: str, response: Response):
    """Get the report for a specific subtask."""
    # Prevent caching
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    
    try:
        # Priority 1: Sandbox
        run_id = get_active_run_id(task_id)
        sandbox_report = LOGS_DIR / run_id / "sandbox" / subtask_name / "report.md"
        
        # Priority 2: Data Dir
        data_report = DATA_DIR / task_id / subtask_name / "report.md"

        if sandbox_report.exists():
            return {"report": sandbox_report.read_text(encoding='utf-8')}
        elif data_report.exists():
            return {"report": data_report.read_text(encoding='utf-8')}

        return {"report": ""}
    except Exception as e:
        logger.error(f"Failed to read subtask report: {e}")
        return {"report": ""}
    except Exception as e:
        logger.error(f"Failed to read subtask report: {e}")
        return {"report": ""}

@app.post("/tasks/{task_id}/subtasks/{subtask_name}/report")
async def update_subtask_report(task_id: str, subtask_name: str, payload: Dict[str, Any]):
    """Update the report for a specific subtask."""
    try:
        subtask_dir = DATA_DIR / task_id / subtask_name

        if not subtask_dir.exists():
            raise HTTPException(404, f"Subtask '{subtask_name}' not found")

        content = payload.get("content", "")
        is_eda = payload.get("is_eda", False)

        filename = "eda_report.md" if is_eda else "report.md"
        report_path = subtask_dir / filename

        report_path.write_text(content)

        logger.info(f"✅ Saved report for {task_id}/{subtask_name}")

        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update subtask report: {e}")
        raise HTTPException(500, str(e))

@app.get("/tasks/{task_id}/rubric")
async def get_rubric(task_id: str):
    """Get the grading rubric for open-ended tasks."""
    try:
        rubric_path = BENCHMARKS_DIR / task_id / "rubric.md"
        if rubric_path.exists():
            return {"content": rubric_path.read_text()}
        # Fallback to checking data dir in case it was created there
        data_rubric_path = DATA_DIR / task_id / "rubric.md"
        if data_rubric_path.exists():
            return {"content": data_rubric_path.read_text()}
        return {"content": ""}
    except Exception as e:
        logger.error(f"Failed to read rubric: {e}")
        return {"content": ""}

@app.post("/tasks/{task_id}/rubric")
async def update_rubric(task_id: str, payload: Dict[str, str]):
    """Update the grading rubric - saves to both DATA_DIR and BENCHMARKS_DIR."""
    try:
        content = payload.get("content", "")

        # Save to BENCHMARKS_DIR
        bench_path = BENCHMARKS_DIR / task_id / "rubric.md"
        os.makedirs(bench_path.parent, exist_ok=True)
        bench_path.write_text(content)

        # Also save to DATA_DIR to keep in sync
        data_path = DATA_DIR / task_id / "rubric.md"
        os.makedirs(data_path.parent, exist_ok=True)
        data_path.write_text(content)

        logger.info(f"Updated rubric for {task_id} in both DATA_DIR and BENCHMARKS_DIR")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Failed to update rubric: {e}")
        raise HTTPException(500, str(e))

@app.get("/tasks/{task_id}/mode")
async def get_task_mode(task_id: str):
    """Detect if a dataset uses single-task or multi-task mode."""
    try:
        dataset_dir = DATA_DIR / task_id

        if not dataset_dir.exists():
            raise HTTPException(404, f"Dataset {task_id} not found")

        # Check for task_* subdirectories
        task_dirs = list(dataset_dir.glob("task_*"))

        if len(task_dirs) == 0:
            # Single-task mode (legacy)
            return {
                "mode": "single",
                "task_id": task_id,
                "description_path": str(dataset_dir / "description.md"),
                "rubric_path": str(dataset_dir / "rubric.md"),
                "note": "Legacy single-task mode"
            }
        else:
            # Multi-task mode (new feature)
            tasks = []
            for task_dir in sorted(task_dirs):
                if task_dir.is_dir():
                    tasks.append({
                        "name": task_dir.name,
                        "description_path": str(task_dir / "description.md"),
                        "rubric_path": str(task_dir / "rubric.md")
                    })

            return {
                "mode": "multi",
                "task_id": task_id,
                "tasks": tasks,
                "default_task": tasks[0]["name"] if tasks else None,
                "note": "Multi-task mode"
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to detect task mode: {e}", exc_info=True)
        raise HTTPException(500, str(e))

@app.get("/tasks/{task_id}/subtasks")
async def get_subtasks(task_id: str):
    """Get all subtasks for a dataset."""
    try:
        dataset_dir = DATA_DIR / task_id

        if not dataset_dir.exists():
            raise HTTPException(404, f"Dataset {task_id} not found")

        # Get all task_* directories
        task_dirs = sorted([d for d in dataset_dir.glob("task_*") if d.is_dir()])

        subtasks = []
        for task_dir in task_dirs:
            subtask_name = task_dir.name
            description_path = task_dir / "description.md"
            rubric_path = task_dir / "rubric.md"

            # Check if description exists
            description = ""
            if description_path.exists():
                description = description_path.read_text(encoding='utf-8')

            # Check if rubric exists
            rubric = ""
            if rubric_path.exists():
                rubric = rubric_path.read_text(encoding='utf-8')

            subtasks.append({
                "name": subtask_name,
                "description": description[:200] + "..." if len(description) > 200 else description,
                "has_description": description_path.exists(),
                "has_rubric": rubric_path.exists(),
                "description_path": str(description_path),
                "rubric_path": str(rubric_path)
            })

        return {
            "task_id": task_id,
            "subtasks": subtasks,
            "total": len(subtasks)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get subtasks: {e}", exc_info=True)
        raise HTTPException(500, str(e))

@app.post("/tasks/{task_id}/subtasks")
async def create_subtask(task_id: str, payload: Dict[str, Any]):
    """Create a new subtask/workspace."""
    try:
        import os
        import shutil
        from pathlib import Path

        subtask_name = payload.get("name", "").strip()
        copy_description = payload.get("copy_description", False)
        copy_rubric = payload.get("copy_rubric", False)
        from_task = payload.get("from_task", None)

        if not subtask_name:
            raise HTTPException(400, "Subtask name is required")

        # Allow alphanumeric, underscore, hyphen, and Chinese characters
        import re
        if not re.match(r'^[a-zA-Z0-9_\-\u4e00-\u9fa5]+$', subtask_name):
            raise HTTPException(400, "Subtask name must be alphanumeric (underscore, hyphen, and Chinese characters allowed)")

        dataset_dir = DATA_DIR / task_id

        # Check if this is the first subtask being created
        existing_task_dirs = sorted([d for d in dataset_dir.glob("task_*") if d.is_dir()])

        if len(existing_task_dirs) == 0:
            # First subtask! Copy original description and rubric to task_1
            logger.info(f"First subtask creation detected. Copying original files to task_1")

            task_1_dir = dataset_dir / "task_1"
            task_1_dir.mkdir(parents=True, exist_ok=True)

            # Copy description (keep original)
            original_desc = dataset_dir / "description.md"
            if original_desc.exists():
                shutil.copy2(str(original_desc), str(task_1_dir / "description.md"))
                logger.info(f"Copied description.md to task_1/")

            # Copy rubric (keep original)
            original_rubric = dataset_dir / "rubric.md"
            if original_rubric.exists():
                shutil.copy2(str(original_rubric), str(task_1_dir / "rubric.md"))
                logger.info(f"Copied rubric.md to task_1/")

            # Create task_1 directory structure
            task_1_data_dir = task_1_dir / "data"
            task_1_data_dir.mkdir(exist_ok=True)

            # Create symlink to raw data
            raw_source = dataset_dir / "data" / "raw"
            raw_target = task_1_data_dir / "raw"

            if raw_source.exists():
                try:
                    raw_target.symlink_to(os.path.relpath(raw_source, task_1_data_dir))
                    logger.info(f"Created symlink for task_1: {raw_target} -> {raw_source}")
                except Exception as e:
                    logger.warning(f"Failed to create symlink for task_1: {e}")

            # Create other directories for task_1
            (task_1_data_dir / "prepared").mkdir(exist_ok=True)
            (task_1_dir / "workspace").mkdir(exist_ok=True)
            (task_1_dir / "eda").mkdir(exist_ok=True)

            logger.info(f"✅ Created task_1 from original files")

        # Create the new subtask directory
        subtask_dir = dataset_dir / subtask_name
        if subtask_dir.exists():
            raise HTTPException(400, f"Subtask '{subtask_name}' already exists")

        logger.info(f"Creating new subtask: {task_id}/{subtask_name}")

        # Create directory structure
        subtask_dir.mkdir(parents=True, exist_ok=True)

        # Create data directory with symlink to raw data
        data_dir = subtask_dir / "data"
        data_dir.mkdir(exist_ok=True)

        raw_source = dataset_dir / "data" / "raw"
        raw_target = data_dir / "raw"

        if raw_source.exists():
            # Create symlink to share raw data
            try:
                raw_target.symlink_to(os.path.relpath(raw_source, data_dir))
                logger.info(f"Created symlink: {raw_target} -> {raw_source}")
            except Exception as e:
                logger.warning(f"Failed to create symlink, will copy: {e}")
                # Fallback: copy data
                shutil.copytree(raw_source, raw_target)

        # Create prepared directory (empty)
        prepared_dir = data_dir / "prepared"
        prepared_dir.mkdir(exist_ok=True)

        # Create other directories
        (subtask_dir / "workspace").mkdir(exist_ok=True)
        (subtask_dir / "eda").mkdir(exist_ok=True)

        # Determine source task for copying
        if from_task:
            source_dir = dataset_dir / from_task
        else:
            # Default to task_1 if it exists, otherwise use dataset root
            task_1_dir = dataset_dir / "task_1"
            if task_1_dir.exists():
                source_dir = task_1_dir
            else:
                source_dir = dataset_dir

        # Copy description if requested
        if copy_description:
            source_desc = source_dir / "description.md"
            if source_desc.exists():
                shutil.copy2(source_desc, subtask_dir / "description.md")
                logger.info(f"Copied description.md to {subtask_name}")
            else:
                # Create default if source doesn't exist
                (subtask_dir / "description.md").write_text(
                    f"# Task: {subtask_name}\n\n# Task Description\n\nPlease describe the task objectives here.\n",
                    encoding='utf-8'
                )
        else:
            # Create default
            (subtask_dir / "description.md").write_text(
                f"# Task: {subtask_name}\n\n# Task Description\n\nPlease describe the task objectives here.\n",
                encoding='utf-8'
            )

        # Copy rubric if requested
        if copy_rubric:
            source_rubric = source_dir / "rubric.md"
            if source_rubric.exists():
                shutil.copy2(source_rubric, subtask_dir / "rubric.md")
                logger.info(f"Copied rubric.md to {subtask_name}")
            else:
                # Create default if source doesn't exist
                (subtask_dir / "rubric.md").write_text(
                    generate_default_rubric(subtask_name),
                    encoding='utf-8'
                )
        else:
            # Create default
            (subtask_dir / "rubric.md").write_text(
                generate_default_rubric(subtask_name),
                encoding='utf-8'
            )

        logger.info(f"✅ Created subtask: {task_id}/{subtask_name}")

        return {
            "status": "success",
            "subtask_name": subtask_name,
            "path": str(subtask_dir),
            "message": f"Subtask '{subtask_name}' created successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create subtask: {e}", exc_info=True)
        raise HTTPException(500, str(e))

@app.get("/tasks/{task_id}/subtasks/{subtask_name}")
async def get_subtask_details(task_id: str, subtask_name: str):
    """Get description and rubric for a specific subtask."""
    try:
        subtask_dir = DATA_DIR / task_id / subtask_name

        if not subtask_dir.exists():
            raise HTTPException(404, f"Subtask '{subtask_name}' not found")

        description_path = subtask_dir / "description.md"
        rubric_path = subtask_dir / "rubric.md"

        description = ""
        rubric = ""

        if description_path.exists():
            description = description_path.read_text(encoding='utf-8')

        if rubric_path.exists():
            rubric = rubric_path.read_text(encoding='utf-8')

        return {
            "task_id": task_id,
            "subtask_name": subtask_name,
            "description": description,
            "rubric": rubric,
            "has_description": description_path.exists(),
            "has_rubric": rubric_path.exists()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get subtask details: {e}", exc_info=True)
        raise HTTPException(500, str(e))

def generate_default_rubric(task_name: str) -> str:
    """Generate a default rubric template."""
    return f"""# Grading Rubric for {task_name}

## Core Criteria (Total: 1.0)

1. **Problem Understanding & Approach** (Weight: 0.25)
   - [ ] Clear understanding of the problem statement
   - [ ] Appropriate methodology chosen for the task
   - [ ] Reasonable task decomposition (if multi-step)

2. **Data Processing & Preparation** (Weight: 0.25)
   - [ ] Data loaded correctly from specified sources
   - [ ] Appropriate preprocessing applied
   - [ ] Edge cases handled properly

3. **Solution Implementation** (Weight: 0.35)
   - [ ] Solution code is correct and complete
   - [ ] Logical structure and organization
   - [ ] Error handling implemented

4. **Results & Validation** (Weight: 0.15)
   - [ ] Results address the original problem
   - [ ] Outputs are well-formatted and interpretable
   - [ ] Achieved reasonable performance

## Scoring Guidelines
- **Full Credit**: All requirements met with high quality
- **Partial Credit** (50-80%): Some requirements met
- **No Credit** (0%): Requirements not met

## Overall Assessment
After scoring, provide:
- Total Score (0.0 to 1.0)
- Strengths
- Areas for Improvement
"""

@app.get("/tasks/{task_id}/subtasks/{subtask_name}/rubric")
async def get_subtask_rubric(task_id: str, subtask_name: str):
    """Get rubric for a specific subtask."""
    try:
        subtask_dir = DATA_DIR / task_id / subtask_name

        if not subtask_dir.exists():
            raise HTTPException(404, f"Subtask '{subtask_name}' not found")

        rubric_path = subtask_dir / "rubric.md"
        content = ""

        if rubric_path.exists():
            content = rubric_path.read_text(encoding='utf-8')

        return {
            "task_id": task_id,
            "subtask_name": subtask_name,
            "content": content,
            "exists": rubric_path.exists()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get subtask rubric: {e}", exc_info=True)
        raise HTTPException(500, str(e))

@app.post("/tasks/{task_id}/subtasks/{subtask_name}/rubric")
async def save_subtask_rubric(task_id: str, subtask_name: str, payload: Dict[str, Any]):
    """Save rubric for a specific subtask."""
    try:
        subtask_dir = DATA_DIR / task_id / subtask_name

        if not subtask_dir.exists():
            raise HTTPException(404, f"Subtask '{subtask_name}' not found")

        rubric_path = subtask_dir / "rubric.md"
        content = payload.get("content", "")

        rubric_path.write_text(content, encoding='utf-8')

        logger.info(f"✅ Saved rubric for {task_id}/{subtask_name}")

        return {
            "status": "success",
            "message": "Rubric saved successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save subtask rubric: {e}", exc_info=True)
        raise HTTPException(500, str(e))

@app.post("/tasks/{task_id}/subtasks/{subtask_name}/description")
async def save_subtask_description(task_id: str, subtask_name: str, payload: Dict[str, Any]):
    """Save description for a specific subtask."""
    try:
        subtask_dir = DATA_DIR / task_id / subtask_name

        if not subtask_dir.exists():
            raise HTTPException(404, f"Subtask '{subtask_name}' not found")

        description_path = subtask_dir / "description.md"
        content = payload.get("content", "")

        description_path.write_text(content, encoding='utf-8')

        logger.info(f"✅ Saved description for {task_id}/{subtask_name}")

        return {
            "status": "success",
            "message": "Description saved successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save subtask description: {e}", exc_info=True)
        raise HTTPException(500, str(e))

@app.get("/tasks/{task_id}/code-history")
async def get_code_history(task_id: str, task: Optional[str] = None):
    """Get model training code history from code_history directory.

    Args:
        task_id: The dataset/task ID
        task: Optional subtask name for filtering (e.g., "task_1")
    """
    try:
        import re
        from pathlib import Path

        logger.info(f"🔍 Fetching code history for task: {task_id}, subtask: {task}")

        # The actual directory structure is: runs/dsat_run_{task_id}_{task}_*/sandbox/code_history
        # For multi-task mode, include task name in pattern
        if task:
            pattern = f"dsat_run_{task_id}_{task}_*"
        else:
            pattern = f"dsat_run_{task_id}_*"

        logger.info(f"📁 Looking for runs matching: {pattern}")

        run_dirs = []
        for run_dir in LOGS_DIR.glob(pattern):
            if run_dir.is_dir():
                run_dirs.append(run_dir)
                logger.info(f"  Found run directory: {run_dir}")

        if not run_dirs:
            logger.warning(f"  No run directories found for task: {task_id}" + (f", subtask: {task}" if task else ""))

        # Sort by modification time (newest first)
        run_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        code_history_files = []

        # Check each run directory for code_history
        for run_dir in run_dirs:
            # Try both possible locations
            possible_paths = [
                run_dir / "sandbox" / "code_history",
                run_dir / "sandbox_workdir" / "code_history",
            ]

            for code_history_dir in possible_paths:
                logger.info(f"  Checking code_history dir: {code_history_dir}, exists: {code_history_dir.exists()}")

                if code_history_dir.exists():
                    # Find all model_code_*.py files
                    model_files = sorted(code_history_dir.glob("model_code_*.py"), reverse=True)
                    logger.info(f"    Found {len(model_files)} model code files in {code_history_dir}")

                    for model_file in model_files:
                        try:
                            # Extract timestamp from filename or use file modification time
                            match = re.search(r'model_code_(\d+)\.py', model_file.name)
                            if match:
                                file_num = int(match.group(1))
                            else:
                                file_num = 0

                            # Use file modification time as timestamp
                            timestamp = model_file.stat().st_mtime

                            # Read file content
                            content = model_file.read_text(encoding='utf-8')

                            # Extract metadata from header if available
                            summary = f"模型代码 #{file_num:03d}"
                            if "# Mode: Code Improvement" in content:
                                summary = f"改进代码 #{file_num:03d}"

                            code_history_files.append({
                                "filename": model_file.name,
                                "content": content,
                                "summary": summary,
                                "timestamp": timestamp * 1000,  # Convert to milliseconds
                                "file_num": file_num
                            })

                            logger.info(f"      Loaded {model_file.name}: {len(content)} chars")
                        except Exception as e:
                            logger.warning(f"Failed to read code file {model_file}: {e}")

        # Sort by timestamp (newest first) then by file number
        code_history_files.sort(key=lambda x: (x["timestamp"], -x["file_num"]), reverse=True)

        logger.info(f"✅ Returning {len(code_history_files)} code history files for task {task_id}")
        return {"files": code_history_files}

    except Exception as e:
        logger.error(f"Failed to get code history: {e}", exc_info=True)
        return {"files": []}

@app.get("/tasks/{task_id}/debug-paths")
async def debug_paths(task_id: str):
    """Debug endpoint to check file paths."""
    from pathlib import Path

    runs_dir = LOGS_DIR / task_id
    result = {
        "task_id": task_id,
        "logs_dir": str(LOGS_DIR),
        "runs_dir_exists": runs_dir.exists(),
        "runs_dir": str(runs_dir),
        "run_dirs": []
    }

    if runs_dir.exists():
        for run_dir in runs_dir.glob("dsat_run_*"):
            if run_dir.is_dir():
                # Check both possible code_history locations
                code_history_sandbox = run_dir / "sandbox" / "code_history"
                code_history_sandbox_workdir = run_dir / "sandbox_workdir" / "code_history"

                run_info = {
                    "name": run_dir.name,
                    "path": str(run_dir),
                    "code_history_locations": {
                        "sandbox/code_history": {
                            "exists": code_history_sandbox.exists(),
                            "path": str(code_history_sandbox),
                            "model_code_files": [
                                f.name for f in code_history_sandbox.glob("model_code_*.py")
                            ] if code_history_sandbox.exists() else []
                        },
                        "sandbox_workdir/code_history": {
                            "exists": code_history_sandbox_workdir.exists(),
                            "path": str(code_history_sandbox_workdir),
                            "model_code_files": [
                                f.name for f in code_history_sandbox_workdir.glob("model_code_*.py")
                            ] if code_history_sandbox_workdir.exists() else []
                        }
                    }
                }
                result["run_dirs"].append(run_info)

    return result

@app.get("/tasks/{task_id}/code-history/file/{filename}")
async def get_code_history_file(task_id: str, filename: str, task: Optional[str] = None):
    """Get a specific code file from code history.

    Args:
        task_id: The dataset/task ID
        filename: The code filename to load
        task: Optional subtask name for filtering (e.g., "task_1")
    """
    try:
        from pathlib import Path

        logger.info(f"📂 Loading code file: {filename} for task: {task_id}" + (f", subtask: {task}" if task else ""))

        # Find all run directories for this task
        run_dirs = []
        if task:
            pattern = f"dsat_run_{task_id}_{task}_*"
        else:
            pattern = f"dsat_run_{task_id}_*"

        for run_dir in LOGS_DIR.glob(pattern):
            if run_dir.is_dir():
                run_dirs.append(run_dir)

        # Sort by modification time (newest first)
        run_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        # Search for the file in each run directory with both possible locations
        for run_dir in run_dirs:
            possible_paths = [
                run_dir / "sandbox" / "code_history" / filename,
                run_dir / "sandbox_workdir" / "code_history" / filename,
            ]

            for file_path in possible_paths:
                if file_path.exists():
                    content = file_path.read_text(encoding='utf-8')
                    logger.info(f"✅ Found and loaded {filename}: {len(content)} chars from {file_path}")
                    return {"filename": filename, "code": content}

        # If not found in standard locations, try direct path in run root
        for run_dir in run_dirs:
            file_path = run_dir / filename
            if file_path.exists() and file_path.suffix == '.py':
                content = file_path.read_text(encoding='utf-8')
                logger.info(f"✅ Found {filename} in run root: {len(content)} chars")
                return {"filename": filename, "code": content}

        logger.warning(f"❌ File not found: {filename}")
        raise HTTPException(404, f"File not found: {filename}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load code file: {e}", exc_info=True)
        raise HTTPException(500, str(e))

@app.post("/run")
async def run_workflow(
    task_id: str = Form(...),
    workflow: str = Form(...),
    model: str = Form(...),
    data_source: str = Form("raw"),  # New parameter: "raw" or "prepared"
    task: Optional[str] = Form(None)  # Optional subtask name for multi-task mode
):
    """启动工作流训练"""
    try:
        if task_id in ACTIVE_PROCESSES:
            raise HTTPException(400, "Task already running")

        # 准备运行命令
        run_script = BASE_DIR / "run_benchmark.py"
        if not run_script.exists():
            raise HTTPException(404, "run_benchmark.py not found")

        # 构建命令 - 修复参数名称和数据目录
        cmd = [
            sys.executable,
            str(run_script),
            "--workflow", workflow,
            "--benchmark", "mle",
            "--mle-competitions", task_id,
            "--mle-data-dir", str(DATA_DIR),  # ✅ 添加数据目录参数
            "--llm-model", model,
            "--keep-workspaces",  # ✅ 强制保留工作区，供前端查看
            "--data-source", data_source  # ✅ 添加数据源选择
        ]

        # Add subtask if in multi-task mode
        if task:
            cmd.extend(["--task", task])
            logger.info(f"Running in multi-task mode with subtask: {task}")

        logger.info(f"Starting workflow with data source: {data_source}")

        # 启动进程
        log_file = LOGS_DIR / f"{task_id}_{workflow}.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(log_file, 'w') as lf:
            proc = subprocess.Popen(
                cmd,
                stdout=lf,
                stderr=subprocess.STDOUT,
                cwd=str(BASE_DIR),
                env=os.environ.copy()
            )

        ACTIVE_PROCESSES[task_id] = proc
        logger.info(f"Started workflow {workflow} for task {task_id} (PID: {proc.pid})")
        logger.info(f"Command: {' '.join(cmd)}")
        logger.info(f"Data directory: {DATA_DIR}")

        return {"status": "started", "task_id": task_id, "workflow": workflow}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start workflow: {e}")
        raise HTTPException(500, str(e))

@app.post("/tasks/{task_id}/stop")
async def stop_workflow(task_id: str):
    """停止工作流"""
    try:
        logger.info(f"Attempting to stop workflow for task: {task_id}")
        logger.info(f"Active processes: {list(ACTIVE_PROCESSES.keys())}")

        killed_pids = []

        # 方法1: 如果进程在字典中，直接终止
        if task_id in ACTIVE_PROCESSES:
            proc = ACTIVE_PROCESSES[task_id]
            pid = proc.pid
            logger.info(f"Found process {pid} for task {task_id}, terminating...")

            # 先尝试优雅终止
            proc.terminate()

            # 等待进程结束（最多10秒）
            try:
                proc.wait(timeout=10)
                logger.info(f"Process {pid} terminated gracefully")
                killed_pids.append(pid)
            except subprocess.TimeoutExpired:
                logger.warning(f"Process {pid} did not terminate gracefully, killing...")
                proc.kill()
                try:
                    proc.wait(timeout=5)
                    logger.info(f"Process {pid} killed")
                    killed_pids.append(pid)
                except subprocess.TimeoutExpired:
                    logger.error(f"Process {pid} could not be killed")

            del ACTIVE_PROCESSES[task_id]

        # 方法2: 使用 pgrep 和 pkill 杀死整个进程组
        # 匹配 --mle-competitions {task_id} 的进程
        try:
            # 使用 pgrep 找到主进程 PID
            pgrep_result = subprocess.run(
                ["pgrep", "-f", f"run_benchmark.py.*--mle-competitions.*{task_id}"],
                capture_output=True,
                text=True
            )

            if pgrep_result.returncode == 0 and pgrep_result.stdout.strip():
                pids = pgrep_result.stdout.strip().split('\n')
                logger.info(f"Found PIDs via pgrep: {pids}")

                for pid_str in pids:
                    try:
                        pid = int(pid_str)
                        if pid not in killed_pids:
                            # 杀死整个进程组（包括子进程）
                            import signal
                            try:
                                os.killpg(os.getpgid(pid), signal.SIGTERM)
                                logger.info(f"Sent SIGTERM to process group {pid}")
                                killed_pids.append(pid)
                            except ProcessLookupError:
                                logger.warning(f"Process {pid} already terminated")
                            except Exception as e:
                                logger.error(f"Failed to kill process group {pid}: {e}")
                    except ValueError:
                        continue

                # 等待2秒让进程优雅退出
                await asyncio.sleep(2)

                # 如果还有进程活着，使用 SIGKILL
                for pid_str in pids:
                    try:
                        pid = int(pid_str)
                        # 检查进程是否还在
                        if os.path.exists(f"/proc/{pid}") or subprocess.run(["ps", "-p", str(pid)], capture_output=True).returncode == 0:
                            logger.warning(f"Process {pid} still alive, sending SIGKILL")
                            try:
                                os.killpg(os.getpgid(pid), signal.SIGKILL)
                            except:
                                pass
                    except:
                        pass

        except Exception as e:
            logger.error(f"Error using pgrep/pkill: {e}")

        logger.info(f"Successfully stopped workflow for task {task_id}. Killed PIDs: {killed_pids}")
        return {"status": "stopped", "pids": killed_pids}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop workflow: {traceback.format_exc()}")
        raise HTTPException(500, str(e))

@app.get("/logs/{task_id}")
async def get_logs(task_id: str, task: Optional[str] = None):
    """获取任务日志

    Args:
        task_id: 任务ID
        task: 可选的子任务名称
    """
    try:
        # 构建日志文件搜索模式
        if task:
            # Multi-task mode: search for subtask-specific logs
            pattern = f"{task_id}_{task}_*.log"
        else:
            # Single task mode or global task logs
            pattern = f"{task_id}_*.log"

        # 查找最新的日志文件
        log_files = list(LOGS_DIR.glob(pattern))

        if not log_files:
            # 如果没有专用日志，检查是否有运行目录
            if task:
                run_id = get_active_run_id(f"{task_id}_{task}")
            else:
                run_id = get_active_run_id(task_id)

            log_path = LOGS_DIR / run_id / "trajectory.log"
            if not log_path.exists():
                logger.info(f"No logs found for task_id={task_id}, task={task}")
                return {"logs": ""}

        # 获取最新的日志文件
        latest_log = max(log_files, key=os.path.getmtime)
        logger.info(f"Reading log file: {latest_log}")

        # 读取所有行（不限制行数）
        lines = []
        with open(latest_log, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        logger.info(f"Read {len(lines)} lines from log file")

        # 如果行数太多，可以返回最后N行，但默认返回全部
        if len(lines) > 10000:
            logger.warning(f"Large log file ({len(lines)} lines), returning last 10000 lines")
            lines = lines[-10000:]

        return {"logs": "".join(lines)}
    except Exception as e:
        logger.error(f"Failed to read logs: {e}")
        return {"logs": f"Error reading logs: {str(e)}"}

@app.post("/upload")
async def upload(background_tasks: BackgroundTasks, file: UploadFile = File(...), task_name: str = Form(...), task_comment: str = Form(""), task_mode: str = Form("standard_ml")):
    import tempfile
    try:
        path = DATA_DIR / task_name
        if path.exists(): shutil.rmtree(path)
        raw = path / "raw"
        os.makedirs(raw, exist_ok=True)
        is_zip = file.filename.endswith(".zip")
        file_path = raw / file.filename
        async with aiofiles.open(file_path, "wb") as f: await f.write(await file.read())
        if is_zip:
            def ex():
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp_p = Path(tmpdir)
                    with zipfile.ZipFile(file_path, 'r') as z: z.extractall(tmp_p)
                    for junk in list(tmp_p.rglob("__MACOSX")) + list(tmp_p.rglob(".DS_Store")):
                        try:
                            if junk.is_dir(): shutil.rmtree(junk)
                            else: junk.unlink()
                        except: pass
                    top_items = [x for x in tmp_p.iterdir() if not x.name.startswith(".")]
                    source_dir = tmp_p
                    if len(top_items) == 1 and top_items[0].is_dir(): source_dir = top_items[0]
                    for item in source_dir.iterdir():
                        if item.is_dir(): shutil.copytree(item, raw / item.name)
                        else: shutil.copy2(item, raw / item.name)
                    file_path.unlink()
            await anyio.to_thread.run_sync(ex)
        bench_dir = BENCHMARKS_DIR / task_name
        if bench_dir.exists(): shutil.rmtree(bench_dir)
        os.makedirs(bench_dir, exist_ok=True)
        with open(bench_dir / ".analyzing", "w") as f: f.write("1")
        background_tasks.add_task(analyze_and_register, task_name, raw, task_comment, task_mode)
        return {"info": "Success", "task_name": task_name}
    except Exception as e: raise HTTPException(500, str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)