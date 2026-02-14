"""
DSLighting Workflows Module

This module provides base classes and utilities for implementing custom workflows.
It includes the BaseWorkflow class, workflow factories for creating workflow
instances, preset workflows for common use cases, and search strategies.

**Submodules:**
- base: Base workflow class
- factory: Workflow factory classes
- presets: Preset workflow configurations
- strategies: Search strategies
- utils: Workflow utilities
- state: Workflow-specific state containers (AutoKaggle, DSAgent)
- operators: Workflow-specific operators (AFlow, AutoMind, DSAgent, AutoKaggle)
"""

import logging
from typing import Set

logger = logging.getLogger(__name__)


def _import_with_error_logging(module_name: str, attrs: list[str]) -> tuple:
    """Import module with explicit error logging for better debugging."""
    try:
        module = __import__(f"dslighting.workflows.{module_name}", fromlist=[attrs])
        return tuple(getattr(module, attr) for attr in attrs)
    except ImportError as e:
        logger.error(f"Failed to import {module_name}: {e}")
        raise


try:
    from .base import BaseWorkflow

    # Import all factory classes
    from .factory.base import BaseWorkflowFactory
    from .factory import (
        WorkflowFactory,
        AIDEWorkflowFactory,
        AutoMindWorkflowFactory,
        DSAgentWorkflowFactory,
        DataInterpreterWorkflowFactory,
        AutoKaggleWorkflowFactory,
        DeepAnalyzeWorkflowFactory,
        MyCustomAgentWorkflowFactory,
        AFlowWorkflowFactory,
        DynamicWorkflowFactory,
    )

    # Import all preset workflows
    from .presets import (
        AIDE,
        AutoKaggle,
        DataInterpreter,
        DeepAnalyze,
        DSAgent,
        AutoMind,
        AFlow,
        AIDEWorkflow,
        AutoKaggleWorkflow,
        DataInterpreterWorkflow,
        DeepAnalyzeWorkflow,
        DSAgentWorkflow,
        AutoMindWorkflow,
        AFlowWorkflow,
    )

    # Import all search strategies
    from .strategies import (
        SearchStrategy,
        GreedyStrategy,
        BeamSearchStrategy,
        MCTSStrategy,
        EvolutionaryStrategy,
    )

    # Import utilities
    from .utils import (
        build_error_history,
        capture_llm_history,
        llm_history_length,
        collect_output_files,
        extract_output_filenames_from_description,
        find_new_output_files,
        get_initial_sandbox_files,
        OUTPUT_EXTENSIONS,
        IGNORE_FILES,
    )

except ImportError as e:
    logger.error(f"Failed to import workflows module: {e}")
    logger.error("Please ensure all dependencies are installed.")
    # Set all imports to None for graceful degradation
    BaseWorkflow = None  # type: ignore
    BaseWorkflowFactory = None  # type: ignore
    WorkflowFactory = None  # type: ignore
    AIDEWorkflowFactory = None  # type: ignore
    AutoMindWorkflowFactory = None  # type: ignore
    DSAgentWorkflowFactory = None  # type: ignore
    DataInterpreterWorkflowFactory = None  # type: ignore
    AutoKaggleWorkflowFactory = None  # type: ignore
    DeepAnalyzeWorkflowFactory = None  # type: ignore
    MyCustomAgentWorkflowFactory = None  # type: ignore
    AFlowWorkflowFactory = None  # type: ignore
    DynamicWorkflowFactory = None  # type: ignore
    AIDE = None  # type: ignore
    AutoKaggle = None  # type: ignore
    DataInterpreter = None  # type: ignore
    DeepAnalyze = None  # type: ignore
    DSAgent = None  # type: ignore
    AutoMind = None  # type: ignore
    AFlow = None  # type: ignore
    AIDEWorkflow = None  # type: ignore
    AutoKaggleWorkflow = None  # type: ignore
    DataInterpreterWorkflow = None  # type: ignore
    DeepAnalyzeWorkflow = None  # type: ignore
    DSAgentWorkflow = None  # type: ignore
    AutoMindWorkflow = None  # type: ignore
    AFlowWorkflow = None  # type: ignore
    SearchStrategy = None  # type: ignore
    GreedyStrategy = None  # type: ignore
    BeamSearchStrategy = None  # type: ignore
    MCTSStrategy = None  # type: ignore
    EvolutionaryStrategy = None  # type: ignore
    build_error_history = None  # type: ignore
    capture_llm_history = None  # type: ignore
    llm_history_length = None  # type: ignore
    collect_output_files = None  # type: ignore
    extract_output_filenames_from_description = None  # type: ignore
    find_new_output_files = None  # type: ignore
    get_initial_sandbox_files = None  # type: ignore
    OUTPUT_EXTENSIONS: Set[str] = set()  # type: ignore
    IGNORE_FILES: Set[str] = set()  # type: ignore

    # Re-raise the original error to alert developers
    raise


__all__ = [
    "BaseWorkflow",
    "BaseWorkflowFactory",
    "WorkflowFactory",
    "AIDEWorkflowFactory",
    "AutoMindWorkflowFactory",
    "DSAgentWorkflowFactory",
    "DataInterpreterWorkflowFactory",
    "AutoKaggleWorkflowFactory",
    "DeepAnalyzeWorkflowFactory",
    "MyCustomAgentWorkflowFactory",
    "AFlowWorkflowFactory",
    "DynamicWorkflowFactory",
    # presets
    "AIDE",
    "AutoKaggle",
    "DataInterpreter",
    "DeepAnalyze",
    "DSAgent",
    "AutoMind",
    "AFlow",
    "AIDEWorkflow",
    "AutoKaggleWorkflow",
    "DataInterpreterWorkflow",
    "DeepAnalyzeWorkflow",
    "DSAgentWorkflow",
    "AutoMindWorkflow",
    "AFlowWorkflow",
    # strategies
    "SearchStrategy",
    "GreedyStrategy",
    "BeamSearchStrategy",
    "MCTSStrategy",
    "EvolutionaryStrategy",
    # utilities
    "build_error_history",
    "capture_llm_history",
    "llm_history_length",
    "collect_output_files",
    "extract_output_filenames_from_description",
    "find_new_output_files",
    "get_initial_sandbox_files",
    "OUTPUT_EXTENSIONS",
    "IGNORE_FILES",
]
