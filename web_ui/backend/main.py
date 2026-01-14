import uvicorn
import os
import sys
from pathlib import Path

# Add the backend directory to sys.path so we can import 'app'
backend_dir = Path(__file__).resolve().parent
sys.path.append(str(backend_dir))

if __name__ == "__main__":
    # We run the app defined in app/main.py
    # Using the string import format to avoid some import issues during dev
    uvicorn.run("app.main:app", host="0.0.0.0", port=8003, reload=True)
