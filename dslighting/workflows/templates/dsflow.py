"""
A simple, baseline workflow that serves as the starting point (seed)
for the meta-optimization evolutionary algorithm.
"""


def get_initial_dsflow_workflow_code() -> str:
    """Returns the source code for a DSFlow seed workflow using dsflow_ops operators."""
    return '''
from pathlib import Path
from typing import Any, Dict

from dslighting.workflows.base import BaseWorkflow


class Workflow(BaseWorkflow):
    """
    A robust seed workflow that:
    1) Generates a structured plan
    2) Generates runnable code
    3) Executes in sandbox and refines on failure

    It is intentionally minimal, but uses injected dsflow_ops operators so the
    DSFlow optimizer can extend/modify it reliably.
    """

    async def solve(self, description: str, io_instructions: str, data_dir: Path, output_path: Path) -> None:
        inspection = await self.operators["DSDataInspect"]()
        full_description = f"{description}\\n\\n--- RUNTIME DATA INSPECTION ---\\n{inspection}\\n"

        plan = await self.operators["DSProblemAnalysis"](full_description, io_instructions)
        code = await self.operators["DSCodeGen"](full_description, io_instructions, plan)
        code = await self.operators["DSDataAcqValid"](full_description, io_instructions, code)
        code = await self.operators["DSSubmissionValid"](full_description, io_instructions, code)

        workspace = self.services.get("workspace")
        sandbox_workdir = workspace.get_path("sandbox_workdir") if workspace else Path(".")
        submission_path = sandbox_workdir / output_path.name

        last_error = ""
        for attempt in range(3):
            result = await self.operators["ExecutePython"](code)
            if result.success and submission_path.exists():
                return

            if result.success and not submission_path.exists():
                last_error = (
                    f"Execution succeeded but output file '{output_path.name}' was not created in '{sandbox_workdir}'."
                )
            else:
                last_error = result.stderr or "Unknown execution error."

            if attempt < 2:
                code = await self.operators["DSCodeRefine"](
                    full_description, io_instructions, plan, code, last_error
                )

        raise RuntimeError(last_error)
'''
