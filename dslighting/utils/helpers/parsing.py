"""
DSLighting Utils - Parsing

重新导出 dsat.utils.parsing
"""
try:
    from dsat.utils.parsing import parse_plan_and_code
except ImportError:
    parse_plan_and_code = None

__all__ = ["parse_plan_and_code"]
