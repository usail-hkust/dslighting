import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List

from pydantic import BaseModel, Field

from dsat.operators.base import Operator
from dsat.services.llm import LLMService
from dsat.services.sandbox import SandboxService
from dsat.services.states.autokaggle_state import AutoKaggleState, TaskContract, PhaseMemory
from dsat.prompts.autokaggle_prompt import (
    get_deconstructor_prompt,
    get_phase_planner_prompt,
    get_step_planner_prompt,
    get_developer_prompt,
    get_validator_prompt,
    get_reviewer_prompt,
    get_summarizer_prompt,
)
from dsat.models.formats import StepPlan

logger = logging.getLogger(__name__)


class PhasePlanningResponse(BaseModel):
    """Response model for phase planning."""
    phases: List[str]


class ValidationResponse(BaseModel):
    """Response model for file validation."""
    passed: bool
    reason: str = ""


class ReviewResponse(BaseModel):
    """Response model for code review."""
    score: int
    suggestion: str = Field(default="", description="Constructive feedback or a suggestion for improvement.")


class TaskDeconstructionOperator(Operator):
    """Parses the natural language description into a structured TaskContract."""
    
    async def __call__(self, description: str) -> TaskContract:
        logger.info("Deconstructing task description into a structured contract...")
        prompt = get_deconstructor_prompt(description, TaskContract.model_json_schema())
        contract = await self.llm_service.call_with_json(prompt, output_model=TaskContract)
        logger.info(f"Task deconstructed. Goal: {contract.task_goal}")
        return contract


class AutoKagglePlannerOperator(Operator):
    """Handles high-level phase planning and low-level step planning."""
    
    async def __call__(self, *args, **kwargs) -> Any:
        """
        Main entry point for the planner operator.
        Can be called with different arguments for different planning tasks.
        """
        if len(args) == 1 and isinstance(args[0], TaskContract):
            # Called for phase planning
            return await self.plan_phases(args[0])
        elif len(args) == 2 and isinstance(args[0], AutoKaggleState) and isinstance(args[1], str):
            # Called for step planning
            return await self.plan_step_details(args[0], args[1])
        else:
            raise ValueError(f"AutoKagglePlannerOperator called with unexpected arguments: {args}, {kwargs}")
    
    async def plan_phases(self, contract: TaskContract) -> List[str]:
        logger.info("Planning dynamic phases for the workflow...")
        prompt = get_phase_planner_prompt(contract)
        response = await self.llm_service.call_with_json(prompt, output_model=PhasePlanningResponse)
        phases = response.phases
        logger.info(f"Dynamic phases planned: {phases}")
        return phases

    async def plan_step_details(self, state: AutoKaggleState, phase_goal: str) -> StepPlan:
        logger.info(f"Planning detailed steps for phase: '{phase_goal}'...")
        prompt = get_step_planner_prompt(state, phase_goal)
        step_plan = await self.llm_service.call_with_json(prompt, output_model=StepPlan)
        return step_plan


class DynamicValidationOperator(Operator):
    """Dynamically validates generated files against the TaskContract."""
    
    async def __call__(self, contract: TaskContract, workspace_dir: Path) -> Dict[str, Any]:
        logger.info("Performing dynamic validation of output files...")
        results = {}
        for output_file in contract.output_files:
            file_path = workspace_dir / output_file.filename
            if not file_path.exists():
                results[output_file.filename] = {"passed": False, "reason": "File was not generated."}
                continue
            
            try:
                content_snippet = "\\n".join(file_path.read_text().splitlines()[:20])
            except Exception as e:
                results[output_file.filename] = {"passed": False, "reason": f"Could not read file: {str(e)}"}
                continue
                
            prompt = get_validator_prompt(contract, output_file.filename, content_snippet)
            validation = await self.llm_service.call_with_json(prompt, output_model=ValidationResponse)
            results[output_file.filename] = {"passed": validation.passed, "reason": validation.reason}
        logger.info(f"Validation results: {results}")
        return results


class AutoKaggleDeveloperOperator(Operator):
    """Writes, executes, and validates code."""
    
    def __init__(self, llm_service: LLMService, sandbox_service: SandboxService, validator: DynamicValidationOperator):
        super().__init__(llm_service, name="AutoKaggleDeveloper")
        self.sandbox = sandbox_service
        self.validator = validator

    async def __call__(self, state: AutoKaggleState, phase_goal: str, plan: str, attempt_history: List) -> Dict:
        logger.info(f"Developer starting work for phase: '{phase_goal}'")
        prompt = get_developer_prompt(state, phase_goal, plan, attempt_history)
        
        raw_reply = await self.llm_service.call(prompt)
        match = re.search(r"```(?:python|py)?\s*([\s\S]*?)\s*```", raw_reply, re.DOTALL)
        code = match.group(1).strip() if match else ""

        if not code:
            return {"code": "", "status": False, "output": "", "error": "No code was generated.", "validation_result": {}}

        exec_result = self.sandbox.run_script(code)

        validation_result = {}
        if exec_result.success:
            # Note: This still validates against the *final* contract outputs. The reviewer logic handles this.
            validation_result = await self.validator(state.contract, self.sandbox.workspace.run_dir)
        
        return {
            "code": code,
            "status": exec_result.success,
            "output": exec_result.stdout,
            "error": exec_result.stderr,
            "validation_result": validation_result
        }


class AutoKaggleReviewerOperator(Operator):
    """Reviews the developer's work and provides a score and suggestions."""
    
    async def __call__(self, state: AutoKaggleState, phase_goal: str, dev_result: Dict, plan: str = "") -> Dict:
        logger.info("Reviewer assessing developer's work...")
        prompt = get_reviewer_prompt(phase_goal, dev_result, plan)
        review = await self.llm_service.call_with_json(prompt, output_model=ReviewResponse)
        review_dict = {
            "score": review.score,
            "suggestion": review.suggestion
        }
        logger.info(f"Review complete. Score: {review.score}")
        return review_dict


class AutoKaggleSummarizerOperator(Operator):
    """Summarizes a successful phase into a report."""
    
    async def __call__(self, state: AutoKaggleState, phase_memory: PhaseMemory) -> str:
        logger.info(f"Summarizer creating report for phase: '{phase_memory.phase_goal}'")
        prompt = get_summarizer_prompt(state, phase_memory)
        report = await self.llm_service.call(prompt)
        logger.info("Report created.")
        return report