"""
DSLighting Common - Constants

重新导出 dsat.common.constants
"""
try:
    from dsat.common.constants import *
except ImportError:
    # 如果 DSAT 不可用，定义一些基本的常量
    DEFAULT_MAX_STEPS = 100
    DEFAULT_TIMEOUT = 300

__all__ = ["DEFAULT_MAX_STEPS", "DEFAULT_TIMEOUT"]
