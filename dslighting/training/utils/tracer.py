"""
Trace 收集工具
"""
from typing import Any, Dict, List


class TraceCollector:
    """
    Trace 收集器
    """

    def __init__(self):
        self.traces: List[Dict[str, Any]] = []

    def add_trace(self, trace: Dict[str, Any]):
        """添加 trace"""
        self.traces.append(trace)

    def get_traces(self) -> List[Dict[str, Any]]:
        """获取所有 traces"""
        return self.traces

    def clear(self):
        """清空 traces"""
        self.traces.clear()


__all__ = ["TraceCollector"]
