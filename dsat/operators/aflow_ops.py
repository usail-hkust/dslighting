from typing import List, Dict, Any
from pydantic import BaseModel, Field

from dsat.operators.base import Operator
from dsat.services.llm import LLMService

# --- Pydantic Models for Structured I/O ---

class ScEnsembleResponse(BaseModel):
    """Structured response for the Self-Consistency Ensemble operator."""
    thought: str = Field(description="The step-by-step thinking process to determine the most consistent solution.")
    solution_letter: str = Field(description="The single letter (A, B, C, etc.) of the most consistent solution.")

class ReviewResponse(BaseModel):
    """Structured response for the Review operator."""
    is_correct: bool = Field(description="True if the solution is very likely correct, False otherwise.")
    feedback: str = Field(description="If incorrect, detailed feedback for revision. If correct, a brief justification.")

class ReviseResponse(BaseModel):
    """Structured response for the Revise operator."""
    solution: str = Field(description="The complete, revised solution based on the provided feedback.")


# --- Operator Implementations ---

class ScEnsembleOperator(Operator):
    """
    Performs a self-consistency check by asking the LLM to vote on the most
    frequent or logical answer from a list of candidate solutions.
    """
    async def __call__(self, solutions: List[str], problem: str) -> str:
        if not self.llm_service:
            raise ValueError("LLMService is required for this operator.")
        
        solution_text = ""
        solution_map = {}
        for i, solution in enumerate(solutions):
            letter = chr(65 + i)
            solution_map[letter] = solution
            solution_text += f"{letter}: \n{solution}\n\n"

        prompt = (
            f"Given the problem: '{problem}'\n\n"
            f"Several solutions have been generated:\n{solution_text}\n"
            "Carefully evaluate these solutions and identify the answer that appears most frequently or is most logical. "
            "Respond with a JSON object containing your thought process and the letter of the most consistent solution."
        )
        
        response_model = await self.llm_service.call_with_json(prompt, output_model=ScEnsembleResponse)
        
        chosen_letter = response_model.solution_letter.strip().upper()
        return solution_map.get(chosen_letter, solutions[0]) # Default to first solution on failure

class ReviewOperator(Operator):
    """
    Critically reviews a solution for correctness and provides structured feedback.
    """
    async def __call__(self, problem: str, solution: str) -> ReviewResponse:
        if not self.llm_service:
            raise ValueError("LLMService is required for this operator.")

        prompt = (
            "You are a meticulous reviewer. Given a problem and a solution, your task is to critically evaluate the solution's correctness. "
            "If you are more than 95% confident the solution is incorrect, provide feedback for fixing it. Otherwise, confirm its correctness.\n\n"
            f"# PROBLEM\n{problem}\n\n"
            f"# SOLUTION\n{solution}\n\n"
            "Respond with a JSON object containing your evaluation."
        )
        
        return await self.llm_service.call_with_json(prompt, output_model=ReviewResponse)

class ReviseOperator(Operator):
    """
    Revises a solution based on feedback from the Review operator.
    """
    async def __call__(self, problem: str, solution: str, feedback: str) -> str:
        if not self.llm_service:
            raise ValueError("LLMService is required for this operator.")

        prompt = (
            "You are an expert programmer. A previous solution was found to be incorrect. "
            "Your task is to revise the solution based on the provided feedback.\n\n"
            f"# PROBLEM\n{problem}\n\n"
            f"# INCORRECT SOLUTION\n{solution}\n\n"
            f"# FEEDBACK\n{feedback}\n\n"
            "Provide a JSON object containing the complete, revised solution."
        )
        
        response_model = await self.llm_service.call_with_json(prompt, output_model=ReviseResponse)
        return response_model.solution
