"""
Implements DSAgentState, which manages the running log for the DS-Agent workflow.
"""
from pydantic import BaseModel
from dsat.services.states.base import State

class DSAgentState(State, BaseModel):
    """
    Holds the state for a DS-Agent workflow execution, primarily the running log
    which accumulates summaries of each experimental step.
    """
    running_log: str = ""
    final_code: str = ""
