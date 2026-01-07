# dsat/workflows/manual/autokaggle_workflow.py
import logging
from pathlib import Path
from typing import Dict, Any
import shutil # <-- ADD THIS IMPORT

from dsat.workflows.base import DSATWorkflow
from dsat.services.llm import LLMService
from dsat.services.sandbox import SandboxService
from dsat.services.workspace import WorkspaceService
from dsat.services.states.autokaggle_state import AutoKaggleState, PhaseMemory, AttemptMemory
from dsat.operators.autokaggle_ops import (
    TaskDeconstructionOperator,
    AutoKagglePlannerOperator,
    AutoKaggleDeveloperOperator,
    DynamicValidationOperator,
    AutoKaggleReviewerOperator,
    AutoKaggleSummarizerOperator,
)

logger = logging.getLogger(__name__)


class AutoKaggleWorkflow(DSATWorkflow):
    """
    Implements the Contract-Driven Dynamic AutoKaggle Standard Operating Procedure.
    """

    def __init__(self, operators: Dict[str, Any], services: Dict[str, Any], agent_config: Dict[str, Any]):
        super().__init__(operators, services, agent_config)
        self.workspace: WorkspaceService = services["workspace"]
        self.llm_service: LLMService = services["llm"]
        self.sandbox: SandboxService = services["sandbox"]
        
        # Operator Initialization with Dependency Injection
        validator = DynamicValidationOperator(llm_service=self.llm_service)
        self.operators = {
            "deconstructor": TaskDeconstructionOperator(llm_service=self.llm_service),
            "planner": AutoKagglePlannerOperator(llm_service=self.llm_service),
            "developer": AutoKaggleDeveloperOperator(llm_service=self.llm_service, sandbox_service=self.sandbox, validator=validator),
            "reviewer": AutoKaggleReviewerOperator(llm_service=self.llm_service),
            "summarizer": AutoKaggleSummarizerOperator(llm_service=self.llm_service),
        }
        sop_config = agent_config.get("autokaggle", {})
        self.config = {
            "max_attempts_per_phase": sop_config.get("max_attempts_per_phase", 5), # Give it a few more tries
            "success_threshold": sop_config.get("success_threshold", 3.0)
        }

    async def solve(self, description: str, io_instructions: str, data_dir: Path, output_path: Path) -> None:
        logger.info("Starting Stateful Contract-Driven Dynamic SOP Workflow...")

        full_context_for_deconstructor = f"{description}\n\n{io_instructions}"
        
        task_contract = await self.operators["deconstructor"](full_context_for_deconstructor)
        dynamic_phases = await self.operators["planner"].plan_phases(task_contract)
        
        state = AutoKaggleState(
            contract=task_contract,
            dynamic_phases=dynamic_phases,
            io_instructions=io_instructions,
            full_task_description=description
        )

        for i, phase_goal in enumerate(state.dynamic_phases):
            logger.info(f"--- Starting Dynamic Phase {i+1}/{len(state.dynamic_phases)}: '{phase_goal}' ---")
            
            current_phase_memory = PhaseMemory(phase_goal=phase_goal)
            phase_succeeded = False
            
            for attempt in range(self.config["max_attempts_per_phase"]):
                logger.info(f"--- Phase '{phase_goal}', Attempt {attempt + 1} ---")

                step_plan = await self.operators["planner"].plan_step_details(state, phase_goal)
                dev_result = await self.operators["developer"](state, phase_goal, step_plan.plan, current_phase_memory.attempts)
                review_result = await self.operators["reviewer"](state, phase_goal, dev_result, plan=step_plan.plan)
                
                ## --- MODIFIED: Stricter Artifact-based Validation --- ##
                all_artifacts_produced = True
                sandbox_workdir = self.sandbox.workspace.get_path("sandbox_workdir")
                if dev_result['status']: # Only check for artifacts if code ran successfully
                    if not step_plan.output_files:
                        logger.warning(f"Phase '{phase_goal}' has no planned output files. Relying on reviewer score alone.")
                    for filename in step_plan.output_files:
                        if not (sandbox_workdir / filename).exists():
                            logger.error(f"Attempt failed: Planned artifact '{filename}' was NOT created.")
                            all_artifacts_produced = False
                            break # No need to check other files
                else:
                    all_artifacts_produced = False

                attempt_memory = AttemptMemory(
                    attempt_number=attempt,
                    plan=step_plan.plan,
                    code=dev_result['code'],
                    execution_output=dev_result['output'],
                    execution_error=dev_result['error'],
                    validation_result=dev_result.get('validation_result', {}),
                    review_score=review_result.get('score', 1.0),
                    review_suggestion=review_result.get('suggestion', 'No suggestion provided.')
                )
                current_phase_memory.attempts.append(attempt_memory)

                if dev_result['status'] and all_artifacts_produced and review_result.get('score', 1.0) >= self.config["success_threshold"]:
                    logger.info(f"--- Phase '{phase_goal}' Succeeded ---")
                    phase_succeeded = True
                    
                    # Register newly created artifacts in the global state
                    for filename in step_plan.output_files:
                        description = f"Generated during phase: {phase_goal}"
                        state.global_artifacts[filename] = description
                        current_phase_memory.output_artifacts[filename] = description
                        logger.info(f"Registered new artifact: {filename}")
                    
                    break # Exit attempt loop on success
                else:
                    logger.warning(f"Attempt failed. Code Success: {dev_result['status']}. Artifacts Produced: {all_artifacts_produced}. Score: {review_result.get('score', 1.0)}. Retrying...")

            if phase_succeeded:
                summary_report = await self.operators["summarizer"](state, current_phase_memory)
                current_phase_memory.final_report = summary_report
                current_phase_memory.is_successful = True
                state.phase_history.append(current_phase_memory)
            else:
                logger.error(f"--- Phase '{phase_goal}' FAILED after all attempts. Aborting workflow. ---")
                return # Abort entire workflow if a phase fails

        logger.info("All dynamic phases completed successfully.")
        
        ## --- ADDED: Final Artifact Collection --- ##
        final_submission_filename = None
        if state.contract.output_files:
            # Assume the first output file in the contract is the required one.
            final_submission_filename = state.contract.output_files[0].filename
        
        if final_submission_filename and final_submission_filename in state.global_artifacts:
            source_file = sandbox_workdir / final_submission_filename
            destination_file = output_path
            
            logger.info(f"Collecting final submission artifact '{source_file}' to '{destination_file}'.")
            try:
                destination_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(source_file, destination_file)
                logger.info("Final artifact collected successfully.")
            except Exception as e:
                logger.error(f"Failed to collect final artifact: {e}")
        else:
            logger.error(f"Workflow finished, but required output file '{final_submission_filename}' was not found in the global artifact registry.")