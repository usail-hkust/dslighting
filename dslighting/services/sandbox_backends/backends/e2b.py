"""E2B cloud sandbox backend."""

import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from dslighting.services.sandbox_backends.backends.base import SandboxBackend, SandboxBackendConfig
from dslighting.utils.typing import ExecutionResult

logger = logging.getLogger(__name__)


class E2BSandboxBackend(SandboxBackend):
    """E2B cloud sandbox backend.

    This backend executes code in E2B's cloud sandbox environment.
    It requires an E2B API key to be configured.

    Usage pattern (following E2B docs):
        1. Initialize sandbox
        2. Optionally upload files to workspace
        3. Run code with run_code()
        4. Get results with stdout, stderr, charts, etc.
    """

    def __init__(
        self,
        config: Optional[SandboxBackendConfig] = None,
        api_key: Optional[str] = None,
    ):
        """Initialize the E2B sandbox backend.

        Args:
            config: Backend configuration.
            api_key: E2B API key. If not provided, will try to read from E2B_API_KEY env var.
        """
        super().__init__(config)
        self.api_key = api_key
        self._sandbox = None
        self._sandbox_id = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the E2B sandbox.

        Raises:
            ImportError: If e2b package is not installed.
            ValueError: If API key is not provided.
        """
        logger.info("Initializing E2BSandboxBackend")

        try:
            from e2b import Sandbox
        except ImportError:
            raise ImportError(
                "E2B SDK is not installed. Install it with: pip install e2b"
            )

        if not self.api_key:
            import os
            self.api_key = os.environ.get("E2B_API_KEY")

        if not self.api_key:
            raise ValueError(
                "E2B API key is required. Provide it via api_key parameter "
                "or E2B_API_KEY environment variable."
            )

        # Create sandbox with configuration
        self._sandbox = Sandbox(
            api_key=self.api_key,
            timeout=self.config.timeout,
            envs=self.config.env_vars,
        )
        self._sandbox_id = self._sandbox.sandbox_id
        self._initialized = True
        logger.info(f"E2B sandbox initialized: {self._sandbox_id}")

    async def upload_file(self, content: bytes, path: str) -> str:
        """Upload a file to the E2B sandbox.

        This follows the E2B pattern:
            >>> content = open("dataset.csv").read()
            >>> path = await sandbox.upload_file(content, "/home/user/dataset.csv")

        Args:
            content: File content as bytes.
            path: Destination path in the sandbox.

        Returns:
            The path where the file was saved.
        """
        if not self._sandbox:
            await self.initialize()

        from e2b import Sandbox
        if isinstance(self._sandbox, Sandbox):
            return await self._sandbox.files.write(path, content)
        else:
            # Fallback for older API
            return self._sandbox.files.write(path, content)

    async def download_file(self, path: str) -> bytes:
        """Download a file from the E2B sandbox.

        Args:
            path: Path to the file in the sandbox.

        Returns:
            File content as bytes.
        """
        if not self._sandbox:
            await self.initialize()

        return await self._sandbox.files.read(path)

    async def _upload_workspace_files(self, workspace_path: str) -> None:
        """Upload all files from workspace to E2B sandbox.

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
                    # Use E2B's files.write
                    await self._sandbox.files.write(sandbox_path, content)
                    files_uploaded += 1
                    logger.debug(f"Uploaded file: {sandbox_path}")
                except Exception as e:
                    logger.warning(f"Failed to upload file {sandbox_path}: {e}")

        if files_uploaded > 0:
            logger.info(f"Uploaded {files_uploaded} files to E2B sandbox")

    async def execute(
        self,
        code: str,
        workspace_path: str,
        timeout: Optional[int] = None,
    ) -> ExecutionResult:
        """Execute code in the E2B sandbox.

        This uses E2B's code interpreter API which:
        - Runs Python code in an isolated environment
        - Supports pre-installed libraries (pandas, matplotlib, etc.)
        - Returns stdout, stderr, charts (PNG), and other artifacts

        Args:
            code: Python code to execute.
            workspace_path: Path to the workspace directory (used for file operations).
            timeout: Optional timeout override in seconds.

        Returns:
            ExecutionResult with stdout, stderr, success status, charts, etc.
        """
        if not self._initialized:
            await self.initialize()

        # Upload files from workspace_path to E2B sandbox
        await self._upload_workspace_files(workspace_path)

        effective_timeout = timeout or self.config.timeout
        execution_id = uuid.uuid4().hex
        started_at = datetime.utcnow()
        perf_start = time.perf_counter()

        try:
            logger.info(f"Executing code in E2B sandbox (timeout: {effective_timeout}s)...")

            # Use E2B's run_code() method (code interpreter API)
            # This is different from commands.run() - it uses the code interpreter
            # which has pre-installed data science libraries
            result = self._sandbox.run_code(
                code,
                timeout=effective_timeout,
            )

            # E2B run_code() returns a CodeResult object with:
            # - results: list of execution results (can contain logs, charts, tables)
            # - error: error info if execution failed
            # - logs: stdout/stderr

            success = result.error is None
            exc_type = None

            # Extract stdout/stderr from logs
            stdout = ""
            stderr = ""
            artifacts = []

            if result.logs:
                stdout = result.logs.stdout or ""
                stderr = result.logs.stderr or ""

            # Check for error
            if result.error:
                exc_type = result.error.name
                stderr = result.error.value or ""
                if result.error.traceback:
                    stderr += "\n" + result.error.traceback

            # Extract charts/images from results
            # E2B returns charts as base64 PNG in result.png
            for i, exec_result in enumerate(result.results):
                if hasattr(exec_result, 'png') and exec_result.png:
                    # Chart is saved as base64 PNG
                    artifacts.append(f"chart_{i}.png")

            status = "succeeded" if success else "failed"
            logger.info(f"E2B execution finished: {status}.")

            if not success:
                logger.error(f"=== E2B EXECUTION FAILED ===")
                logger.error(f"Exception Type: {exc_type}")
                if stdout:
                    logger.error(f"STDOUT:\n{stdout}")
                if stderr:
                    logger.error(f"STDERR:\n{stderr}")
                logger.error(f"=== END ERROR LOG ===")

            duration_ms = int((time.perf_counter() - perf_start) * 1000)

            return ExecutionResult(
                success=success,
                stdout=stdout,
                stderr=stderr,
                exc_type=exc_type,
                artifacts=artifacts,
                metadata={
                    "execution_id": execution_id,
                    "sandbox_id": self._sandbox_id,
                    "sandbox_cwd": workspace_path,
                    "started_at_utc": started_at.isoformat() + "Z",
                    "duration_ms": duration_ms,
                    "backend": "e2b",
                },
            )

        except Exception as e:
            logger.error(f"Error executing in E2B sandbox: {e}", exc_info=True)
            duration_ms = int((time.perf_counter() - perf_start) * 1000)
            return ExecutionResult(
                success=False,
                stderr=str(e),
                exc_type=e.__class__.__name__,
                metadata={
                    "execution_id": execution_id,
                    "sandbox_id": self._sandbox_id,
                    "duration_ms": duration_ms,
                    "backend": "e2b",
                },
            )

    async def shutdown(self) -> None:
        """Shutdown the E2B sandbox."""
        logger.info("Shutting down E2BSandboxBackend")
        if self._sandbox:
            try:
                self._sandbox.kill()
                logger.info(f"E2B sandbox {self._sandbox_id} killed")
            except Exception as e:
                logger.warning(f"Error killing E2B sandbox: {e}")
            finally:
                self._sandbox = None
                self._sandbox_id = None
                self._initialized = False
