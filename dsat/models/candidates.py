from pydantic import BaseModel, Field
from typing import Optional, List

class WorkflowCandidate(BaseModel):
    """
    Represents a proposed orchestration workflow being evaluated by a
    Paradigm 3 (AFlow-style) meta-optimization driver.
    """
    workflow_code: str = Field(description="The code for the proposed orchestration workflow.")
    fitness: Optional[float] = Field(default=None, description="The fitness score of this workflow.")
    lineage: List[str] = Field(default_factory=list, description="IDs of parent workflow candidates.")
    round_num: Optional[int] = Field(default=None, description="The optimization round this candidate was generated in.")

    class Config:
        """Pydantic configuration."""
        extra = 'forbid'