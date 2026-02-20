"""DS-Sandbox backend."""

import logging
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

from dslighting.services.sandbox_backends.backends.base import SandboxBackend, SandboxBackendConfig
from dslighting.utils.typing import ExecutionResult

logger = logging.getLogger(__name__)


class DSSandboxBackend(SandboxBackend):
    """DS-Sandbox backend with E2B-compatible API.

    This backend executes code in a local DS-Sandbox environment.
    It provides an E2B-compatible interface for ease of use.

    Usage (E2B-compatible):
        >>> from ds_sandbox import Sandbox
        >>> sandbox = await Sandbox.create()
        >>> result = sandbox.run_code("print('hello')")
        >>> await sandbox.kill()

    Features:
    - Docker or local process isolation
    - File upload/download
    - Code execution with timeout
    - Pre-installed data science libraries
    """

    def __init__(
        self,
        config: Optional[SandboxBackendConfig] = None,
        backend_type: str = "docker",
        workspace_base_dir: Optional[str] = None,
        paused_workspaces_base_dir: Optional[str] = None,
    ):
        """Initialize the DS-Sandbox backend.

        Args:
            config: Backend configuration.
            backend_type: Type of backend to use ("docker" or "local").
            workspace_base_dir: Base directory for workspaces.
            paused_workspaces_base_dir: Base directory for paused workspaces.
        """
        super().__init__(config)
        self.backend_type = backend_type
        self.workspace_base_dir = workspace_base_dir
        self.paused_workspaces_base_dir = paused_workspaces_base_dir
        self._sandbox = None
        self._sandbox_id = None
        self._initialized = False

    async def initialize(self, workspace_path: str = None) -> None:
        """Initialize the DS-Sandbox.

        Args:
            workspace_path: DSLighting workspace path. For local mode, use symlink instead of copying.

        Raises:
            ImportError: If ds_sandbox package is not installed.
        """
        logger.info(f"Initializing DSSandboxBackend (backend_type={self.backend_type})")

        try:
            from ds_sandbox import Sandbox, SandboxConfig
        except ImportError:
            raise ImportError(
                "DS-Sandbox is not installed. Install it with: pip install ds-sandbox"
            )

        workspace_base_dir = (
            self.workspace_base_dir
            or os.getenv("SANDBOX_WORKSPACE_BASE")
            or "/tmp/ds_sandbox_workspaces"
        )
        paused_workspaces_base_dir = (
            self.paused_workspaces_base_dir
            or os.getenv("SANDBOX_PAUSED_BASE")
            or "/tmp/ds_sandbox_paused"
        )

        # Create config
        config = SandboxConfig(
            default_backend=self.backend_type,
            workspace_base_dir=workspace_base_dir,
            paused_workspaces_base_dir=paused_workspaces_base_dir,
        )

        # For local mode, pass external workspace path to create symlink
        external_workspace = workspace_path if self.backend_type == "local" else None

        # Create sandbox using E2B-compatible API (use create_async to avoid asyncio.run() in async context)
        self._sandbox = await Sandbox.create_async(
            config=config,
            timeout=self.config.timeout,
            envs=self.config.env_vars,
            external_workspace_path=external_workspace,
        )
        self._sandbox_id = self._sandbox.workspace_id
        self._initialized = True
        logger.info(f"DSSandboxBackend initialized: {self._sandbox_id}")

    async def upload_file(self, content: bytes, path: str) -> str:
        """Upload a file to the sandbox.

        E2B-compatible API:
            >>> await sandbox.files.write("/workspace/data.csv", content)

        Args:
            content: File content as bytes.
            path: Destination path in the sandbox.

        Returns:
            The path where the file was saved.
        """
        if not self._sandbox:
            await self.initialize()

        return await self._sandbox.files.write(path, content)

    async def download_file(self, path: str) -> bytes:
        """Download a file from the sandbox.

        Args:
            path: Path to the file in the sandbox.

        Returns:
            File content as bytes.
        """
        if not self._sandbox:
            await self.initialize()

        return await self._sandbox.files.read(path)

    async def _upload_workspace_files(self, workspace_path: str) -> None:
        """Upload all files from workspace to ds_sandbox.

        Args:
            workspace_path: Path to the local workspace directory.
        """
        import os
        from pathlib import Path

        workspace = Path(workspace_path)
        if not workspace.exists():
            logger.warning(f"Workspace does not exist: {workspace_path}")
            return

        # Upload all files recursively
        files_uploaded = 0
        for root, dirs, files in os.walk(workspace):
            for file in files:
                file_path = Path(root) / file
                # Calculate relative path
                rel_path = file_path.relative_to(workspace)
                # Convert to sandbox path (use forward slashes)
                sandbox_path = str(rel_path).replace("\\", "/")

                try:
                    content = file_path.read_bytes()
                    # Use ds_sandbox's files.write (sync wrapper)
                    self._sandbox.files.write(sandbox_path, content)
                    files_uploaded += 1
                    logger.debug(f"Uploaded file: {sandbox_path}")
                except Exception as e:
                    logger.warning(f"Failed to upload file {sandbox_path}: {e}")

        if files_uploaded > 0:
            logger.info(f"Uploaded {files_uploaded} files to ds_sandbox")

    async def execute(
        self,
        code: str,
        workspace_path: str,
        timeout: Optional[int] = None,
    ) -> ExecutionResult:
        """Execute code in the DS-Sandbox.

        This uses the E2B-compatible run_code() API which:
        - Runs Python code in an isolated environment
        - Supports pre-installed libraries (pandas, matplotlib, etc.)
        - Returns stdout, stderr, error, and artifacts

        Args:
            code: Python code to execute.
            workspace_path: Path to the workspace directory.
            timeout: Optional timeout override in seconds.

        Returns:
            ExecutionResult with stdout, stderr, success status, artifacts, etc.
        """
        if not self._initialized:
            await self.initialize(workspace_path=workspace_path)

        # For docker mode, upload files from DSLighting workspace to ds_sandbox
        # For local mode, files are shared via symlink (no upload needed)
        if self.backend_type != "local":
            await self._upload_workspace_files(workspace_path)

        effective_timeout = timeout or self.config.timeout
        execution_id = uuid.uuid4().hex
        started_at = datetime.utcnow()
        perf_start = time.perf_counter()

        try:
            logger.info(f"Executing code in DS-Sandbox (timeout: {effective_timeout}s)...")

            # Use E2B-compatible run_code API
            result = await self._sandbox.run_code_async(
                code,
                timeout=effective_timeout,
            )

            # Extract results
            success = result.success
            exc_type = None
            stdout = result.logs.stdout if result.logs else ""
            stderr = result.logs.stderr if result.logs else ""

            # Check for error
            if result.error:
                exc_type = result.error.get("name")
                if not stderr:
                    stderr = result.error.get("value", "")

            status = "succeeded" if success else "failed"
            logger.info(f"DS-Sandbox execution finished: {status}.")

            if not success:
                logger.error(f"=== DS-SANDBOX EXECUTION FAILED ===")
                logger.error(f"Exception Type: {exc_type}")
                if stdout:
                    logger.error(f"STDOUT:\n{stdout}")
                if stderr:
                    logger.error(f"STDERR:\n{stderr}")
                logger.error(f"=== END ERROR LOG ===")

            duration_ms = int((time.perf_counter() - perf_start) * 1000)

            # Extract artifacts from results
            artifacts = []
            if result.results:
                for r in result.results:
                    if isinstance(r, dict) and r.get("artifacts"):
                        artifacts.extend(r["artifacts"])

            return ExecutionResult(
                success=success,
                stdout=stdout,
                stderr=stderr,
                exc_type=exc_type,
                artifacts=artifacts,
                metadata={
                    "execution_id": execution_id,
                    "workspace_id": self._sandbox_id,
                    "sandbox_cwd": workspace_path,
                    "started_at_utc": started_at.isoformat() + "Z",
                    "duration_ms": duration_ms,
                    "backend": "ds_sandbox",
                    "backend_type": self.backend_type,
                },
            )

        except ImportError as e:
            logger.error(f"DS-Sandbox package not available: {e}")
            return ExecutionResult(
                success=False,
                stderr=f"DS-Sandbox not available: {e}",
                exc_type="ImportError",
                metadata={
                    "execution_id": execution_id,
                    "backend": "ds_sandbox",
                },
            )

        except Exception as e:
            logger.error(f"Error executing in DS-Sandbox: {e}", exc_info=True)
            duration_ms = int((time.perf_counter() - perf_start) * 1000)
            return ExecutionResult(
                success=False,
                stderr=str(e),
                exc_type=e.__class__.__name__,
                metadata={
                    "execution_id": execution_id,
                    "duration_ms": duration_ms,
                    "backend": "ds_sandbox",
                },
            )

    async def shutdown(self) -> None:
        """Shutdown the DS-Sandbox."""
        logger.info("Shutting down DSSandboxBackend")
        if self._sandbox:
            try:
                await self._sandbox.kill()
                logger.info(f"DSSandboxBackend {self._sandbox_id} killed")
            except Exception as e:
                logger.warning(f"Error killing sandbox: {e}")
            finally:
                self._sandbox = None
                self._sandbox_id = None
                self._initialized = False
