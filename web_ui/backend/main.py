import sys
import os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import shutil
import subprocess

# Add parent directory to sys.path to import dslighting modules if needed
# (Though for stability, we might call the runner via subprocess initially)
sys.path.append(str(Path(__file__).parent.parent.parent))

app = FastAPI(title="DSLighting Web UI")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "competitions"
LOGS_DIR = BASE_DIR / "runs"

@app.get("/")
def read_root():
    return {"status": "DSLighting Backend is running"}

@app.get("/workflows")
def list_workflows():
    return {
        "workflows": [
            "aide", 
            "automind", 
            "dsagent", 
            "data_interpreter", 
            "autokaggle", 
            "aflow", 
            "deepanalyze"
        ]
    }

@app.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...), 
    task_name: str = Form(...)
):
    """
    Uploads a dataset zip or single file and prepares it in the expected dslighting structure.
    Expects structure: data/competitions/<task_name>/raw
    """
    task_path = DATA_DIR / task_name
    raw_path = task_path / "raw"
    prepared_path = task_path / "prepared" / "public"
    
    # Clean/Create directories
    if task_path.exists():
        pass # Decide if we overwrite or error. For now, we append/overwrite files.
    
    os.makedirs(raw_path, exist_ok=True)
    os.makedirs(prepared_path, exist_ok=True)
    
    file_location = raw_path / file.filename
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
        
    # For simplicity in this demo, copy the uploaded file to 'train.csv' if it's a csv
    # allowing the runner to find it easily if the user uploaded 'train.csv'.
    # A real implementation would handle unzipping or multiple files.
    if file.filename.endswith(".csv"):
        shutil.copy(file_location, prepared_path / file.filename)

    return {"info": f"File '{file.filename}' saved at '{file_location}'"}

def run_benchmark_task(workflow: str, task_id: str):
    """
    Executes the benchmark command in a subprocess.
    """
    cmd = [
        "python", "run_benchmark.py",
        "--workflow", workflow,
        "--benchmark", "mle",
        "--data-dir", "data/competitions",
        "--task-id", task_id
    ]
    
    # Note: This runs in the context of the activated venv if started correctly
    # or needs explicit venv python path.
    with open(f"web_ui/backend/logs_{task_id}.txt", "w") as log_file:
        subprocess.run(cmd, cwd=str(BASE_DIR), stdout=log_file, stderr=subprocess.STDOUT)

@app.post("/run")
async def run_task(
    background_tasks: BackgroundTasks,
    workflow: str = Form(...),
    task_id: str = Form(...)
):
    """
    Triggers a run in the background.
    """
    background_tasks.add_task(run_benchmark_task, workflow, task_id)
    return {"status": "started", "task_id": task_id, "workflow": workflow}

@app.get("/logs/{task_id}")
def get_logs(task_id: str):
    log_file = Path(f"web_ui/backend/logs_{task_id}.txt")
    if log_file.exists():
        with open(log_file, "r") as f:
            return {"logs": f.read()}
    return {"logs": "Waiting for logs..."}
