# dsat/services/sandbox.py

import logging
import re
import subprocess
import sys
import uuid
import asyncio
import shutil
import time
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, List, Dict, Any
from multiprocessing import Process, Queue

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError, CellTimeoutError, DeadKernelError

from dsat.common.typing import ExecutionResult
from dsat.services.workspace import WorkspaceService

logger = logging.getLogger(__name__)

NOTEBOOK_INIT_CODE = """
import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

try:
    import seaborn as sns
    sns.set_theme(style="whitegrid")
except Exception:
    pass

warnings.filterwarnings('ignore')
print("DSAT Notebook environment initialized.")
"""

class NotebookExecutor:
    """
    Manages a persistent Jupyter kernel for cell-by-cell code execution.
    This class is intended to be used as an async context manager.
    """
    def __init__(self, workspace: WorkspaceService, timeout: int):
        self.workspace = workspace
        self.timeout = timeout
        self.nb = nbformat.v4.new_notebook()
        self.client = NotebookClient(
            self.nb, 
            timeout=self.timeout, 
            cwd=str(self.workspace.get_path("sandbox_workdir"))
        )
        self._initialized = False
        self._kernel_cm = None

    async def start(self):
        if self._initialized:
            return
        logger.info("Starting new Jupyter kernel for notebook execution...")
        self._kernel_cm = self.client.async_setup_kernel()
        await self._kernel_cm.__aenter__()
        logger.info("Kernel started. Initializing environment...")
        self._initialized = True
        sandbox_workdir_path = self.workspace.get_path("sandbox_workdir").resolve()
        full_init_code = (
            f"import os\n"
            f"os.chdir(r'{sandbox_workdir_path}')\n"
            f"print(f'CWD set to: {{os.getcwd()}}')\n"
            f"\n"
            f"{NOTEBOOK_INIT_CODE}"
        )
        init_result = await self.execute_cell(full_init_code)
        if not init_result.success:
            await self.stop()
            raise RuntimeError(f"Could not initialize notebook environment. Error: {init_result.stderr}")
        if self.nb.cells:
            self.nb.cells.pop(0)
        logger.info(f"Notebook environment ready. CWD is now {sandbox_workdir_path}")

    async def stop(self):
        logger.info("Shutting down Jupyter kernel.")
        if self._kernel_cm is not None:
            try:
                await self._kernel_cm.__aexit__(None, None, None)
            finally:
                self._kernel_cm = None
                self._initialized = False

    def _parse_cell_outputs(self, outputs: list) -> ExecutionResult:
        stdout_lines, stderr_lines, artifacts = [], [], []
        success = True
        exc_type = None
        for out in outputs:
            if out.output_type == 'stream':
                if out.name == 'stdout': stdout_lines.append(out.text)
                else: stderr_lines.append(out.text)
            elif out.output_type in ['execute_result', 'display_data']:
                if 'text/plain' in out.data: stdout_lines.append(out.data['text/plain'])
                if 'image/png' in out.data: artifacts.append("[Image data generated in notebook]")
            elif out.output_type == 'error':
                success = False
                exc_type = out.ename
                ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                traceback_text = ansi_escape.sub('', "\n".join(out.traceback))
                stderr_lines.append(f"ERROR: {out.ename}\n{traceback_text}")
        return ExecutionResult(
            success=success, stdout="\n".join(stdout_lines).strip(),
            stderr="\n".join(stderr_lines).strip(), artifacts=artifacts, exc_type=exc_type
        )

    async def execute_cell(self, code: str) -> ExecutionResult:
        if not self._initialized:
            raise RuntimeError("NotebookExecutor not started. Use 'async with' context manager.")
        cell_index = len(self.nb.cells)
        self.nb.cells.append(nbformat.v4.new_code_cell(source=code))
        try:
            await self.client.async_execute_cell(self.nb.cells[cell_index], cell_index)
            result = self._parse_cell_outputs(self.nb.cells[cell_index].outputs)
        except CellExecutionError:
            result = self._parse_cell_outputs(self.nb.cells[cell_index].outputs)
        except (CellTimeoutError, DeadKernelError) as e:
            result = ExecutionResult(success=False, stderr=str(e), exc_type=e.__class__.__name__)
        
        notebook_path = self.workspace.get_path("artifacts") / "session.ipynb"
        with open(notebook_path, "w", encoding='utf-8') as f:
            nbformat.write(self.nb, f)
        return result

