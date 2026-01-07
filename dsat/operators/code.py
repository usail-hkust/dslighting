import logging
from typing import Any

from dsat.common.typing import ExecutionResult
from dsat.operators.base import Operator
from dsat.services.sandbox import SandboxService, ProcessIsolatedNotebookExecutor

logger = logging.getLogger(__name__)

class ExecuteAndTestOperator(Operator):
    """
    An operator that acts as a clean interface to the SandboxService,
    handling both script and notebook execution modes.
    """
    def __init__(self, sandbox_service: SandboxService):
        super().__init__(name="ExecuteAndTest")
        self.sandbox = sandbox_service

    async def __call__(self, code: str, mode: str = "script", executor_context: Any = None) -> ExecutionResult:
        """
        Executes code using the configured sandbox.

        Args:
            code (str): The Python code to execute.
            mode (str): The execution mode, either 'script' or 'notebook'.
            executor_context (Any): For notebook mode, this must be the active ProcessIsolatedNotebookExecutor instance.

        Returns:
            ExecutionResult: The outcome of the execution.
        """
        if mode == "script":
            logger.info("Executing code as a script...")
            # run_script is synchronous in the sandbox service, but we call it from an async operator
            # A fully async sandbox would use asyncio.to_thread
            return self.sandbox.run_script(code)
        
        elif mode == "notebook":
            if not isinstance(executor_context, ProcessIsolatedNotebookExecutor):
                raise TypeError("Notebook mode requires a valid ProcessIsolatedNotebookExecutor instance passed via executor_context.")
            
            logger.info("Executing notebook cell...")
            return await executor_context.execute_cell(code)
            
        else:
            raise ValueError(f"Unknown execution mode: {mode}")