"""Sandbox service for isolated code execution in a controlled environment."""

import logging
import os
import json
import re
import resource
import subprocess
import sys
import uuid
import asyncio
import shutil
import time
import multiprocessing
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, List, Dict, Any, Optional
from multiprocessing import Process, Queue

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError, CellTimeoutError, DeadKernelError

from dslighting.utils.typing import ExecutionResult
from dslighting.services.workspace import WorkspaceService
from dslighting.error import WorkspaceError
from dslighting.utils.constants import (
    DEFAULT_FLUSH_INTERVAL,
    DEFAULT_MAX_BATCH_SIZE,
    DEFAULT_POOL_SIZE_SANDBOX,
    WORKER_TIMEOUT_SECONDS,
    MAX_MEMORY_MB,
    CPU_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)

__all__ = [
    "SandboxService",
    "NotebookExecutor",
    "ProcessIsolatedNotebookExecutor",
    "ResourceLimitedExecutor",
    "PersistentWorkerPool",
    "TelemetryBatcher",
]

# ==============================================================================
# ==                    RESOURCE LIMITING FOR SANDBOX PROCESSES               ==
# ==============================================================================

def set_process_limits(max_memory_mb: int = MAX_MEMORY_MB, max_cpu_seconds: int = CPU_TIMEOUT_SECONDS):
    """Set resource limits for sandbox processes.

    Args:
        max_memory_mb: Maximum memory in megabytes
        max_cpu_seconds: Maximum CPU time in seconds
    """
    # Memory limit (RSS in bytes - RLIMIT_AS limits address space which includes memory)
    resource.setrlimit(
        resource.RLIMIT_AS,
        (max_memory_mb * 1024 * 1024, resource.RLIM_INFINITY)
    )
    # CPU time limit
    resource.setrlimit(resource.RLIMIT_CPU, (max_cpu_seconds, resource.RLIM_INFINITY))


class ResourceLimitedExecutor:
    """Executor with resource limits for sandboxed code execution."""

    def __init__(self, max_memory_mb: int = MAX_MEMORY_MB, max_cpu_seconds: int = CPU_TIMEOUT_SECONDS):
        """Initialize executor with resource limits.

        Args:
            max_memory_mb: Maximum memory in megabytes (default: 4096 MB)
            max_cpu_seconds: Maximum CPU time in seconds (default: 300s)
        """
        self.max_memory_mb = max_memory_mb
        self.max_cpu_seconds = max_cpu_seconds

    def start(self):
        """Start executor with resource limits.

        Note: On systems using 'spawn' multiprocessing (e.g., macOS),
        resource limits must be set at the start of each child process.
        For 'fork' systems, limits can be set after fork.
        """
        if multiprocessing.get_start_method() == 'spawn':
            # For spawned processes, limits should be set early in the worker entry point
            # This is handled in notebook_worker() for the notebook execution path
            logger.debug(
                f"Resource limits configured: {self.max_memory_mb}MB memory, "
                f"{self.max_cpu_seconds}s CPU. Note: apply limits in child process."
            )
        else:
            # For fork, we can set limits in the parent
            set_process_limits(self.max_memory_mb, self.max_cpu_seconds)
            logger.debug(
                f"Resource limits set in parent process: "
                f"{self.max_memory_mb}MB memory, {self.max_cpu_seconds}s CPU."
            )

    def apply_to_worker(self):
        """Apply resource limits within a worker process.

        Call this early in any spawned child process to enforce limits.
        """
        set_process_limits(self.max_memory_mb, self.max_cpu_seconds)
        logger.debug(
            f"Resource limits applied to worker: "
            f"{self.max_memory_mb}MB memory, {self.max_cpu_seconds}s CPU."
        )


# ==============================================================================
# ==                    TELEMETRY BATCHER                                     ==
# ==============================================================================

NOTEBOOK_INIT_CODE = """
import warnings
import pandas as pd
import numpy as np
import os

# Optional: matplotlib (for plotting)
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
except Exception:
    pass

# Optional: seaborn (for better plots)
try:
    import seaborn as sns
    sns.set_theme(style="whitegrid")
except Exception:
    pass

warnings.filterwarnings('ignore')
print("DSLighting Notebook environment initialized.")
"""


