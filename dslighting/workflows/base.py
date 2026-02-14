from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Union, Optional
import asyncio

from dslighting.error import WorkflowError
from dslighting.core.data import TaskContext


# --- New, standardized workflow interface (core) ---
class BaseWorkflow(ABC):
    """
    New standardized workflow abstract base class defining the "physical interface contract".

    Any workflow implementing this interface becomes a generic problem solver
    that is completely decoupled from the specific form of the task (QA, Kaggle, etc.).
    It only understands files and directories.

    Usage:
        # For users: use run() - simple interface
        agent = MyCustomAgent(...)
        result = agent.run(data="path/to/data")

        # For advanced users: use solve() - more control
        await agent.solve(
            description="Task description",
            io_instructions="Input: train.csv\\nOutput: submission.csv",
            data_dir=Path("/path/to/data"),
            output_path=Path("submission.csv")
        )
    """

    def __init__(self, operators: Dict[str, Any], services: Dict[str, Any], agent_config: Dict[str, Any]):
        """
        Initialize through dependency injection.

        Args:
            operators: A dictionary containing all operator instances needed by this workflow.
            services: A dictionary containing required service instances (e.g., LLMService, SandboxService).
            agent_config: A dictionary containing agent behavior-specific configuration.
        """
        self.operators = operators
        self.services = services
        self.agent_config = agent_config

        # Session-scoped actor cache used by the declarative DAG adapter.
        self._dag_actor_sessions: Dict[str, Any] = {}

    @abstractmethod
    async def solve(
        self,
        description: str,
        io_instructions: str,  # NEW ARGUMENT
        data_dir: Path,
        output_path: Path,
    ) -> None:
        """
        Solve a given task based on the physical file interface.

        This is the core method that all custom agents must implement.

        This is the core method for all standardized workflows. Workflows implementing this method need to:
        1.  Treat `data_dir` as their only input source.
        2.  Execute their internal logic (e.g., call LLM, run code) to solve the task described in `description`.
        3.  Write their final, evaluable answer as a single file to the complete path specified by `output_path`.

        Args:
            description: Natural language goal description and data analysis report.
            io_instructions: Explicit, standardized instructions for reading input and writing output.
            data_dir: A directory containing all input files needed to solve the task (e.g., `problem.txt`, `train.csv`).
            output_path: The complete path where the final output file (e.g., `answer.txt`, `submission.csv`) must be saved.
        """
        raise NotImplementedError

    # ---------------------------------------------------------------------
    # Declarative DAG contract (default adapter for build_actor-based workflows)
    # ---------------------------------------------------------------------

    def supports_declarative_dag(self) -> bool:
        """Return whether this workflow can be adapted to declarative DAG execution."""
        # Explicitly implemented declarative methods always supported.
        if self.__class__.build_operator_graph is not BaseWorkflow.build_operator_graph:
            return True
        return callable(getattr(self, "build_actor", None))

    def build_operator_graph(
        self,
        *,
        task_id: str,
        description: str,
        io_instructions: str,
        data_dir: Path,
        output_path: Path,
        dag_options: Any = None,
    ) -> "WorkflowGraphSpec":
        """Build the initial operator graph for this workflow.

        Default behavior wraps legacy ``build_actor(...)`` implementations so existing
        workflow actors can execute through the declarative runtime adapter.
        """
        from dslighting.runtime.dag.types import WorkflowGraphSpec

        build_actor = getattr(self, "build_actor", None)
        if not callable(build_actor):
            raise NotImplementedError(
                f"Workflow '{self.__class__.__name__}' does not implement build_operator_graph() or build_actor()."
            )

        attempts = [
            {
                "task_id": task_id,
                "description": description,
                "io_instructions": io_instructions,
                "data_dir": data_dir,
                "output_path": output_path,
                "dag_options": dag_options,
            },
            {
                "task_id": task_id,
                "description": description,
                "io_instructions": io_instructions,
                "data_dir": data_dir,
                "output_path": output_path,
            },
            {
                "description": description,
                "io_instructions": io_instructions,
                "data_dir": data_dir,
                "output_path": output_path,
            },
        ]

        actor = None
        last_type_error: Optional[TypeError] = None
        for kwargs in attempts:
            try:
                actor = build_actor(**kwargs)
                if actor is not None:
                    break
            except TypeError as exc:
                last_type_error = exc
                continue

        if actor is None:
            if last_type_error is not None:
                raise last_type_error
            raise RuntimeError(
                f"Workflow '{self.__class__.__name__}' build_actor() returned None for task '{task_id}'."
            )

        self._dag_actor_sessions[task_id] = actor
        return WorkflowGraphSpec(
            task_id=task_id,
            initial_nodes=list(actor.initial_nodes()),
            initial_state=actor.initial_state(),
        )

    def on_operator_node_result(
        self,
        *,
        result: "NodeResult",
        dag_state: Any,
    ) -> "GraphDelta":
        """Handle one node result and return dynamic graph updates.

        Default behavior forwards to a legacy actor session created in
        ``build_operator_graph``.
        """
        from dslighting.runtime.dag.types import GraphDelta

        actor = self._dag_actor_sessions.get(result.task_id)
        if actor is None:
            return GraphDelta(
                new_nodes=[],
                done=True,
                final_result={
                    "status": "failed",
                    "error": f"No DAG actor session found for task '{result.task_id}'.",
                    "failed_node_id": result.node_id,
                },
            )

        new_nodes, done = actor.on_node_result(result)
        final_result = actor.get_result() if done else None
        return GraphDelta(new_nodes=list(new_nodes or []), done=bool(done), final_result=final_result)

    def finalize_operator_graph(self, *, task_id: str, dag_state: Any) -> Any:
        """Finalize and return workflow DAG result.

        Default behavior returns legacy actor result if present.
        """
        actor = self._dag_actor_sessions.pop(task_id, None)
        if actor is None:
            return None
        return actor.get_result()

    def run(
        self,
        data: Union[str, Path, TaskContext],
        task: Optional[str] = None,
        output: Optional[Union[str, Path]] = None,
        **kwargs,
    ) -> "WorkflowResult":
        """
        Convenient synchronous wrapper around solve().

        This is the high-level user interface. Users only need to call run(),
        without worrying about asyncio or parameter extraction.

        Note: If you're already in an async context (e.g., inside an async
        function), use await agent.solve(...) directly instead of agent.run().

        Args:
            data: Data path (str/Path) or TaskContext object
            task: Optional task description (inferred from data if not provided)
            output: Optional output path (inferred from data if not provided)
            **kwargs: Additional arguments (for future extensibility)

        Returns:
            WorkflowResult object with execution results

        Example:
            >>> from my_custom_agent import MyCustomAgent
            >>> agent = MyCustomAgent(...)
            >>> result = agent.run(data="path/to/data")
            >>> print(f"Success: {result.success}")
        """
        # Lazy import to avoid circular dependency
        from dslighting.core.data import DataLoader

        # Step 1: Load data if needed
        if isinstance(data, (str, Path)):
            loader = DataLoader(data)
            loaded_data = loader.load()
        else:
            loaded_data = data

        # Step 2: Extract parameters
        description = task or loaded_data.description
        io_instructions = loaded_data.io_instructions
        data_dir = loaded_data.data_dir
        output_path = output or loaded_data.output_path

        # Step 3: Run solve() asynchronously
        # Check if we're already in an event loop
        try:
            asyncio.get_running_loop()
            # We're in an async context, this is an error
            raise WorkflowError(
                "agent.run() cannot be called from an async context. "
                "Use 'await agent.solve(...)' instead.",
                error_code="WRK-004",
                suggestion="Use 'await agent.solve(...)' directly in async contexts instead of agent.run()",
            )
        except RuntimeError as e:
            # Check if this is the expected "no running loop" error
            if "no running event loop" not in str(e):
                # Some other RuntimeError, re-raise it
                raise
            # No running loop, this is the expected case - continue to asyncio.run()
            pass
        except WorkflowError:
            # Re-raise our custom error
            raise

        asyncio.run(
            self.solve(
                description=description,
                io_instructions=io_instructions,
                data_dir=data_dir,
                output_path=output_path,
            )
        )

        # Step 4: Return result
        return WorkflowResult(
            success=True,
            workflow=self.__class__.__name__,
            output_path=output_path,
        )


class WorkflowResult:
    """
    Result from workflow execution.

    Returned by the run() method.
    """

    def __init__(
        self,
        success: bool,
        workflow: str,
        output_path: Path,
        score: Optional[float] = None,
        error: Optional[str] = None,
    ):
        """
        Initialize WorkflowResult.

        Args:
            success: Whether execution was successful
            workflow: Workflow class name
            output_path: Output file path
            score: Optional score
            error: Optional error message
        """
        self.success = success
        self.workflow = workflow
        self.output_path = output_path
        self.score = score
        self.error = error

    def __repr__(self) -> str:
        """String representation of result."""
        if self.success:
            return f"WorkflowResult(success=True, workflow={self.workflow}, output={self.output_path})"
        else:
            return f"WorkflowResult(success=False, workflow={self.workflow}, error={self.error})"
