# dslighting/ops/presets/dsflow.py

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field

from dslighting.core.data.perception import DataPerceptionRuntime
from dslighting.ops.base import Operator
from dslighting.services.sandbox import SandboxService
from dslighting.utils.typing import ExecutionResult

# -----------------------------------------------------------------------------
# Common "meta" operators (ported from aflow_ops, kept local for DSFlow).


class ScEnsembleResponse(BaseModel):
    thought: str = Field(description="Rationale for selecting the most consistent solution.")
    solution_letter: str = Field(description="Chosen letter (A, B, C, ...).")


class ScEnsembleOperator(Operator):
    """
    Selects the best solution among candidates via self-consistency voting.
    Call signature: `await op(solutions: List[str], problem: str) -> str`
    """

    async def __call__(self, solutions: List[str], problem: str) -> str:
        if not self.llm_service:
            raise ValueError("LLMService is required for ScEnsembleOperator.")

        solution_map: Dict[str, str] = {}
        blocks: List[str] = []
        for i, solution in enumerate(solutions):
            letter = chr(65 + i)
            solution_map[letter] = solution
            blocks.append(f"{letter}:\n{solution}")

        candidates_text = "\n\n".join(blocks)
        prompt = (
            f"Problem:\n{problem}\n\n"
            f"Candidate solutions:\n\n{candidates_text}\n\n"
            "Pick the most robust/correct/consistent solution. "
            "Return JSON with fields: thought, solution_letter."
        )
        resp = await self.llm_service.call_with_json(prompt, output_model=ScEnsembleResponse)
        letter = resp.solution_letter.strip().upper()
        return solution_map.get(letter, solutions[0])


class ReviewResponse(BaseModel):
    is_correct: bool = Field(description="True if solution is likely correct.")
    feedback: str = Field(description="Feedback for improving/fixing the solution.")


class ReviewOperator(Operator):
    """
    Reviews a solution and returns structured feedback.
    Call signature: `await op(problem: str, solution: str) -> ReviewResponse`
    """

    async def __call__(self, problem: str, solution: str) -> ReviewResponse:
        if not self.llm_service:
            raise ValueError("LLMService is required for ReviewOperator.")

        prompt = (
            "You are a meticulous reviewer. Evaluate the solution correctness.\n\n"
            f"# PROBLEM\n{problem}\n\n"
            f"# SOLUTION\n{solution}\n\n"
            "Return JSON with fields: is_correct, feedback."
        )
        return await self.llm_service.call_with_json(prompt, output_model=ReviewResponse)


class ReviseResponse(BaseModel):
    solution: str = Field(description="Revised solution.")


class ReviseOperator(Operator):
    """
    Revises a solution based on feedback.
    Call signature: `await op(problem: str, solution: str, feedback: str) -> str`
    """

    async def __call__(self, problem: str, solution: str, feedback: str) -> str:
        if not self.llm_service:
            raise ValueError("LLMService is required for ReviseOperator.")

        prompt = (
            "You are an expert programmer. Revise the solution based on feedback.\n\n"
            f"# PROBLEM\n{problem}\n\n"
            f"# CURRENT SOLUTION\n{solution}\n\n"
            f"# FEEDBACK\n{feedback}\n\n"
            "Return JSON with field: solution."
        )
        resp = await self.llm_service.call_with_json(prompt, output_model=ReviseResponse)
        return resp.solution


# -----------------------------------------------------------------------------
# Minimal, reusable data-science operators.


class DSPlanResponse(BaseModel):
    thought: str = Field(description="High-level reasoning.")
    plan: str = Field(description="Step-by-step plan to solve the task.")


class DSProblemAnalysisOperator(Operator):
    """
    Produces a concrete data-science plan.
    Call signature: `await op(problem: str, io_instructions: str) -> str`
    """

    async def __call__(self, problem: str, io_instructions: str) -> str:
        if not self.llm_service:
            raise ValueError("LLMService is required for DSProblemAnalysisOperator.")

        prompt = (
            "You are an expert data scientist. Produce a concrete plan.\n\n"
            f"# PROBLEM\n{problem}\n\n"
            f"# I/O REQUIREMENTS\n{io_instructions}\n\n"
            "Return JSON with fields: thought, plan."
        )
        resp = await self.llm_service.call_with_json(prompt, output_model=DSPlanResponse)
        return resp.plan


class DSCodeResponse(BaseModel):
    thought: str = Field(description="Reasoning for the approach.")
    python_code: str = Field(description="Complete runnable Python script.")


class DSCodeGenOperator(Operator):
    """
    Generates a complete Python solution from a plan.
    Call signature: `await op(problem: str, io_instructions: str, plan: str) -> str`
    """

    async def __call__(self, problem: str, io_instructions: str, plan: str) -> str:
        if not self.llm_service:
            raise ValueError("LLMService is required for DSCodeGenOperator.")

        prompt = (
            "Write a single, complete Python script to solve the task.\n"
            "The script MUST follow the I/O requirements exactly.\n\n"
            f"# PROBLEM\n{problem}\n\n"
            f"# PLAN\n{plan}\n\n"
            f"# I/O REQUIREMENTS\n{io_instructions}\n\n"
            "Return JSON with fields: thought, python_code."
        )
        resp = await self.llm_service.call_with_json(prompt, output_model=DSCodeResponse)
        return resp.python_code


