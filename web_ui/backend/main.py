import sys
import os
import shutil
import subprocess
import zipfile
import yaml
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

app = FastAPI(title="DSLighting Web UI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use resolve() to get absolute path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "competitions"
BENCHMARKS_DIR = BASE_DIR / "benchmarks" / "mlebench" / "competitions"
LOGS_DIR = BASE_DIR / "runs"

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BENCHMARKS_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"status": "DSLighting Backend is running", "base_dir": str(BASE_DIR)}

@app.get("/workflows")
def list_workflows():
    return {
        "workflows": [
            "aide", "automind", "dsagent", "data_interpreter", 
            "autokaggle", "aflow", "deepanalyze"
        ]
    }

@app.get("/models")
def list_models():
    """List available models from .env or config."""
    import json
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
    
    # 1. Check LLM_MODEL_CONFIGS
    configs_raw = os.getenv("LLM_MODEL_CONFIGS")
    models = []
    if configs_raw:
        try:
            configs = json.loads(configs_raw)
            models = list(configs.keys())
        except:
            pass
            
    # 2. Check default LLM_MODEL
    default_model = os.getenv("LLM_MODEL")
    if default_model and default_model not in models:
        models.insert(0, default_model)
        
    # 3. Fallback
    if not models:
        models = ["gpt-4o-mini"]
        
    return {"models": models}

@app.get("/tasks")
def list_tasks():
    """List all registered custom tasks."""
    tasks = []
    # List tasks from DATA_DIR as user data is the source of truth
    if DATA_DIR.exists():
        for task_dir in DATA_DIR.iterdir():
            if task_dir.is_dir():
                tasks.append(task_dir.name)
    return {"tasks": sorted(tasks)}

@app.get("/tasks/{task_id}")
def get_task_details(task_id: str):
    """Get details of a specific task."""
    # Check both data dir and benchmark dir
    data_task_dir = DATA_DIR / task_id
    bench_task_dir = BENCHMARKS_DIR / task_id
    
    if not data_task_dir.exists():
        raise HTTPException(status_code=404, detail="Task data not found")
    
    # Attempt to read description from BENCHMARKS_DIR (where we write metadata)
    desc_path = bench_task_dir / "description.md"
    description = ""
    if desc_path.exists():
        description = desc_path.read_text()
    else:
        description = f"# {task_id}\n\n(No description provided)"
        
    config_path = bench_task_dir / "config.yaml"
    config = {}
    if config_path.exists():
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

    # List public data files
    public_path = data_task_dir / "prepared" / "public"
    files = []
    if public_path.exists():
        files = [f.name for f in public_path.iterdir()]

    return {
        "id": task_id,
        "description": description,
        "files": files,
        "config": config,
        "status": "registered" if bench_task_dir.exists() else "unregistered"
    }

@app.post("/tasks/{task_id}/update")
async def update_task(task_id: str, description: str = Form(...)):
    """Update task description/prompt."""
    bench_task_dir = BENCHMARKS_DIR / task_id
    
    # If not registered yet, try to register
    if not bench_task_dir.exists():
        # Try to re-register based on existing data
        data_task_dir = DATA_DIR / task_id
        if data_task_dir.exists():
            pub = data_task_dir / "prepared" / "public"
            priv = data_task_dir / "prepared" / "private"
            if pub.exists() and priv.exists():
                register_competition(task_id, pub, priv)
            else:
                raise HTTPException(status_code=400, detail="Cannot register task: missing prepared data folders")
        else:
            raise HTTPException(status_code=404, detail="Task not found")

    desc_path = bench_task_dir / "description.md"
    with open(desc_path, "w") as f:
        f.write(description)
        
    return {"status": "updated", "id": task_id}

