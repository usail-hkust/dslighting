"""
DSLighting Tasks - 任务加载器

提供不同类型任务的加载器，统一任务配置和数据加载
"""

# DSAT Tasks (重新导出)
try:
    # 尝试导入 dsat.tasks 中的所有内容
    from dsat import tasks as _tasks

    # 重新导出所有公开内容
    _dsat_all = [
        name for name in dir(_tasks)
        if not name.startswith('_')
    ]

    # 将所有内容导入到当前命名空间
    for name in _dsat_all:
        globals()[name] = getattr(_tasks, name)

except ImportError:
    _dsat_all = []

# DSLighting Task Loaders
from .mle_task_loader import MLETaskLoader

__all__ = _dsat_all + ["MLETaskLoader"]