class DSCodeRefineOperator(Operator):
    """
    Refines code given an execution error.
    Call signature: `await op(problem: str, io_instructions: str, plan: str, prev_code: str, error: str) -> str`
    """

    async def __call__(
        self, problem: str, io_instructions: str, plan: str, prev_code: str, error: str
    ) -> str:
        if not self.llm_service:
            raise ValueError("LLMService is required for DSCodeRefineOperator.")

        prompt = (
            "Fix the Python script based on the execution error. "
            "Keep the I/O requirements strictly.\n\n"
            f"# PROBLEM\n{problem}\n\n"
            f"# PLAN\n{plan}\n\n"
            f"# I/O REQUIREMENTS\n{io_instructions}\n\n"
            f"# PREVIOUS CODE\n```python\n{prev_code}\n```\n\n"
            f"# ERROR\n{error}\n\n"
            "Return JSON with fields: thought, python_code."
        )
        resp = await self.llm_service.call_with_json(prompt, output_model=DSCodeResponse)
        return resp.python_code


class DSCodeEditResponse(BaseModel):
    thought: str = Field(description="Reasoning for the edit.")
    python_code: str = Field(description="Edited complete runnable Python script.")


class DSDataAcqValidOperator(Operator):
    """
    Validates and improves data loading so all available inputs are used correctly.
    Call signature: `await op(problem: str, io_instructions: str, prev_code: str) -> str`
    """

    async def __call__(self, problem: str, io_instructions: str, prev_code: str) -> str:
        if not self.llm_service:
            raise ValueError("LLMService is required for DSDataAcqValidOperator.")

        prompt = (
            "You are a careful data scientist. Improve data loading logic so the script uses the correct "
            "input files available in the current working directory, without hardcoding absolute paths.\n\n"
            f"# PROBLEM + DATA REPORT\n{problem}\n\n"
            f"# I/O REQUIREMENTS\n{io_instructions}\n\n"
            f"# CURRENT CODE\n```python\n{prev_code}\n```\n\n"
            "Return JSON with fields: thought, python_code."
        )
        resp = await self.llm_service.call_with_json(prompt, output_model=DSCodeEditResponse)
        return resp.python_code


class DSSubmissionValidOperator(Operator):
    """
    Validates and fixes submission writing so grading will accept the output.
    Call signature: `await op(problem: str, io_instructions: str, prev_code: str) -> str`
    """

    async def __call__(self, problem: str, io_instructions: str, prev_code: str) -> str:
        if not self.llm_service:
            raise ValueError("LLMService is required for DSSubmissionValidOperator.")

        prompt = (
            "You are a strict Kaggle submission validator. Ensure the script writes EXACTLY the required "
            "submission CSV (correct filename, columns, order, and types) into the current working directory.\n\n"
            f"# PROBLEM + DATA REPORT\n{problem}\n\n"
            f"# I/O REQUIREMENTS\n{io_instructions}\n\n"
            f"# CURRENT CODE\n```python\n{prev_code}\n```\n\n"
            "Return JSON with fields: thought, python_code."
        )
        resp = await self.llm_service.call_with_json(prompt, output_model=DSCodeEditResponse)
        return resp.python_code


class DSDataInspectOperator(Operator):
    """
    Reuses DSLighting's data-perception runtime to inspect the sandbox CWD.
    Call signature: `await op() -> str`
    """

    def __init__(
        self,
        sandbox_service: SandboxService,
        data_perception: DataPerceptionRuntime | None = None,
    ):
        super().__init__(name="DSDataInspect")
        self._sandbox = sandbox_service
        self._data_perception = data_perception or DataPerceptionRuntime()

    async def __call__(self) -> str:
        sandbox_workdir = self._sandbox.workspace.get_path("sandbox_workdir")
        report = self._data_perception.analyze_data(
            sandbox_workdir,
            task_type="kaggle",
        )

        marker = "## Data Schema Analysis"
        if marker in report:
            schema = report.split(marker, 1)[1]
            # Stop at the next top-level section, if any.
            next_header = "\n## "
            if next_header in schema:
                schema = schema.split(next_header, 1)[0]
            schema = (marker + schema).strip()
        else:
            schema = report.strip()

        # Keep prompts bounded.
        if len(schema) > 4000:
            schema = schema[:4000] + "\n...[truncated]..."
        return schema


class ExecutePythonOperator(Operator):
    """
    Executes code in the SandboxService.
    Call signature: `await op(code: str) -> ExecutionResult`
    """

    def __init__(self, sandbox_service: SandboxService):
        super().__init__(name="ExecutePython")
        self._sandbox = sandbox_service

    async def __call__(self, code: str) -> ExecutionResult:
        return await self._sandbox.run_script(code)
