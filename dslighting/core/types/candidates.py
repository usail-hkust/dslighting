"""
DSLighing Core Types - Workflow Candidates

重新导出 DSAT candidate models
"""
try:
    from dsat.models.candidates import WorkflowCandidate
except ImportError:
    WorkflowCandidate = None

__all__ = ["WorkflowCandidate"]
