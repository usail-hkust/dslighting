"""
Custom Operators - User-Defined Operators

Add your custom operators in this directory.

Example:
1. Create a file my_custom_operator.py
2. Define your operator class (inheriting from Operator)
3. Import it in this file
4. Export it in dslighting/operators/__init__.py
"""

# ========== Built-in Example Operators ==========

# DataProfilerOperator - Data profiling operator (complete example)
from .data_profiler import DataProfilerOperator

# TextAnalysisOperator - Text analysis operator (example)
# from .example_operator import TextAnalysisOperator

# ========== User-Defined Operators ==========
# Add your custom operators here
# from .my_custom_operator import MyCustomOperator
# from .my_llm_operator import MyLLMOperator
# from .my_data_operator import MyDataOperator

__all__ = [
    # Built-in examples
    "DataProfilerOperator",
    # "TextAnalysisOperator",

    # Add your operators here
    # "MyCustomOperator",
    # "MyLLMOperator",
    # "MyDataOperator",
]
