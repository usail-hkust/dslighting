"""
DSLighting Common - Exceptions

重新导出 dsat.common.exceptions
"""
try:
    from dsat.common.exceptions import *
except ImportError:
    # 如果 DSAT 不可用，定义一些基本的异常
    class DSLightingError(Exception):
        """Base exception for DSLighting"""
        pass

    class DataLoadError(DSLightingError):
        """Exception raised when data loading fails"""
        pass

    class AgentExecutionError(DSLightingError):
        """Exception raised when agent execution fails"""
        pass

__all__ = [
    "DSLightingError",
    "DataLoadError",
    "AgentExecutionError",
]
