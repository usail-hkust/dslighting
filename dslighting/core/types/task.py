"""
DSLighing Core Types - Task Definitions

重新导出 DSAT task models
"""
try:
    from dsat.models.task import (
        TaskDefinition,
        TaskType,
        TaskMode,
    )
except ImportError:
    TaskDefinition = None
    TaskType = None
    TaskMode = None

__all__ = [
    "TaskDefinition",
    "TaskType",
    "TaskMode",
]
