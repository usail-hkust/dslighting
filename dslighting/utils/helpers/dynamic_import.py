"""
DSLighting Utils - Dynamic Import

重新导出 dsat.utils.dynamic_import
"""
try:
    from dsat.utils.dynamic_import import import_workflow_from_string
except ImportError:
    import_workflow_from_string = None

__all__ = ["import_workflow_from_string"]
