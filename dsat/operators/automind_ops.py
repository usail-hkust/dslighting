import logging
from typing import Dict

from dsat.models.formats import ComplexityScore, DecomposedPlan
from dsat.operators.base import Operator
from dsat.services.llm import LLMService

logger = logging.getLogger(__name__)

class ComplexityScorerOperator(Operator):
    """Scores the complexity of a natural language plan."""
    async def __call__(self, plan: str, task_goal: str) -> ComplexityScore:
        logger.info("Scoring plan complexity...")
        prompt = (
            "You are an expert project manager. On a scale of 1 to 5, where 1 is trivial "
            "(e.g., load a file and report basic properties) and 5 is highly complex (e.g., multi-stage pipeline involving custom algorithms, extensive preprocessing, or complex simulations), how complex is the following plan?\n\n"
            f"## Task Goal:\n{task_goal}\n\n"
            f"## Proposed Plan:\n{plan}\n\n"
            "Respond with a JSON object containing your score and a brief justification."
        )
        score = await self.llm_service.call_with_json(prompt, output_model=ComplexityScore)
        logger.info(f"Plan complexity scored at {score.complexity}/5.")
        return score

class PlanDecomposerOperator(Operator):
    """Decomposes a complex plan into a structured list of sequential steps."""
    async def __call__(self, plan: str, task_goal: str) -> DecomposedPlan:
        logger.info("Decomposing complex plan into steps...")
        prompt = (
            "You are an expert data scientist. Decompose the following high-level plan into a sequence of "
            "small, logical, and executable steps. Each step should represent a single cell in a data science notebook.\n\n"
            f"## Task Goal:\n{task_goal}\n\n"
            f"## High-Level Plan:\n{plan}\n\n"
            "Respond with a JSON object containing a list of tasks. Each task must have a unique `task_id` and an `instruction`."
        )
        decomposed_plan = await self.llm_service.call_with_json(prompt, output_model=DecomposedPlan)
        logger.info(f"Plan decomposed into {len(decomposed_plan.tasks)} steps.")
        return decomposed_plan