class TelemetryBatcher:
    """
    Batches telemetry writes to reduce I/O overhead.
    Writes are flushed when batch size is reached or after a timeout.
    """

    def __init__(self, file_path: Path, flush_interval: float = DEFAULT_FLUSH_INTERVAL, max_batch_size: int = DEFAULT_MAX_BATCH_SIZE):
        """
        Args:
            file_path: Path to the output file
            flush_interval: Maximum seconds between flushes
            max_batch_size: Maximum number of records to batch before flushing
        """
        self.file_path = Path(file_path)
        self.flush_interval = flush_interval
        self.max_batch_size = max_batch_size
        self._buffer: List[Dict[str, Any]] = []
        self._last_flush = time.time()
        self._lock = asyncio.Lock()

    async def write(self, data: Dict[str, Any]) -> None:
        """Add data to the batch buffer. Flushes if necessary."""
        async with self._lock:
            self._buffer.append(data)
            should_flush = (
                len(self._buffer) >= self.max_batch_size or
                time.time() - self._last_flush > self.flush_interval
            )
            if should_flush:
                await self._flush()

    async def _flush(self) -> None:
        """Write buffered data to disk."""
        if not self._buffer:
            return

        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            # Try to use aiofiles for async write
            try:
                import aiofiles
                async with aiofiles.open(self.file_path, "a", encoding="utf-8") as f:
                    for item in self._buffer:
                        await f.write(json.dumps(item, ensure_ascii=False) + "\n")
            except ImportError:
                # Fall back to sync write
                with open(self.file_path, "a", encoding="utf-8") as f:
                    for item in self._buffer:
                        f.write(json.dumps(item, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.warning("Failed to flush telemetry batch: %s", exc)
        finally:
            self._buffer.clear()
            self._last_flush = time.time()

    async def finalize(self) -> None:
        """Force flush any remaining buffered data."""
        async with self._lock:
            await self._flush()

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
            raise WorkspaceError(
                f"Could not initialize notebook environment. Error: {init_result.stderr}",
                error_code="WSP-002",
                details={"stderr": init_result.stderr},
                suggestion="Check the notebook initialization code and ensure dependencies are installed"
            )
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
            raise WorkspaceError(
                "NotebookExecutor not started. Use 'async with' context manager.",
                error_code="WSP-003",
                suggestion="Use the notebook_executor context manager: 'async with sandbox.notebook_executor() as executor:'"
            )
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
    run_dir: str,  # Changed: Pass run_dir path string instead of WorkspaceService object
    timeout: int,
    env_overrides: Optional[Dict[str, str]] = None,
    max_memory_mb: int = MAX_MEMORY_MB,
    max_cpu_seconds: int = CPU_TIMEOUT_SECONDS,
):
    """
    This function runs in a separate process. It creates an asyncio event loop,
    manages a NotebookExecutor, and processes tasks from the queue.

    IMPORTANT: On macOS (and any system using 'spawn' for multiprocessing),
    we must pass only picklable objects (like strings) to the worker process.
    We reconstruct WorkspaceService inside the worker from the run_dir path.

    Args:
        task_queue: Queue to receive code to execute
        result_queue: Queue to send results back
        run_dir: Path string to the workspace directory
        timeout: Execution timeout in seconds
        env_overrides: Environment variable overrides
        max_memory_mb: Maximum memory in megabytes for resource limits
        max_cpu_seconds: Maximum CPU time in seconds for resource limits
    """
    # Apply resource limits early in the spawned process
    # This must be done at the start since 'spawn' doesn't inherit limits
    set_process_limits(max_memory_mb=max_memory_mb, max_cpu_seconds=max_cpu_seconds)
    logger.debug(
        f"Resource limits applied in worker: {max_memory_mb}MB memory, "
        f"{max_cpu_seconds}s CPU."
    )

    # Reconstruct WorkspaceService inside the worker process
    # We pass the parent directory as base_dir and run_dir name as run_name
    from pathlib import Path
    run_dir_path = Path(run_dir)
    base_dir = str(run_dir_path.parent)
    run_name = run_dir_path.name

    workspace = WorkspaceService(run_name, base_dir)
    if env_overrides:
        for key, value in env_overrides.items():
            os.environ[str(key)] = str(value)

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
    def __init__(
        self,
        workspace: WorkspaceService,
        timeout: int,
        env_overrides: Optional[Dict[str, str]] = None,
        max_memory_mb: int = MAX_MEMORY_MB,
        max_cpu_seconds: int = CPU_TIMEOUT_SECONDS,
    ):
        """
        Args:
            workspace: Workspace service for managing files
            timeout: Execution timeout in seconds
            env_overrides: Environment variable overrides
            max_memory_mb: Maximum memory in megabytes for sandbox (default: 4096)
            max_cpu_seconds: Maximum CPU time in seconds (default: 300)
        """
        self.task_queue = Queue()
        self.result_queue = Queue()
        self.env_overrides = {
            str(key): str(value)
            for key, value in (env_overrides or {}).items()
            if value is not None
        }
        self.max_memory_mb = max_memory_mb
        self.max_cpu_seconds = max_cpu_seconds
        # Pass workspace path as string instead of WorkspaceService object
        # This ensures compatibility with macOS 'spawn' multiprocessing mode
        workspace_path = str(workspace.run_dir)
        self.worker_process = Process(
            target=notebook_worker,
            args=(
                self.task_queue, self.result_queue, workspace_path, timeout,
                self.env_overrides, max_memory_mb, max_cpu_seconds
            ),
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
            raise WorkspaceError(
                "Worker process is not running.",
                error_code="WSP-004",
                suggestion="Ensure the notebook worker process is started before executing cells"
            )
            
        loop = asyncio.get_running_loop()
        
        # Send the task asynchronously
        await loop.run_in_executor(None, self.task_queue.put, code)

        # Wait for the result asynchronously
        result = await loop.run_in_executor(None, self.result_queue.get)

        return result


class PersistentWorkerPool:
    """
    Manages a pool of persistent notebook worker processes to avoid the overhead
    of creating new processes for each task.

    This significantly improves performance by reusing worker processes across
    multiple executions. Workers are created on-demand and kept alive for reuse.
    """

    def __init__(
        self,
        workspace: WorkspaceService,
        pool_size: int = DEFAULT_POOL_SIZE_SANDBOX,
        timeout: int = WORKER_TIMEOUT_SECONDS,
        env_overrides: Optional[Dict[str, str]] = None,
        max_memory_mb: int = MAX_MEMORY_MB,
        max_cpu_seconds: int = CPU_TIMEOUT_SECONDS,
    ):
        """
        Args:
            workspace: Workspace service for managing files
            pool_size: Maximum number of worker processes to maintain
            timeout: Execution timeout for each worker (seconds)
            env_overrides: Environment variables to set in worker processes
            max_memory_mb: Maximum memory in megabytes per worker (default: 4096)
            max_cpu_seconds: Maximum CPU time in seconds per worker (default: 300)
        """
        self.workspace = workspace
        self.pool_size = pool_size
        self.timeout = timeout
        self.env_overrides = env_overrides
        self.max_memory_mb = max_memory_mb
        self.max_cpu_seconds = max_cpu_seconds
        self.workers: List[ProcessIsolatedNotebookExecutor] = []
        self.available_workers: asyncio.Queue = asyncio.Queue()
        self._lock = asyncio.Lock()
        self._initialized = False

    async def start(self):
        """Initialize the worker pool."""
        if self._initialized:
            return

        logger.info(f"Initializing persistent worker pool with {self.pool_size} workers...")
        async with self._lock:
            for i in range(self.pool_size):
                worker = ProcessIsolatedNotebookExecutor(
                    workspace=self.workspace,
                    timeout=self.timeout,
                    env_overrides=self.env_overrides,
                    max_memory_mb=self.max_memory_mb,
                    max_cpu_seconds=self.max_cpu_seconds,
                )
                worker.start()
                self.workers.append(worker)
                await self.available_workers.put(worker)

            self._initialized = True
            logger.info(f"Worker pool initialized with {len(self.workers)} workers")

    async def execute_cell(self, code: str) -> ExecutionResult:
        """
        Execute code in an available worker from the pool.

        If no workers are available, this will wait until one becomes free.
        """
        if not self._initialized:
            await self.start()

        # Get an available worker (waits if necessary)
        worker = await self.available_workers.get()

        try:
            # Execute the code
            result = await worker.execute_cell(code)
        finally:
            # Always return the worker to the pool
            await self.available_workers.put(worker)

        return result

    async def stop(self):
        """Shutdown all workers in the pool."""
        if not self._initialized:
            return

        logger.info("Shutting down persistent worker pool...")
        async with self._lock:
            # Stop all workers
            for worker in self.workers:
                worker.stop(timeout=5)

            self.workers.clear()
            self._initialized = False

        logger.info("Worker pool shutdown complete")

    @property
    def pool_size_active(self) -> int:
        """Return the current number of active workers in the pool."""
        return len(self.workers)

    @property
    def available_count(self) -> int:
        """Return the number of currently available workers."""
        return self.available_workers.qsize()


# ==============================================================================
# ==                   MODIFIED: SANDBOX SERVICE INTEGRATION                  ==
# ==============================================================================
class SandboxService:
    """
    Provides unified access to isolated script and notebook code execution environments.

    **Important**: All public methods are async. Use await everywhere.

    This design ensures consistency across DSLighting - users don't need to remember
    which methods are sync vs async. Just use await for all operations.

    Args:
        workspace: Workspace service for managing files
        timeout: Default timeout for script execution (seconds)
        auto_matplotlib: Automatically inject matplotlib backend (default: False).
                        Set to True for Web UI environments that need visualization.
                        Set to False for standalone package usage.

    Example:
        >>> sandbox = SandboxService(workspace=workspace_service)
        >>> result = await sandbox.run_script(code)  # Always use await
    """
    def __init__(
        self,
        workspace: WorkspaceService,
        timeout: int = 600,
        auto_matplotlib: bool = False,
        env_overrides: Optional[Dict[str, str]] = None,
        backend: Optional[Any] = None,
    ):
        """Initialize SandboxService.

        Args:
            workspace: Workspace service for managing files.
            timeout: Default timeout for script execution (seconds).
            auto_matplotlib: Automatically inject matplotlib backend.
            env_overrides: Environment variable overrides.
            backend: Optional sandbox backend. If not provided, uses local subprocess.
        """
        self.workspace = workspace
        self.timeout = timeout
        self.auto_matplotlib = auto_matplotlib
        self.env_overrides = {
            str(key): str(value)
            for key, value in (env_overrides or {}).items()
            if value is not None
        }
        self.execution_history: List[Dict[str, Any]] = []
        self.backend = backend

        # Thread pool for running sync operations in background threads
        # This allows sandbox executions to be async from user's perspective
        # while actually executing synchronously in thread pool
        import concurrent.futures
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=DEFAULT_POOL_SIZE_SANDBOX)

    async def run_script(self, script_code: str, timeout: Optional[int] = None) -> ExecutionResult:
        """
        Async API: Runs a Python script within the sandbox workspace.

        This is an async method that runs the synchronous subprocess execution
        in a thread pool, providing a consistent async interface to users.

        Args:
            script_code: Python code to execute
            timeout: Optional timeout override (uses self.timeout if None)

        Returns:
            ExecutionResult with stdout, stderr, success status, etc.

        Example:
            >>> result = await sandbox.run_script("print('hello')")
        """
        # If a backend is provided, use it
        if self.backend is not None:
            workspace_path = str(self.workspace.get_path("sandbox_workdir"))
            return await self.backend.execute(script_code, workspace_path, timeout)

        # Otherwise, use the legacy local execution
        loop = asyncio.get_event_loop()
        # Run the sync implementation in a thread pool
        return await loop.run_in_executor(
            self._executor,
            self._run_script_sync,
            script_code,
            timeout
        )

    def _run_script_sync(self, script_code: str, timeout: Optional[int] = None) -> ExecutionResult:
        """
        Internal sync implementation of run_script.

        This method does the actual synchronous subprocess execution.
        It's wrapped by the public async run_script() method.
        """
        # Optionally inject matplotlib non-interactive backend
        # This is only done if auto_matplotlib=True (used by Web UI for visualization)
        if self.auto_matplotlib:
            # Force non-interactive backend for matplotlib to prevent blocking plt.show()
            fixed_code = "import matplotlib\nmatplotlib.use('Agg')\n" + script_code
            logger.debug("Auto-injected matplotlib non-interactive backend")
        else:
            # Use code as-is without modification (default for DSLighting package)
            fixed_code = script_code

        script_name = f"_sandbox_script_{uuid.uuid4().hex}.py"
        script_path = self.workspace.run_dir / script_name
        execution_id = uuid.uuid4().hex
        started_at = datetime.utcnow()
        perf_start = time.perf_counter()
        execution_result: ExecutionResult = ExecutionResult(success=False, stdout="", stderr="", exc_type=None)

        try:
            script_path.write_text(fixed_code, encoding="utf-8")
            logger.info(f"Executing script '{script_name}' in sandbox (timeout: {self.timeout}s)...")
            completed_process = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True, text=True, timeout=self.timeout,
                cwd=self.workspace.get_path("sandbox_workdir"),
                encoding='utf-8', errors='replace',
                env={**os.environ, **self.env_overrides},
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
                    copied_script_path = scripts_dir / script_name
                    shutil.copy2(script_path, copied_script_path)
                except Exception as copy_error:
                    logger.error(f"Failed to copy sandbox script '{script_name}' to artifacts: {copy_error}", exc_info=True)

            execution_metadata = {
                "execution_id": execution_id,
                "script_filename": script_name,
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
                "code": fixed_code,
            }
            self.execution_history.append(history_entry)
        return execution_result

    @asynccontextmanager
    async def notebook_executor(self) -> AsyncGenerator[ProcessIsolatedNotebookExecutor, None]:
        """
        Provides a process-isolated notebook executor as an asynchronous context
        manager to ensure proper startup and cleanup of the worker process.
        """
        executor = ProcessIsolatedNotebookExecutor(
            self.workspace,
            self.timeout,
            env_overrides=self.env_overrides,
        )
        executor.start()
        try:
            yield executor
        finally:
            executor.stop()

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Return a copy of sandbox execution history for telemetry persistence."""
        return list(self.execution_history)
