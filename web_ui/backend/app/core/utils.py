import re
import uuid
import os
import threading
from pathlib import Path
from .config import LOGS_DIR

import logging

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()

def get_active_run_id(task_id: str) -> str:
    """Find the LATEST existing dsat_run directory in the absolute LOGS_DIR or generate a NEW one."""
    with _LOCK:
        safe_task_id = "".join(c if c.isalnum() else "_" for c in task_id)
        prefix = f"dsat_run_{safe_task_id}_"
        
        # Ensure root logs dir exists
        os.makedirs(LOGS_DIR, exist_ok=True)
        
        # 1. Search in the intended absolute LOGS_DIR (project_root/runs)
        existing = [d for d in LOGS_DIR.iterdir() if d.is_dir() and d.name.startswith(prefix)]
        if existing:
            # Sort by modification time to get the most recent one
            existing.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            active_id = existing[0].name
            # logger.info(f"Using existing workspace: {LOGS_DIR / active_id}")
            return active_id
                
        # 2. Generate a NEW ID if nothing found
        new_id = f"{prefix}{uuid.uuid4().hex[:8]}"
        logger.info(f"Creating new workspace for {task_id}: {LOGS_DIR / new_id}")
        os.makedirs(LOGS_DIR / new_id, exist_ok=True)
        return new_id

def transform_report_links(content: str, task_id: str) -> str:
    if not content:
        return ""
    run_id = get_active_run_id(task_id)
    # The static files are served from /outputs which maps to LOGS_DIR
    base_url = f"http://localhost:8003/outputs/{run_id}/sandbox/"
    
    def repl(m):
        alt = m.group(1)
        path = m.group(2)
        # Skip if already a full URL or absolute path
        if path.startswith(('http', 'https', '/')):
            return m.group(0)
        
        # Clean relative path markers
        p = path
        if p.startswith('./'):
            p = p[2:]
        elif p.startswith('../'):
            # Basic support for one level up, though not expected here
            p = p[3:]
            
        full_url = f"{base_url}{p}"
        logger.debug(f"Transforming image link: {path} -> {full_url}")
        return f"![{alt}]({full_url})"
    
    # Standard Markdown image regex: ![alt text](path/to/image.png)
    return re.sub(r'!\[(.*?)\]\((.*?)\)', repl, content)
