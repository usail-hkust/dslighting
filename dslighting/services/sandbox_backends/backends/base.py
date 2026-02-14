"""Sandbox backend abstract interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from dslighting.utils.typing import ExecutionResult


@dataclass
class SandboxBackendConfig:
    """Configuration for sandbox backend.

    Attributes:
        timeout: Timeout for code execution in seconds.
        memory_mb: Memory limit in megabytes.
        cpu_cores: Number of CPU cores to allocate.
        network_policy: Network policy ("disabled", "whitelist", "proxy").
        env_vars: Environment variables to set in the sandbox.
    """
    timeout: int = 600
    memory_mb: int = 4096
    cpu_cores: float = 2.0
    network_policy: str = "disabled"
    env_vars: Dict[str, str] = field(default_factory=dict)


class SandboxBackend(ABC):
    """Abstract base class for sandbox backends.

    This defines the interface that all sandbox backends must implement.
    Each backend provides a different way to execute code in isolation.
    """

    def __init__(self, config: Optional[SandboxBackendConfig] = None):
        """Initialize the backend with configuration.

        Args:
            config: Backend configuration. Uses defaults if not provided.
        """
        self.config = config or SandboxBackendConfig()

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the backend.

        This is called once before any code execution.
        Use this to set up connections, start services, etc.
        """
        pass

    @abstractmethod
    async def execute(
        self,
        code: str,
        workspace_path: str,
        timeout: Optional[int] = None,
    ) -> ExecutionResult:
        """Execute code in the sandbox.

        Args:
            code: Python code to execute.
            workspace_path: Path to the workspace directory.
            timeout: Optional timeout override in seconds.

        Returns:
            ExecutionResult with stdout, stderr, success status, etc.
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the backend.

        This is called when the backend is no longer needed.
        Use this to clean up resources, close connections, etc.
        """
        pass

    @property
    def name(self) -> str:
        """Return the name of this backend."""
        return self.__class__.__name__
