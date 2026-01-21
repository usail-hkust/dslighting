"""
Custom Operators - 用户自定义 Operators

在这个目录下添加你自己的自定义 operators。

示例：
1. 创建文件 my_custom_operator.py
2. 定义你的 operator 类（继承自 Operator）
3. 在这个文件中导入
4. 在 dslighting/operators/__init__.py 中导出
"""

# ========== 内置示例 Operators ==========

# DataProfilerOperator - 数据特征分析 Operator（完整示例）
from .data_profiler import DataProfilerOperator

# TextAnalysisOperator - 文本分析 Operator（示例）
# from .example_operator import TextAnalysisOperator

# ========== 用户自定义 Operators ==========
# 在这里添加你自己的 operators
# from .my_custom_operator import MyCustomOperator
# from .my_llm_operator import MyLLMOperator
# from .my_data_operator import MyDataOperator

__all__ = [
    # 内置示例
    "DataProfilerOperator",
    # "TextAnalysisOperator",

    # 添加你的 operators 到这里
    # "MyCustomOperator",
    # "MyLLMOperator",
    # "MyDataOperator",
]