# ==============================================================================
# ==                    NEW: WORKER FUNCTION FOR SUBPROCESS                   ==
# ==============================================================================

def notebook_worker(
    task_queue: Queue, 
    result_queue: Queue, 
    workspace: WorkspaceService, 
    timeout: int
):
    """
    This function runs in a separate process. It creates an asyncio event loop,
    manages a NotebookExecutor, and processes tasks from the queue.
    """
    async def main_loop():
        # The executor's lifecycle is tied to this async function
        executor = NotebookExecutor(workspace, timeout)
        await executor.start()
        
        while True:
            # Get code from the main process. A `None` object is the shutdown signal.
            code = task_queue.get()
            if code is None:
                break
            
            # Execute the code and put the result back
            result = await executor.execute_cell(code)
            result_queue.put(result)
            
        await executor.stop()

    try:
        asyncio.run(main_loop())
    except Exception as e:
        # If something catastrophic happens, report it back
        logger.error(f"Notebook worker process failed: {e}", exc_info=True)
        result_queue.put(ExecutionResult(
            success=False, stderr=f"Worker process failed: {e}", exc_type=e.__class__.__name__
        ))


class ProcessIsolatedNotebookExecutor:
    """
    Manages the lifecycle of a notebook worker process, providing a clean
    interface to the main application and ensuring robust cleanup.
    """
    def __init__(self, workspace: WorkspaceService, timeout: int):
        self.task_queue = Queue()
        self.result_queue = Queue()
        self.worker_process = Process(
            target=notebook_worker,
            args=(self.task_queue, self.result_queue, workspace, timeout),
            daemon=True  # Set as daemon process to prevent main process from hanging
        )

    def start(self):
        """Starts the worker process."""
        logger.info("Starting process-isolated notebook worker...")
        self.worker_process.start()
        
    def stop(self, timeout: int = 10):
        """
        Stops the worker process gracefully, with a forceful termination fallback.
        Note: Since this is a daemon process, it will be automatically terminated
        when the parent process exits, providing an additional safety mechanism.
        """
        if not self.worker_process.is_alive():
            return
            
        logger.info("Stopping process-isolated notebook worker...")
        try:
            # Send shutdown signal
            self.task_queue.put(None)
            # Wait for graceful shutdown
            self.worker_process.join(timeout=timeout)
            
            # If still alive, it's hung. Terminate it.
            if self.worker_process.is_alive():
                logger.warning(
                    f"Notebook worker did not exit gracefully within {timeout}s. Terminating."
                )
                self.worker_process.terminate()
                self.worker_process.join() # Wait for termination to complete
        finally:
            self.task_queue.close()
            self.result_queue.close()
        logger.info("Notebook worker stopped.")

    async def execute_cell(self, code: str) -> ExecutionResult:
        """
        Sends code to the worker process and waits for the result.
        This is async to fit into the main application's event loop, but the
        underlying queue.get() is blocking. We use run_in_executor to avoid
        blocking the main event loop.
        """
        if not self.worker_process.is_alive():
            raise RuntimeError("Worker process is not running.")
            
        loop = asyncio.get_running_loop()
        
        # Send the task asynchronously
        await loop.run_in_executor(None, self.task_queue.put, code)
        
        # Wait for the result asynchronously
        result = await loop.run_in_executor(None, self.result_queue.get)
        
        return result


