"""
A simple, baseline workflow that serves as the starting point (seed)
for the meta-optimization evolutionary algorithm.
"""

def get_initial_workflow_code() -> str:
    """Returns the source code for a simple workflow using injected operators."""
    return '''
import shutil
from pathlib import Path
from dsat.workflows.base import DSATWorkflow
from dsat.services.llm import LLMService
from dsat.services.sandbox import SandboxService
from dsat.utils.parsing import parse_plan_and_code
from typing import Dict, Any, List

class Workflow(DSATWorkflow):
    """
    An initial workflow that generates Python code to solve a Kaggle-style task,
    executes it in a sandbox, and produces a submission file.
    This is a strong starting point for the optimization process.
    """
    def __init__(self, operators: Dict[str, Any], services: Dict[str, Any], agent_config: Dict[str, Any]):
        """
        The driver injects the llm_service and sandbox_service.
        """
        super().__init__(operators, services, agent_config)
        self.llm_service: LLMService = services["llm"]
        self.sandbox_service: SandboxService = services["sandbox"]
        
    async def solve(self, description: str, io_instructions: str, data_dir: Path, output_path: Path):
        """
        The main entry point for executing the workflow.
        """
        print(f"  Initial Workflow: Starting task. Target: {output_path.name}")

        prompt = (
            f"You are an expert AI developer and data scientist. Your task is to write a single, complete Python script to solve the following problem. "
            f"Provide only the Python code in a single code block.\\n\\n"
            f"# PROBLEM DESCRIPTION AND DATA REPORT\\n{description}\\n\\n"
            f"# CRITICAL I/O REQUIREMENTS (MUST BE FOLLOWED)\\n{io_instructions}\\n\\n"
            f"Ensure the script strictly follows the CRITICAL I/O REQUIREMENTS."
        )
        
        # 1. Generate the code
        llm_response = await self.llm_service.call(prompt)
        _, code_to_execute = parse_plan_and_code(llm_response)

        if "# ERROR" in code_to_execute:
            print("  ERROR: Failed to generate valid code from LLM.")
            return

        # 2. Execute the code in the sandbox
        # The sandbox will have its own isolated workspace.
        print("  Initial Workflow: Executing generated script in sandbox...")
        exec_result = self.sandbox_service.run_script(code_to_execute)

        if not exec_result.success:
            print(f"  ERROR: Code execution failed.\\\\n{exec_result.stderr}")
            return

        # 3. Verify the generated submission file exists.
        sandbox_workdir = self.sandbox_service.workspace.get_path("sandbox_workdir")
        generated_file = sandbox_workdir / output_path.name
        
        if generated_file.exists():
            print(f"  SUCCESS: Submission file '{output_path.name}' successfully generated in sandbox.")
        else:
            print(f"  ERROR: Execution succeeded, but the required output file '{output_path.name}' was not created in {sandbox_workdir}.")

'''
