"""dslighting.tools.dsflow.core.models

Internal models used by DSFlow optimization.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field


class PlanScreeningResponse(BaseModel):
    thought: str = Field(description="Critical analysis focusing on weaknesses and risks.")
    score: float = Field(description="Feasibility score from 0 to 10 (strict).")


class ProposedOperator(BaseModel):
    name: str = Field(description="Operator name (Python identifier, unique).")
    description: str = Field(description="What the operator does and when to use it.")
    inputs: str = Field(
        default="",
        description="Explicit input contract for the operator (args/kwargs names, types, and meaning).",
    )
    outputs: str = Field(
        default="",
        description="Explicit output contract for the operator (return type/fields and meaning).",
    )
    triggers: str = Field(
        default="",
        description="Trigger condition / when to apply (short, task-agnostic).",
    )
    task_types: list[str] = Field(
        default_factory=list,
        description="Applicable task types, e.g. ['tabular'], ['nlp'], ['vision'], ['general'].",
    )
    code: str = Field(
        description=(
            "Python source code defining `class <name>(Operator)` with `async def __call__(...)`."
        )
    )


class DSFlowOptimizeResponse(BaseModel):
    thought: str = Field(
        description=(
            "Self-reflection and reasoning before making changes. "
            "Analyze: (1) What worked/failed in parent workflow? "
            "(2) How to generalize to different tasks/datasets? "
            "(3) What robustness improvements are needed? "
            "(4) Summary of key insights and patterns."
        )
    )
    modification: str = Field(description="One-sentence summary of the change.")
    graph: str = Field(description="Complete Python code defining class `Workflow(BaseWorkflow)`.")
    operators: list[ProposedOperator] = Field(
        default_factory=list, description="Optional new operators to register."
    )


@dataclass
class EvalCandidate:
    code: str
    modification: str
    round_num: int
    thought: str = ""  # Self-reflection and reasoning from meta-optimizer
    coarse_score: float = 0.0
    fitness: float = 0.0
    fine_evaluated: bool = False


@dataclass(frozen=True)
class TaskContext:
    competition_id: str
    raw_description: str
    data_dir: Path
    base_report: str
