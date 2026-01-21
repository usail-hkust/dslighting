"""
DSLighing Core Types - 重新导出 DSAT Models

数据类型定义 - 重新导出 DSAT models 和 config。

包括:
- 任务类型 (TaskDefinition, TaskType, TaskMode)
- 优化候选者 (WorkflowCandidate)
- 数据格式 (Plan, ReviewResult, Task, etc.)
- 配置类型 (LLMConfig, TaskConfig, etc.)
"""

try:
    # ========== 任务类型 ==========
    from dsat.models import (
        TaskDefinition,
        TaskType,
        TaskMode,
    )

    # ========== 优化候选者 ==========
    from dsat.models import WorkflowCandidate

    # ========== 数据格式 ==========
    from dsat.models import (
        ReviewResult,
        Plan,
        Task,
        TaskContract,
        StepPlan,
        FileArtifact,
        ComplexityScore,
        DecomposedPlan,
    )

    # ========== 配置类型（从 dsat.config）==========
    from dsat.config import (
        LLMConfig,
        SandboxConfig,
        TaskConfig,
        RunConfig,
        AgentSearchConfig,
    )

except ImportError:
    # 如果 DSAT 不可用
    TaskDefinition = None
    TaskType = None
    TaskMode = None
    WorkflowCandidate = None
    ReviewResult = None
    Plan = None
    Task = None
    TaskContract = None
    StepPlan = None
    FileArtifact = None
    ComplexityScore = None
    DecomposedPlan = None
    LLMConfig = None
    SandboxConfig = None
    TaskConfig = None
    RunConfig = None
    AgentSearchConfig = None

__all__ = [
    # 任务类型
    "TaskDefinition",
    "TaskType",
    "TaskMode",
    # 优化候选者
    "WorkflowCandidate",
    # 数据格式
    "ReviewResult",
    "Plan",
    "Task",
    "TaskContract",
    "StepPlan",
    "FileArtifact",
    "ComplexityScore",
    "DecomposedPlan",
    # 配置类型
    "LLMConfig",
    "SandboxConfig",
    "TaskConfig",
    "RunConfig",
    "AgentSearchConfig",
]
