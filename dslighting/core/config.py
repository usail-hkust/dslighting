"""
DSLighing Core Config - 配置类定义

重新导出 dsat.config。
"""
try:
    from dsat.config import (
        LLMConfig,           # LLM 配置
        SandboxConfig,       # 沙箱配置
        TaskConfig,          # 任务配置
        RunConfig,           # 运行配置
        AgentSearchConfig,   # 搜索配置
    )
except ImportError:
    LLMConfig = None
    SandboxConfig = None
    TaskConfig = None
    RunConfig = None
    AgentSearchConfig = None

__all__ = [
    "LLMConfig",
    "SandboxConfig",
    "TaskConfig",
    "RunConfig",
    "AgentSearchConfig",
]
