# web_ui/backend/app/agents/agent_orchestrator.py
"""
Agent Orchestrator - Coordinates agent execution flows.

This module handles the orchestration of different agent sequences
based on the mode and task requirements.
"""

import logging
from typing import Dict, List, Any, Optional
from ..prompts.agent_prompts import create_eda_summary_prompt

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates agent execution flows"""

    def __init__(self, llm, task_id: str):
        self.llm = llm
        self.task_id = task_id

    async def run_eda_summary_flow(
        self,
        user_question: str,
        execution_result: Dict[str, Any],
        base_context: str,
        chat_status_dict: Dict[str, str]
    ) -> str:
        """
        Run the EDA Summary Agent flow.

        This agent analyzes the execution results and provides a
        helpful response to the user's question.

        Args:
            user_question: The original user question
            execution_result: Dict with stdout, stderr, images
            base_context: Data schema and file system context
            chat_status_dict: For updating UI status

        Returns:
            String response from the summary agent
        """
        chat_status_dict[self.task_id] = "总结分析结果..."

        # Prepare image information for the prompt
        images_info = []
        if execution_result.get("images"):
            for img in execution_result["images"]:
                images_info.append({
                    "filename": img.get("url", "").split("/")[-1],
                    "description": img.get("description", "No description available")
                })

        # Build the prompt
        prompt = create_eda_summary_prompt(
            user_question=user_question,
            execution_output=execution_result.get("stdout", ""),
            images_info=images_info,
            base_context=base_context
        )

        try:
            # Call the LLM (no JSON schema, just natural language)
            logger.info("Calling EDA Summary Agent...")
            summary = await self.llm.call(
                prompt=prompt,
                system_message="You are a helpful data analysis assistant. Analyze the execution results and provide clear, insightful responses to the user's questions."
            )

            logger.info(f"EDA Summary generated: {len(summary)} chars")
            return summary

        except Exception as e:
            logger.error(f"EDA Summary Agent failed: {e}")
            # Fallback to simple summary
            return self._generate_fallback_summary(execution_result)

    def _generate_fallback_summary(self, execution_result: Dict[str, Any]) -> str:
        """Generate a simple fallback summary if the agent fails"""
        parts = []

        # Add output
        if execution_result.get("stdout"):
            parts.append(f"**执行输出:**\n{execution_result['stdout']}")

        # Add image info
        images = execution_result.get("images", [])
        if images:
            parts.append(f"\n**生成了 {len(images)} 个可视化图表:**")
            for i, img in enumerate(images):
                desc = img.get("description", "无描述")
                parts.append(f"- 图表 {i+1}: {desc}")

        return "\n".join(parts) if parts else "代码执行完成，但没有输出。"