# ==============================================================================
# ==                   MODIFIED: SANDBOX SERVICE INTEGRATION                  ==
# ==============================================================================
class SandboxService:
    """
    Provides unified access to isolated script and notebook code execution environments.
    """
    def __init__(self, workspace: WorkspaceService, timeout: int = 600):
        self.workspace = workspace
        self.timeout = timeout
        self.execution_history: List[Dict[str, Any]] = []

    def run_script(self, code: str) -> ExecutionResult:
        # This part of the code was already robust and remains unchanged, but now we record telemetry.
        script_filename = f"_sandbox_script_{uuid.uuid4().hex}.py"
        script_path = self.workspace.run_dir / script_filename
        execution_id = uuid.uuid4().hex
        started_at = datetime.utcnow()
        perf_start = time.perf_counter()
        execution_result: ExecutionResult = ExecutionResult(success=False, stdout="", stderr="", exc_type=None)

        try:
            script_path.write_text(code, encoding="utf-8")
            logger.info(f"Executing script '{script_filename}' in sandbox (timeout: {self.timeout}s)...")
            completed_process = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True, text=True, timeout=self.timeout,
                cwd=self.workspace.get_path("sandbox_workdir"),
                encoding='utf-8', errors='replace'
            )
            success = completed_process.returncode == 0
            exc_type = None
            if not success:
                stderr_lines = completed_process.stderr.strip().split('\n')
                if stderr_lines:
                    match = re.search(r"^(\w+(?:Error|Exception)):", stderr_lines[-1])
                    if match: exc_type = match.group(1)
            status = "succeeded" if success else f"failed (exit code {completed_process.returncode})"
            logger.info(f"Script execution finished: {status}.")
            if not success:
                logger.error(f"=== SCRIPT EXECUTION FAILED ===")
                logger.error(f"Exit Code: {completed_process.returncode}")
                logger.error(f"Exception Type: {exc_type}")
                if completed_process.stdout: logger.error(f"STDOUT:\n{completed_process.stdout}")
                if completed_process.stderr: logger.error(f"STDERR:\n{completed_process.stderr}")
                logger.error(f"=== END ERROR LOG ===")
            execution_result = ExecutionResult(
                success=success, stdout=completed_process.stdout,
                stderr=completed_process.stderr, exc_type=exc_type
            )
        except subprocess.TimeoutExpired as e:
            logger.warning("Script execution timed out. Process was terminated.")
            execution_result = ExecutionResult(
                success=False, stdout=e.stdout or "",
                stderr=e.stderr or f"TimeoutError: Execution exceeded {self.timeout} seconds.",
                exc_type="TimeoutError"
            )
        except Exception as e:
            logger.error(f"An unexpected error occurred during sandbox setup: {e}", exc_info=True)
            execution_result = ExecutionResult(success=False, stderr=str(e), exc_type=e.__class__.__name__)
        finally:
            ended_at = datetime.utcnow()
            duration = round(time.perf_counter() - perf_start, 4)

            copied_script_path = None
            scripts_dir = self.workspace.get_path("artifacts") / "sandbox_scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            if script_path.exists():
                try:
                    copied_script_path = scripts_dir / script_filename
                    shutil.copy2(script_path, copied_script_path)
                except Exception as copy_error:
                    logger.error(f"Failed to copy sandbox script '{script_filename}' to artifacts: {copy_error}", exc_info=True)

            execution_metadata = {
                "execution_id": execution_id,
                "script_filename": script_filename,
                "original_script_path": str(script_path) if script_path.exists() else None,
                "copied_script_path": str(copied_script_path) if copied_script_path else None,
                "sandbox_cwd": str(self.workspace.get_path("sandbox_workdir")),
                "started_at_utc": started_at.isoformat() + "Z",
                "ended_at_utc": ended_at.isoformat() + "Z",
                "duration_seconds": duration,
            }
            execution_result.metadata = execution_metadata

            history_entry = {
                **execution_metadata,
                "success": execution_result.success,
                "exc_type": execution_result.exc_type,
                "stdout": execution_result.stdout,
                "stderr": execution_result.stderr,
                "code": code,
            }
            self.execution_history.append(history_entry)
        return execution_result

    @asynccontextmanager
    async def notebook_executor(self) -> AsyncGenerator[ProcessIsolatedNotebookExecutor, None]:
        """
        Provides a process-isolated notebook executor as an asynchronous context
        manager to ensure proper startup and cleanup of the worker process.
        """
        executor = ProcessIsolatedNotebookExecutor(self.workspace, self.timeout)
        executor.start()
        try:
            yield executor
        finally:
            executor.stop()

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Return a copy of sandbox execution history for telemetry persistence."""
        return list(self.execution_history)
