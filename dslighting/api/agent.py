"""
Agent - High-Level Agent Interface

User-friendly agent class that wraps preset agents using factory pattern.
"""

from pathlib import Path
from typing import Optional, Union
import asyncio
from dataclasses import dataclass, field

# Import factory classes
from dsat.workflows.factory import (
    AIDEWorkflowFactory,
    AutoKaggleWorkflowFactory,
    DataInterpreterWorkflowFactory,
    DeepAnalyzeWorkflowFactory,
    DSAgentWorkflowFactory,
    AutoMindWorkflowFactory,
    AFlowWorkflowFactory,
)


@dataclass
class AgentResult:
    """
    Result of running an Agent on a data science task.

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
    output: any
    cost: float = 0.0
    duration: float = 0.0
    score: Optional[float] = None
    artifacts_path: Optional[Path] = None
    workspace_path: Optional[Path] = None
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)

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


class Agent:
    """
    High-level Agent interface.

    This is the user-facing agent class that provides a simple interface
    to run data science tasks.

    Example:
        from dslighting import Agent

        agent = Agent(workflow="aide", model="gpt-4o")
        result = agent.run(task_id="bike-sharing-demand")
    """

    def __init__(
        self,
        workflow: str = "aide",
        model: str = "gpt-4o",
        api_key: str = None,
        api_base: str = None,
        provider: str = None,
        temperature: float = None,
        timeout: int = 300,
        keep_workspace: bool = False,
        **kwargs
    ):
        """
        Initialize Agent.

        Args:
            workflow: Name of the workflow to use ("aide", "autokaggle", "data_interpreter", "deepanalyze", "dsagent", "automind", "aflow")
            model: LLM model to use
            api_key: API key (optional, will be read from env if not provided)
            api_base: API base URL (optional, will be read from env if not provided)
            provider: LLM provider (optional)
            temperature: Temperature parameter (optional, will be read from env if not provided)
            timeout: Sandbox timeout in seconds
            keep_workspace: Whether to keep workspace after execution
            **kwargs: Additional arguments passed to create_agent()
        """
        self.workflow_name = workflow
        self.timeout = timeout
        self.keep_workspace = keep_workspace
        self._agent_kwargs = kwargs

        # Create factory based on workflow
        workflow_lower = workflow.lower()

        if workflow_lower == "aide":
            self._factory = AIDEWorkflowFactory(
                model=model,
                api_key=api_key,
                api_base=api_base,
                provider=provider,
                temperature=temperature,
                timeout=timeout,
                keep_workspace=keep_workspace
            )
        elif workflow_lower in ["autokaggle", "kaggle"]:
            self._factory = AutoKaggleWorkflowFactory(
                model=model,
                api_key=api_key,
                api_base=api_base,
                provider=provider,
                temperature=temperature,
                timeout=timeout,
                keep_workspace=keep_workspace
            )
        elif workflow_lower in ["data_interpreter", "interpreter"]:
            self._factory = DataInterpreterWorkflowFactory(
                model=model,
                api_key=api_key,
                api_base=api_base,
                provider=provider,
                temperature=temperature,
                timeout=timeout,
                keep_workspace=keep_workspace
            )
        elif workflow_lower == "deepanalyze":
            self._factory = DeepAnalyzeWorkflowFactory(
                model=model,
                api_key=api_key,
                api_base=api_base,
                provider=provider,
                temperature=temperature,
                timeout=timeout,
                keep_workspace=keep_workspace
            )
        elif workflow_lower == "dsagent":
            self._factory = DSAgentWorkflowFactory(
                model=model,
                api_key=api_key,
                api_base=api_base,
                provider=provider,
                temperature=temperature,
                timeout=timeout,
                keep_workspace=keep_workspace
            )
        elif workflow_lower == "automind":
            self._factory = AutoMindWorkflowFactory(
                model=model,
                api_key=api_key,
                api_base=api_base,
                provider=provider,
                temperature=temperature,
                timeout=timeout,
                keep_workspace=keep_workspace
            )
        elif workflow_lower == "aflow":
            self._factory = AFlowWorkflowFactory(
                model=model,
                api_key=api_key,
                api_base=api_base,
                provider=provider,
                temperature=temperature,
                timeout=timeout,
                keep_workspace=keep_workspace
            )
        else:
            raise ValueError(
                f"Unknown workflow: {workflow}. "
                f"Choose from: aide, autokaggle, data_interpreter, deepanalyze, dsagent, automind, aflow"
            )

    def run(
        self,
        task_id: Optional[str] = None,
        data: Union[str, Path, 'TaskContext'] = None,
        task: Optional[str] = None,
        output: Optional[Union[str, Path]] = None,
        **kwargs
    ):
        """
        Run the agent on a task.

        Args:
            task_id: Task ID to load from registry (recommended)
            data: Data to process (can be a path or TaskContext object)
            task: Task description
            output: Output path
            **kwargs: Additional arguments

        Returns:
            AgentResult object containing execution results

        Example:
            # Method 1: Use task_id (recommended)
            result = agent.run(task_id="bike-sharing-demand")

            # Method 2: Use data path
            result = agent.run(data="path/to/data", task="Predict demand")
        """
        # If task_id is provided, use run_with_task_id
        if task_id is not None:
            return asyncio.run(self._factory.run_with_task_id(
                task_id=task_id,
                **self._agent_kwargs,
                **kwargs
            ))

        # Otherwise, fall back to manual execution
        # (This requires loading data and creating agent manually)
        raise NotImplementedError(
            "Direct data/path execution is not yet implemented. "
            "Please use task_id parameter instead:\n\n"
            "  agent.run(task_id='bike-sharing-demand')\n\n"
            "Or use dslighting.run_agent() for simpler usage."
        )

    def cleanup(self):
        """Clean up workspace"""
        self._factory.cleanup()
