import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
load_dotenv(BASE_DIR / ".env")

# Force absolute paths relative to project root
DATA_DIR = (BASE_DIR / "data" / "competitions").resolve()
BENCHMARKS_DIR = (BASE_DIR / "benchmarks" / "mlebench" / "competitions").resolve()
LOGS_DIR = (BASE_DIR / "runs").resolve()

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BENCHMARKS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
