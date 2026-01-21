# dsat/workflows/manual/dsagent_workflow.py

import logging
import difflib
from pathlib import Path
from typing import Dict, Any

from dsat.workflows.base import DSATWorkflow
from dsat.services.states.dsa_log import DSAgentState

from dsat.services.sandbox import SandboxService
from dsat.operators.base import Operator


logger = logging.getLogger(__name__)


class DSAgentWorkflow(DSATWorkflow):
    """
    Implements the core algorithmic loop of DS-Agent: Plan -> Execute -> Log.
    This workflow now conforms to the DSATWorkflow interface.
    """
    def __init__(self, operators: Dict[str, Operator], services: Dict[str, Any], agent_config: Dict[str, Any]):
        super().__init__(operators, services, agent_config)
        self.state: DSAgentState = services["state"]
        self.sandbox_service: SandboxService = services["sandbox"]
        self.planner_op = self.operators["planner"]
        self.executor_op = self.operators["executor"]
        self.logger_op = self.operators["logger"]

    async def solve(self, description: str, io_instructions: str, data_dir: Path, output_path: Path) -> None:
        """
        Use DS-Agent's Plan-Execute-Log loop...
        """
        logger.info(f"DSAgentWorkflow starting to solve task. Target output: {output_path}")

        self.state.running_log = "[Initial State] Starting analysis."
        self.state.final_code = "# Basic Initialization. Analyze the data report and I/O requirements."
        
        task_goal = description
        current_io_instructions = io_instructions

        max_iterations = self.agent_config.get("max_iterations", 2)

        for step in range(max_iterations):
            logger.info(f"--- Starting DS-Agent Solve Step {step + 1}/{max_iterations} ---")

            # 1. Plan
            plan = await self.planner_op(research_problem=task_goal, io_instructions=current_io_instructions, running_log=self.state.running_log)
            
            # 2. Execute (refine the code)
            initial_code = self.state.final_code
            exec_result, refined_code = await self.executor_op(
                initial_code=initial_code, plan=plan, 
                research_problem=task_goal, io_instructions=current_io_instructions, running_log=self.state.running_log
            )

            diff = "".join(difflib.unified_diff(
                initial_code.splitlines(keepends=True),
                refined_code.splitlines(keepends=True),
            ))
            
            # 3. Log
            new_log_entry = await self.logger_op(running_log=self.state.running_log, plan=plan, exec_result=exec_result, diff=diff)
            
            self.state.running_log = new_log_entry
            
            self.state.final_code = refined_code
            logger.info(f"Step {step + 1} complete. Code has been refined.")

        logger.info("Max iterations reached. Executing the final refined code to produce the output file...")
        final_exec_result = await self.sandbox_service.run_script(self.state.final_code)
        
        if not final_exec_result.success:
            logger.error(f"Final code execution failed!\\n{final_exec_result.stderr}")

