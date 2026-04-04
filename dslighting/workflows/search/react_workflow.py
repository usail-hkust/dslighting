"""ReAct workflow implementation."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from dslighting.ops.code.execute import ExecuteAndTestOperator
from dslighting.ops.presets.react import ReActOperator
from dslighting.prompts.workflows.react import create_react_prompt
from dslighting.react_protocol import normalize_react_reply
from dslighting.runtime.dag.actor import SolveWorkflowActor
from dslighting.workflows.base import BaseWorkflow
from dslighting.workflows.search.react_context_manager import (
    ReActContextConfig,
    ReActContextManager,
    build_react_context_config,
)

logger = logging.getLogger(__name__)


class ReActWorkflow(BaseWorkflow):
    """Thin workflow wrapper around the strict ReAct operator."""

    def __init__(
        self,
        operators: Dict[str, Any],
        services: Dict[str, Any],
        agent_config: Dict[str, Any],
        benchmark: Optional[Any] = None,
    ) -> None:
        super().__init__(operators, services, agent_config)
        self.llm_service = services["llm"]
        self.sandbox_service = services["sandbox"]
        self.workspace_service = services.get("workspace")
        self.benchmark = benchmark
        self.react_op: ReActOperator = operators["react"]
        self.execute_op: ExecuteAndTestOperator = operators["execute"]
        self.max_steps = max(1, int(getattr(self.react_op, "max_steps", 10) or 10))
        self.context_config: ReActContextConfig = build_react_context_config(
            services.get("react_context_config")
        )

    def build_actor(
        self,
        *,
        task_id: str,
        description: str,
        io_instructions: str,
        data_dir: Path,
        output_path: Path,
        dag_options: Optional[Any] = None,
    ) -> SolveWorkflowActor:
        _ = dag_options
        return SolveWorkflowActor(
            task_id=task_id,
            workflow=self,
            description=description,
            io_instructions=io_instructions,
            data_dir=data_dir,
            output_path=output_path,
        )

    async def solve(
        self,
        description: str,
        io_instructions: str,
        data_dir: Path,
        output_path: Path,
    ) -> None:
        """Solve the task using the ReAct loop."""
        if self.workspace_service and data_dir and data_dir.exists():
            self.workspace_service.link_data_to_workspace(data_dir)

        task_context = self._build_task_context(
            description=description,
            io_instructions=io_instructions,
        )
        question = self._render_task_message(task_context)
        system_prompt = create_react_prompt(task_context)

        answer, messages = await self._run_react_loop(
            question=question,
            system_prompt=system_prompt,
        )
        logger.info(
            "[ReActWorkflow] loop finished. answer preview: %r",
            (answer or "")[:200],
        )

        self._save_messages(messages)

    async def _run_react_loop(
        self,
        *,
        question: str,
        system_prompt: str,
    ) -> tuple[str | None, list[dict]]:
        context_manager = ReActContextManager(
            system_prompt=system_prompt,
            task_message=question,
            config=self.context_config,
        )
        final_answer: str | None = None

        for step in range(self.max_steps):
            logger.info("[ReActWorkflow] step %d/%d", step + 1, self.max_steps)
            response = await self.llm_service.call_messages(
                context_manager.build_messages(),
                max_retries=self.llm_service.config.max_retries,
            )
            content = response.choices[0].message.content or ""
            normalized_reply = normalize_react_reply(content)
            if normalized_reply.repaired:
                logger.info(
                    "[ReActWorkflow] repaired assistant reply at step %d: %s",
                    step + 1,
                    normalized_reply.repair_reason,
                )
            context_manager.add_assistant_reply(normalized_reply.normalized_content)

            turn_result = await self.react_op(normalized_reply.normalized_content)
            if turn_result.final_answer is not None:
                final_answer = turn_result.final_answer
                logger.info("[ReActWorkflow] final answer reached at step %d.", step + 1)
                break

            if turn_result.action_code is not None:
                exec_result = await self.execute_op(code=turn_result.action_code, mode="script")
                context_manager.add_runtime_reply(
                    self.react_op.build_execution_message(exec_result)
                )
                continue

            if turn_result.next_user_message is not None:
                context_manager.add_runtime_reply(turn_result.next_user_message)
                if (
                    context_manager.consecutive_feedback_turns()
                    > self.context_config.max_feedback_retries
                ):
                    logger.warning(
                        "[ReActWorkflow] stopping after %d consecutive protocol feedback turns.",
                        context_manager.consecutive_feedback_turns(),
                    )
                    break
        else:
            logger.warning(
                "[ReActWorkflow] reached max_steps=%d without a final answer.",
                self.max_steps,
            )

        return final_answer, context_manager.export_full_history()

    @staticmethod
    def _render_task_message(task_context: Dict[str, str]) -> str:
        return (
            "Task Description:\n"
            f"{task_context['goal_and_data']}\n\n"
            "I/O Requirements:\n"
            f"{task_context['io_instructions']}"
        )

    @staticmethod
    def _build_task_context(*, description: str, io_instructions: str) -> Dict[str, str]:
        return {
            "goal_and_data": description,
            "io_instructions": io_instructions,
        }

    def _save_messages(self, messages: list[dict]) -> None:
        if not self.workspace_service:
            return
        artifacts_dir = self.workspace_service.get_path("artifacts")
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        messages_path = artifacts_dir / "messages.json"
        messages_path.write_text(
            json.dumps(messages, indent=4, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("[ReActWorkflow] messages saved to %s", messages_path)
