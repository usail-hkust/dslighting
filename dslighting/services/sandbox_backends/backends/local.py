"""Local sandbox backend using subprocess for process isolation."""

import logging
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from dslighting.services.sandbox_backends.backends.base import SandboxBackend, SandboxBackendConfig
from dslighting.utils.typing import ExecutionResult

logger = logging.getLogger(__name__)


class LocalSandboxBackend(SandboxBackend):
    """Local sandbox backend using subprocess for process isolation.

    This backend executes code in a local subprocess with optional resource limits.
    It's the default backend that provides process isolation through subprocess.run().
    """

    def __init__(
        self,
        config: Optional[SandboxBackendConfig] = None,
        workspace_path: Optional[str] = None,
        env_overrides: Optional[dict] = None,
        auto_matplotlib: bool = False,
    ):
        """Initialize the local sandbox backend.

        Args:
            config: Backend configuration.
            workspace_path: Path to the workspace directory.
            env_overrides: Environment variable overrides.
            auto_matplotlib: Whether to inject matplotlib non-interactive backend.
        """
        super().__init__(config)
        self.workspace_path = workspace_path
        self.env_overrides = env_overrides or {}
        self.auto_matplotlib = auto_matplotlib
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the backend."""
        logger.info("Initializing LocalSandboxBackend")
        self._initialized = True

    async def execute(
        self,
        code: str,
        workspace_path: str,
        timeout: Optional[int] = None,
    ) -> ExecutionResult:
        """Execute code in a local subprocess.

        Args:
            code: Python code to execute.
            workspace_path: Path to the workspace directory.
            timeout: Optional timeout override in seconds.

        Returns:
            ExecutionResult with stdout, stderr, success status, etc.
        """
        if not self._initialized:
            await self.initialize()

        # Determine the effective timeout
        effective_timeout = timeout or self.config.timeout
        effective_workspace = workspace_path or self.workspace_path

        if not effective_workspace:
            raise ValueError("workspace_path must be provided")

        return self._execute_sync(code, effective_workspace, effective_timeout)

    def _execute_sync(
        self,
        code: str,
        workspace_path: str,
        timeout: int,
    ) -> ExecutionResult:
        """Synchronous execution implementation.

        Args:
            code: Python code to execute.
            workspace_path: Path to the workspace directory.
            timeout: Timeout in seconds.

        Returns:
            ExecutionResult with stdout, stderr, success status, etc.
        """
        # Optionally inject matplotlib non-interactive backend
        if self.auto_matplotlib:
            fixed_code = "import matplotlib\nmatplotlib.use('Agg')\n" + code
            logger.debug("Auto-injected matplotlib non-interactive backend")
        else:
            fixed_code = code

        script_name = f"_sandbox_script_{uuid.uuid4().hex}.py"
        script_path = Path(workspace_path) / "run" / script_name
        execution_id = uuid.uuid4().hex
        started_at = datetime.utcnow()
        perf_start = time.perf_counter()

        # Ensure the run directory exists
        script_path.parent.mkdir(parents=True, exist_ok=True)

        execution_result = ExecutionResult(
            success=False, stdout="", stderr="", exc_type=None
        )

        try:
            script_path.write_text(fixed_code, encoding="utf-8")
            logger.info(
                f"Executing script '{script_name}' in sandbox (timeout: {timeout}s)..."
            )

            completed_process = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=workspace_path,
                encoding="utf-8",
                errors="replace",
                env={**os.environ, **self.env_overrides},
            )

            success = completed_process.returncode == 0
            exc_type = None
            if not success:
                stderr_lines = completed_process.stderr.strip().split("\n")
                if stderr_lines:
                    match = re.search(r"^(\w+(?:Error|Exception)):", stderr_lines[-1])
                    if match:
                        exc_type = match.group(1)

            status = "succeeded" if success else f"failed (exit code {completed_process.returncode})"
            logger.info(f"Script execution finished: {status}.")

            if not success:
                logger.error(f"=== SCRIPT EXECUTION FAILED ===")
                logger.error(f"Exit Code: {completed_process.returncode}")
                logger.error(f"Exception Type: {exc_type}")
                if completed_process.stdout:
                    logger.error(f"STDOUT:\n{completed_process.stdout}")
                if completed_process.stderr:
                    logger.error(f"STDERR:\n{completed_process.stderr}")
                logger.error(f"=== END ERROR LOG ===")

            execution_result = ExecutionResult(
                success=success,
                stdout=completed_process.stdout,
                stderr=completed_process.stderr,
                exc_type=exc_type,
            )

        except subprocess.TimeoutExpired as e:
            logger.warning("Script execution timed out. Process was terminated.")
            execution_result = ExecutionResult(
                success=False,
                stdout=e.stdout or "",
                stderr=e.stderr or f"TimeoutError: Execution exceeded {timeout} seconds.",
                exc_type="TimeoutError",
            )

        except Exception as e:
            logger.error(
                f"An unexpected error occurred during sandbox setup: {e}",
                exc_info=True,
            )
            execution_result = ExecutionResult(
                success=False,
                stderr=str(e),
                exc_type=e.__class__.__name__,
            )

        finally:
            ended_at = datetime.utcnow()
            duration = round(time.perf_counter() - perf_start, 4)

            # Copy script to artifacts
            copied_script_path = None
            artifacts_dir = Path(workspace_path) / "artifacts" / "sandbox_scripts"
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            if script_path.exists():
                try:
                    copied_script_path = artifacts_dir / script_name
                    shutil.copy2(script_path, copied_script_path)
                except Exception as copy_error:
                    logger.error(
                        f"Failed to copy sandbox script '{script_name}' to artifacts: {copy_error}",
                        exc_info=True,
                    )

            # Add metadata
            execution_result.metadata = {
                "execution_id": execution_id,
                "script_filename": script_name,
                "original_script_path": str(script_path) if script_path.exists() else None,
                "copied_script_path": str(copied_script_path) if copied_script_path else None,
                "sandbox_cwd": workspace_path,
                "started_at_utc": started_at.isoformat() + "Z",
                "ended_at_utc": ended_at.isoformat() + "Z",
                "duration_seconds": duration,
                "backend": "local",
            }

        return execution_result

    async def shutdown(self) -> None:
        """Shutdown the backend."""
        logger.info("Shutting down LocalSandboxBackend")
        self._initialized = False
