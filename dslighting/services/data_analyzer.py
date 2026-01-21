"""
DSLighting Data Analyzer Service

重新导出 dsat.services.data_analyzer
"""
try:
    from dsat.services.data_analyzer import DataAnalyzer
except ImportError:
    DataAnalyzer = None

__all__ = ["DataAnalyzer"]
