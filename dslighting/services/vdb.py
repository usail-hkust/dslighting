"""
DSLighting Vector Database Service

重新导出 dsat.services.vdb
"""
try:
    from dsat.services.vdb import VDBService
except ImportError:
    VDBService = None

__all__ = ["VDBService"]
