"""
DSLighting Common - Type Definitions

重新导出 dsat.common.typing
"""
try:
    from dsat.common.typing import *
except ImportError:
    # 如果 DSAT 不可用，定义一些基本的类型
    from typing import Any, Dict, List, Optional, Union

    # 类型别名
    TaskID = str
    FilePath = str
    MetricValue = float

__all__ = [
    "TaskID",
    "FilePath",
    "MetricValue",
]
