"""
Core interfaces for DSLighting.

This module provides abstract base classes and interfaces that define
contracts for various components in the DSLighting framework.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from pathlib import Path
from dataclasses import dataclass, field

from .vector_storage import (
    VectorStorageInterface,
    VectorStorageConfig,
    create_vector_storage,
)


@dataclass
class AgentResult:
    """
    Standard result object for all Agent implementations.

    This class is defined once to avoid duplication across the codebase.
    All agents should return this consistent result format.

    Attributes:
        success: Whether the task completed successfully
        output: Task output (predictions, answer, file path, etc.)
        score: Evaluation score (if available)
        cost: Total LLM cost in USD
        duration: Execution time in seconds
        artifacts_path: Path to generated artifacts
        workspace_path: Path to workspace directory
        error: Error message if failed
        metadata: Additional metadata
    """
    success: bool
    output: Any
    cost: float = 0.0
    duration: float = 0.0
    score: float | None = None
    artifacts_path: Path | None = None
    workspace_path: Path | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        if self.success:
            return (
                f"AgentResult(success={self.success}, "
                f"output={self.output}, "
                f"score={self.score}, "
                f"cost=${self.cost:.4f}, "
                f"duration={self.duration:.1f}s)"
            )
        else:
            return (
                f"AgentResult(success={self.success}, "
                f"error={self.error}, "
                f"cost=${self.cost:.4f})"
            )


class AgentInterface(ABC):
    """
    Base interface that all Agent implementations must follow.

    This ensures consistency across different workflow implementations
    and enables testing through dependency injection.
    """

    @abstractmethod
    def run(
        self,
        task_id: str | None = None,
        data: str | Path | object = None,
        task: str | None = None,
        output: str | Path | None = None,
        **kwargs
    ) -> AgentResult:
        """
        Execute the agent on a task.

        Args:
            task_id: Task ID to load from registry
            data: Data to process (path or data object)
            task: Task description
            output: Output path
            **kwargs: Additional parameters

        Returns:
            AgentResult containing execution results
        """
        pass

    @abstractmethod
    def cleanup(self):
        """Clean up resources and workspaces."""
        pass

    def get_config(self) -> dict[str, Any]:
        """
        Get agent configuration.

        Returns:
            Dictionary containing agent configuration
        """
        raise NotImplementedError("Subclasses must implement get_config()")


class WorkflowFactoryInterface(ABC):
    """
    Base interface for workflow factories.

    Workflow factories are responsible for creating configured agents
    for specific workflow types (AIDE, AutoKaggle, etc.).
    """

    @abstractmethod
    def create_agent(self, **kwargs) -> AgentInterface:
        """
        Create a configured agent instance.

        Args:
            **kwargs: Agent configuration parameters

        Returns:
            Configured AgentInterface instance
        """
        pass

    @abstractmethod
    async def run_with_task_id(
        self,
        task_id: str,
        **kwargs
    ) -> AgentResult:
        """
        Run workflow with a task ID from registry.

        Args:
            task_id: Task identifier
            **kwargs: Additional parameters

        Returns:
            AgentResult containing execution results
        """
        pass

    @abstractmethod
    def cleanup(self):
        """Clean up resources."""
        pass


class LLMProviderInterface(ABC):
    """
    Interface for LLM providers.

    This allows different LLM backends (OpenAI, Anthropic, LiteLLM, etc.)
    to be used interchangeably.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.0,
        **kwargs
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            prompt: Input prompt
            model: Model name
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    async def agenerate(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.0,
        **kwargs
    ) -> str:
        """
        Async version of generate().

        Args:
            prompt: Input prompt
            model: Model name
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            Generated text response
        """
        pass


__all__ = [
    "AgentResult",
    "AgentInterface",
    "WorkflowFactoryInterface",
    "LLMProviderInterface",
    "VectorStorageInterface",
    "VectorStorageConfig",
    "create_vector_storage",
]
