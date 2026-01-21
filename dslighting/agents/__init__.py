"""
DSLighting 2.0 - Agents Layer

重新导出 DSAT Workflows

BaseAgent 实际上就是 DSATWorkflow
"""
try:
    from dsat.workflows.base import DSATWorkflow
    BaseAgent = DSATWorkflow
except ImportError:
    BaseAgent = None

__all__ = ["BaseAgent"]