def register_competition(task_id: str, prepared_public: Path, prepared_private: Path):
    """
    Registers the competition by creating necessary config files in 
    benchmarks/mlebench/competitions/<task_id>
    """
    comp_dir = BENCHMARKS_DIR / task_id
    os.makedirs(comp_dir, exist_ok=True)

    print(f"Registering competition {task_id} in {comp_dir}")

    files_private = list(prepared_private.glob("*.csv"))
    files_public = list(prepared_public.glob("*.csv"))
    
    answer_file = next((f.name for f in files_private if "test" in f.name.lower() or "answer" in f.name.lower()), None)
    if not answer_file and files_private:
        answer_file = files_private[0].name
    
    sample_sub = next((f.name for f in files_public if "sample" in f.name.lower()), None)
    if not sample_sub and files_public:
        sample_sub = files_public[0].name

    if not answer_file:
        if files_public:
            shutil.copy(files_public[0], prepared_private / files_public[0].name)
            answer_file = files_public[0].name
        else:
            answer_file = "dummy_answer.csv"

    if not sample_sub:
        sample_sub = answer_file

    config = {
        "id": task_id,
        "name": task_id,
        "description": "description.md",
        "competition_type": "generic",
        "dataset": {
            "answers": f"{task_id}/prepared/private/{answer_file}",
            "gold_submission": f"{task_id}/prepared/private/{answer_file}",
            "sample_submission": f"{task_id}/prepared/public/{sample_sub}"
        },
        "preparer": f"file:{comp_dir}/prepare.py:prepare",
        "grader": {
            "grade_fn": "mlebench.grade:simple_accuracy_grader"
        },
        "raw_dir": f"{task_id}/raw",
        "public_dir": f"{task_id}/prepared/public",
        "private_dir": f"{task_id}/prepared/private",
        "checksums": "checksums.yaml",
        "leaderboard": "leaderboard.csv"
    }
    
    prepare_py_content = """
from pathlib import Path

def prepare(raw_dir: Path, public_dir: Path, private_dir: Path):
    return public_dir
"""
    with open(comp_dir / "prepare.py", "w") as f:
        f.write(prepare_py_content)

    with open(comp_dir / "config.yaml", "w") as f:
        yaml.dump(config, f)

    if not (comp_dir / "description.md").exists():
        with open(comp_dir / "description.md", "w") as f:
            f.write(f"# {task_id}\n\nAuto-generated competition task.")

    with open(comp_dir / "leaderboard.csv", "w") as f:
        f.write("team_name,score\nbenchmark,0.0")

    with open(comp_dir / "checksums.yaml", "w") as f:
        f.write("")

@app.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...), 
    task_name: str = Form(...)
):
    task_path = DATA_DIR / task_name
    raw_path = task_path / "raw"
    prepared_public = task_path / "prepared" / "public"
    prepared_private = task_path / "prepared" / "private"
    
    if task_path.exists():
        shutil.rmtree(task_path)
    
    os.makedirs(raw_path, exist_ok=True)
    os.makedirs(prepared_public, exist_ok=True)
    os.makedirs(prepared_private, exist_ok=True)
    
    upload_dest = raw_path / file.filename
    with open(upload_dest, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
        
    if file.filename.endswith(".zip"):
        with zipfile.ZipFile(upload_dest, 'r') as zip_ref:
            zip_ref.extractall(raw_path)
            
        extracted_files = [p for p in raw_path.rglob("*") if p.is_file() and p.name != file.filename]
        files_str = [str(p) for p in extracted_files]
        
        has_public = any("public" in f for f in files_str)
        has_private = any("private" in f for f in files_str)
        
        if has_public and has_private:
            for p in extracted_files:
                if "public" in str(p):
                    shutil.copy(p, prepared_public / p.name)
                elif "private" in str(p):
                    shutil.copy(p, prepared_private / p.name)
        else:
            csv_files = [p for p in extracted_files if p.suffix == ".csv"]
            if not csv_files:
                raise HTTPException(status_code=400, detail="No CSV files found in the zip.")
            
            for csv_file in csv_files:
                fname = csv_file.name.lower()
                if "answer" in fname or "solution" in fname:
                    shutil.copy(csv_file, prepared_private / csv_file.name)
                elif "test" in fname and "train" not in fname:
                     shutil.copy(csv_file, prepared_public / csv_file.name)
                     shutil.copy(csv_file, prepared_private / csv_file.name)
                else:
                    shutil.copy(csv_file, prepared_public / csv_file.name)
                    
    elif file.filename.endswith(".csv"):
        shutil.copy(upload_dest, prepared_public / file.filename)
        shutil.copy(upload_dest, prepared_private / file.filename)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format.")

    try:
        register_competition(task_name, prepared_public, prepared_private)
    except Exception as e:
        print(f"Error registering competition: {e}")
        # Log to stderr so it shows in uvicorn logs
        sys.stderr.write(f"Error registering competition: {e}\n")

    return {
        "info": "Dataset uploaded and registered successfully.", 
        "task_name": task_name
    }

def run_benchmark_task(workflow: str, task_id: str, model: Optional[str] = None):
    cmd = [
        "python", "run_benchmark.py",
        "--workflow", workflow,
        "--benchmark", "mle",
        "--data-dir", "data/competitions",
        "--task-id", task_id
    ]
    if model:
        cmd.extend(["--llm-model", model])
    
    with open(f"web_ui/backend/logs_{task_id}.txt", "w") as log_file:
        subprocess.run(cmd, cwd=str(BASE_DIR), stdout=log_file, stderr=subprocess.STDOUT)

@app.post("/run")
async def run_task(
    background_tasks: BackgroundTasks,
    workflow: str = Form(...),
    task_id: str = Form(...),
    model: Optional[str] = Form(None)
):
    background_tasks.add_task(run_benchmark_task, workflow, task_id, model)
    return {"status": "started", "task_id": task_id, "workflow": workflow, "model": model}

@app.get("/logs/{task_id}")
def get_logs(task_id: str):
    log_file = Path(f"web_ui/backend/logs_{task_id}.txt")
    if log_file.exists():
        with open(log_file, "r") as f:
            return {"logs": f.read()}
    return {"logs": "Waiting for logs..."}