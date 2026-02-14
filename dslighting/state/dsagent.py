"""
Implements DSAgentState, which manages the running log for the DS-Agent workflow.
"""
from pydantic import BaseModel
from dslighting.state.base import State

class DSAgentState(BaseModel, State):
    """
    Holds the state for a DS-Agent workflow execution, primarily the running log
    which accumulates summaries of each experimental step.
    """
    running_log: str = ""
    final_code: str = ""
    last_plan: str = ""  # 保存最新的 plan，用于后续节点访问
