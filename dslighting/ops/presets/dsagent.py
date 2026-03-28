import logging
from typing import Optional, Tuple

from dslighting.core.visualization_policy import (
    build_visualization_instruction_text,
    resolve_visualization_policy_from_agent_config,
)
from dslighting.ops.base import Operator
from dslighting.prompts.workflows.dsagent import (
    PLAN_PROMPT_TEMPLATE, PROGRAMMER_PROMPT_TEMPLATE, 
    DEBUGGER_PROMPT_TEMPLATE, LOGGER_PROMPT_TEMPLATE
)
from dslighting.services.llm import LLMService
from dslighting.services.sandbox import SandboxService
from dslighting.services.vdb import VDBService
from dslighting.utils.typing import ExecutionResult
from dslighting.utils.parsing import parse_plan_and_code
from dslighting.state.context import MAX_HISTORY_CHARS, MAX_OUTPUT_CHARS, truncate_output

# Define how much recent context to keep verbatim during summarization
RECENT_CONTEXT_VERBATIM = 8000  # Increased from 2000

logger = logging.getLogger(__name__)

class DevelopPlanOperator(Operator):
    """Retrieves cases and generates an experiment plan."""
    def __init__(
        self,
        llm_service: LLMService,
        vdb_service: Optional[VDBService] = None,
        *,
        agent_config: Optional[dict] = None,
    ):
        super().__init__(llm_service, name="DevelopPlan")
        self.vdb = vdb_service
        self.visualization_policy = resolve_visualization_policy_from_agent_config(agent_config)

    async def __call__(self, research_problem: str, io_instructions: str, running_log: str) -> str:
        safe_running_log = truncate_output(running_log, MAX_HISTORY_CHARS)
        query = f"{research_problem}\n{safe_running_log}"
        if self.vdb:
            retrieved_cases = self.vdb.retrieve_cases(query, top_k=1)
            case = retrieved_cases[0] if retrieved_cases else "No relevant cases found."
        else:
            case = "No relevant cases found."
        
        prompt = PLAN_PROMPT_TEMPLATE.format(
            research_problem=research_problem,
            io_instructions=io_instructions,
            running_log=safe_running_log,
            case=case,
            visualization_guidance=build_visualization_instruction_text(self.visualization_policy),
        )
        plan = await self.llm_service.call(prompt)
        return plan.strip()

class ExecutePlanOperator(Operator):
    """Manages the programmer-debugger loop to implement a plan."""
    def __init__(
        self,
        llm_service: LLMService,
        sandbox_service: SandboxService,
        max_retries: int = 10,
        *,
        agent_config: Optional[dict] = None,
    ):
        super().__init__(llm_service, name="ExecutePlan")
        self.sandbox = sandbox_service
        self.max_retries = max_retries
        self.visualization_policy = resolve_visualization_policy_from_agent_config(agent_config)

    async def __call__(self, initial_code: str, plan: str, research_problem: str, io_instructions: str, running_log: str = "") -> Tuple[ExecutionResult, str]:
        safe_running_log = truncate_output(running_log, MAX_HISTORY_CHARS)
        current_code = initial_code
        exec_result = None  # Initialize to prevent UnboundLocalError
        for attempt in range(self.max_retries):
            if attempt == 0:
                prompt = PROGRAMMER_PROMPT_TEMPLATE.format(
                    code=current_code, plan=plan, research_problem=research_problem,
                    io_instructions=io_instructions, running_log=safe_running_log,
                    visualization_guidance=build_visualization_instruction_text(self.visualization_policy),
                )
            else:
                safe_error_log = truncate_output(exec_result.stderr, MAX_OUTPUT_CHARS)
                prompt = DEBUGGER_PROMPT_TEMPLATE.format(
                    plan=plan, code=current_code, error_log=safe_error_log,
                    research_problem=research_problem, io_instructions=io_instructions, running_log=safe_running_log,
                    visualization_guidance=build_visualization_instruction_text(self.visualization_policy),
                )

            response = await self.llm_service.call(prompt)
            _, current_code = parse_plan_and_code(response)

            exec_result = await self.sandbox.run_script(current_code)
            if exec_result.success:
                return exec_result, current_code

        logger.error(f"Execution failed after {self.max_retries} attempts.")
        return exec_result, current_code # Return last failed result

class ReviseLogOperator(Operator):
    """Summarizes the results of an experiment step."""
    async def __call__(self, running_log: str, plan: str, exec_result: ExecutionResult, diff: str) -> str:
        safe_running_log = truncate_output(running_log, MAX_HISTORY_CHARS)
        execution_log = exec_result.stdout or exec_result.stderr
        safe_execution_log = truncate_output(execution_log, MAX_OUTPUT_CHARS)
        safe_diff = truncate_output(diff, MAX_OUTPUT_CHARS)
        prompt = LOGGER_PROMPT_TEMPLATE.format(
            plan=plan,
            execution_log=safe_execution_log,
            diff=safe_diff,
            running_log=safe_running_log
        )
        new_summary = await self.llm_service.call(prompt)
        
        updated_log = running_log + "\n\n---\n" + new_summary.strip()
        
        if len(updated_log) > MAX_HISTORY_CHARS:
            logger.warning("Running log exceeds character limit; summarizing older history...")

            # Split the log: recent history (verbatim) and older history (to be summarized)
            split_point = max(0, len(updated_log) - RECENT_CONTEXT_VERBATIM)
            older_history = updated_log[:split_point]
            recent_history = updated_log[split_point:]

            if not older_history:
                return updated_log

            # Summarize only the older part
            summarize_prompt = (
                "The following is the older history of a data science project. "
                "Summarize this history concisely. You MUST preserve the following elements if present:\n"
                "1. Key findings and model performance metrics.\n"
                "2. Any explicit data format constraints (e.g., required CSV columns).\n"
                "3. Any explicit I/O details (e.g., filenames used, successful data loading patterns).\n"
                "4. Specific error messages or tracebacks from failed attempts, as they are crucial context for avoiding repeated mistakes.\n"
                f"\n\n# OLDER HISTORY\n{older_history}"
            )
            summarized_older_history = await self.llm_service.call(summarize_prompt)
            
            # Combine summarized older history with verbatim recent history
            updated_log = f"--- SUMMARIZED HISTORY ---\n{summarized_older_history}\n\n--- RECENT HISTORY (VERBATIM) ---\n{recent_history}"

            logger.info("Running log has been updated with summarized history.")
            
        return updated_log
