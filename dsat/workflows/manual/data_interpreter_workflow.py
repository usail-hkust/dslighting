# dsat/workflows/manual/data_interpreter_workflow.py

import logging
from pathlib import Path
from typing import Dict, Any

from dsat.workflows.base import DSATWorkflow
from dsat.models.formats import Plan

from dsat.services.sandbox import SandboxService
from dsat.operators.base import Operator

from dsat.prompts.data_interpreter_prompt import (
    PLAN_PROMPT, GENERATE_CODE_PROMPT, REFLECT_AND_DEBUG_PROMPT, FINALIZE_OUTPUT_PROMPT
)

from dsat.utils.context import ContextManager, MAX_OUTPUT_CHARS, truncate_output

logger = logging.getLogger(__name__)


class DataInterpreterWorkflow(DSATWorkflow):
    """
    Implements the DataInterpreter workflow, now conforming to the DSATWorkflow interface.

    It uses a plan -> (write -> execute -> reflect) loop to solve problems,
    and then executes a final step to generate the required output file.
    It also saves a detailed interaction report as a separate log file.
    """
    def __init__(self, operators: Dict[str, Operator], services: Dict[str, Any], agent_config: Dict[str, Any]):
        super().__init__(operators, services, agent_config)
        self.sandbox_service: SandboxService = services["sandbox"]
        self.planner_op = self.operators["planner"]
        self.generator_op = self.operators["generator"]
        self.debugger_op = self.operators["debugger"]
        self.executor_op = self.operators["executor"]
        self.max_retries = self.agent_config.get("max_retries", 3)
        self.context_manager = ContextManager()
    
    async def solve(self, description: str, io_instructions: str, data_dir: Path, output_path: Path) -> None:
        """
        Use Data Interpreter's plan-and-execute loop...
        """
        logger.info(f"DataInterpreterWorkflow starting to solve task. Target output: {output_path}")

        # The planner needs the full context to make the plan.
        full_context_for_planner = f"{description}\n\n{io_instructions}"

        # 1. Create a plan
        logger.info("Step 1: Planning...")
        plan: Plan = await self.planner_op(user_request=full_context_for_planner)
        logger.info(f"Plan generated with {len(plan.tasks)} tasks.")
        
        report_lines = [f"# Data Interpretation Report for: {description}\n"]
        report_lines.append("## Execution Plan")
        for task in plan.tasks:
            report_lines.append(f"- **Task {task.task_id}**: {task.instruction}")
        report_lines.append("\n---\n")

        # 2. Execute tasks in Notebook context
        logger.info("Step 2: Executing tasks...")
        history_steps = []
        async with self.sandbox_service.notebook_executor() as notebook:
            for task in plan.tasks:
                logger.info(f"Executing Task {task.task_id}: {task.instruction}")
                report_lines.append(f"## Task {task.task_id}: {task.instruction}")
                
                current_code = ""
                exec_result = None
                
                for attempt in range(self.max_retries):
                    logger.info(f"Attempt {attempt + 1}/{self.max_retries} for task {task.task_id}")

                    # Build history context before every attempt (needed by both generate and debug)
                    history_context = self.context_manager.build_history_context(
                        history_steps, 
                        key_order=["task_id", "status", "code", "output"]
                    )

                    if attempt == 0:
                        prompt = GENERATE_CODE_PROMPT.format(
                            user_requirement=description,
                            io_instructions=io_instructions, # Pass separately
                            plan_status=plan.model_dump_json(),
                            current_task=task.instruction, history=history_context
                        )
                        _, current_code = await self.generator_op(system_prompt=prompt)
                    else:
                        safe_error_output = truncate_output(exec_result.stderr, MAX_OUTPUT_CHARS)
                        prompt = REFLECT_AND_DEBUG_PROMPT.format(
                            user_requirement=description,
                            io_instructions=io_instructions, # Pass separately
                            current_task=task.instruction,
                            failed_code=current_code, error_output=safe_error_output,
                            history=history_context
                        )
                        _, current_code = await self.debugger_op(system_prompt=prompt)
                    
                    report_lines.append(f"\n**Attempt {attempt + 1} Code:**\n```python\n{current_code}\n```")
                    exec_result = await self.executor_op(code=current_code, mode="notebook", executor_context=notebook)

                    if exec_result.success:
                        logger.info(f"Task {task.task_id} succeeded.")
                        report_lines.append(f"**Result:** Success\n**Output:**\n```\n{exec_result.stdout}\n```")
                        history_steps.append({
                            "task_id": task.task_id,
                            "status": "Success",
                            "code": truncate_output(current_code, MAX_OUTPUT_CHARS),
                            "output": truncate_output(exec_result.stdout, MAX_OUTPUT_CHARS),
                        })
                        break
                    else:
                        logger.warning(f"Task {task.task_id} failed on attempt {attempt + 1}.")
                        report_lines.append(f"**Result:** Failure\n**Error:**\n```\n{exec_result.stderr}\n```")
                        history_steps.append({
                            "task_id": task.task_id,
                            "status": "Failure",
                            "code": truncate_output(current_code, MAX_OUTPUT_CHARS),
                            "output": truncate_output(exec_result.stderr, MAX_OUTPUT_CHARS),
                        })
                
                report_lines.append("\n---\n")

            logger.info("Step 3: Generating final output file...")
            report_lines.append("## Final Output Generation")

            final_history_context = self.context_manager.build_history_context(
                history_steps, 
                key_order=["task_id", "status", "code", "output"]
            )
            
            finalize_prompt = FINALIZE_OUTPUT_PROMPT.format(
                user_requirement=description,
                io_instructions=io_instructions, # Pass separately
                history=final_history_context,
                output_filename=output_path.name
            )
            _, final_code = await self.generator_op(system_prompt=finalize_prompt)
            report_lines.append(f"**Finalization Code:**\n```python\n{final_code}\n```")
            
            final_exec_result = await self.executor_op(code=final_code, mode="notebook", executor_context=notebook)

            if final_exec_result.success:
                logger.info("Finalization code executed successfully.")
                report_lines.append("**Result:** Success")
            else:
                logger.error(f"Finalization code failed to execute!\n{final_exec_result.stderr}")
                report_lines.append(f"**Result:** Failure\n**Error:**\n```\n{final_exec_result.stderr}\n```")

        # 4. Save the execution report as a separate log file
        report_path = output_path.parent / "execution_report.md"
        report_path.write_text("\n".join(report_lines), encoding='utf-8')
        logger.info(f"Execution report saved to {report_path}")
