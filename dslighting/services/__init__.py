"""
DSLighting 2.0 - Services Layer

This layer provides infrastructure services that support agents and operators.
All services are re-exported from DSAT.

Services:
- LLMService: LLM invocation service
- SandboxService: Sandboxed code execution service
- WorkspaceService: Workspace management service
- DataAnalyzer: Data analysis service
- VDBService: Vector database service for knowledge retrieval
"""

# Re-export DSAT services
from dsat.services.llm import LLMService
from dsat.services.sandbox import SandboxService
from dsat.services.workspace import WorkspaceService

# Try to import optional services
try:
    from dsat.services.analyzer import DataAnalyzer
except ImportError:
    DataAnalyzer = None

try:
    from dsat.services.vdb import VDBService
except ImportError:
    VDBService = None

__all__ = [
    "LLMService",
    "SandboxService",
    "WorkspaceService",
    "DataAnalyzer",
    "VDBService",
]
