"""
DSLighting workflows namespace.

Keep this package import lightweight.

Historically this module eagerly imported every workflow factory, preset, and
utility. That pulled in the full workflow graph on first import of
``dslighting.workflows`` and caused circular imports in paths that only needed a
single nested module such as ``dslighting.workflows.search.react``.

To avoid that, exports are resolved lazily on first attribute access.
"""

from __future__ import annotations

from importlib import import_module
from typing import Dict, Tuple


_LAZY_EXPORTS: Dict[str, Tuple[str, str]] = {
    "BaseWorkflow": ("dslighting.workflows.base", "BaseWorkflow"),
    "BaseWorkflowFactory": ("dslighting.workflows.factory.base", "BaseWorkflowFactory"),
    "WorkflowRegistry": ("dslighting.workflows.factory", "WorkflowRegistry"),
    "default_workflow_registry": ("dslighting.workflows.factory", "default_workflow_registry"),
    "AIDEWorkflowFactory": ("dslighting.workflows.factory", "AIDEWorkflowFactory"),
    "AutoMindWorkflowFactory": ("dslighting.workflows.factory", "AutoMindWorkflowFactory"),
    "DSAgentWorkflowFactory": ("dslighting.workflows.factory", "DSAgentWorkflowFactory"),
    "DataInterpreterWorkflowFactory": ("dslighting.workflows.factory", "DataInterpreterWorkflowFactory"),
    "AutoKaggleWorkflowFactory": ("dslighting.workflows.factory", "AutoKaggleWorkflowFactory"),
    "DeepAnalyzeWorkflowFactory": ("dslighting.workflows.factory", "DeepAnalyzeWorkflowFactory"),
    "MyCustomAgentWorkflowFactory": ("dslighting.workflows.factory", "MyCustomAgentWorkflowFactory"),
    "AFlowWorkflowFactory": ("dslighting.workflows.factory", "AFlowWorkflowFactory"),
    "ReActWorkflowFactory": ("dslighting.workflows.factory", "ReActWorkflowFactory"),
    "DynamicWorkflowFactory": ("dslighting.workflows.factory", "DynamicWorkflowFactory"),
    "AIDE": ("dslighting.workflows.presets", "AIDE"),
    "AutoKaggle": ("dslighting.workflows.presets", "AutoKaggle"),
    "DataInterpreter": ("dslighting.workflows.presets", "DataInterpreter"),
    "DeepAnalyze": ("dslighting.workflows.presets", "DeepAnalyze"),
    "DSAgent": ("dslighting.workflows.presets", "DSAgent"),
    "AutoMind": ("dslighting.workflows.presets", "AutoMind"),
    "AFlow": ("dslighting.workflows.presets", "AFlow"),
    "ReAct": ("dslighting.workflows.presets", "ReAct"),
    "AIDEWorkflow": ("dslighting.workflows.presets", "AIDEWorkflow"),
    "AutoKaggleWorkflow": ("dslighting.workflows.presets", "AutoKaggleWorkflow"),
    "DataInterpreterWorkflow": ("dslighting.workflows.presets", "DataInterpreterWorkflow"),
    "DeepAnalyzeWorkflow": ("dslighting.workflows.presets", "DeepAnalyzeWorkflow"),
    "DSAgentWorkflow": ("dslighting.workflows.presets", "DSAgentWorkflow"),
    "AutoMindWorkflow": ("dslighting.workflows.presets", "AutoMindWorkflow"),
    "AFlowWorkflow": ("dslighting.workflows.presets", "AFlowWorkflow"),
    "ReActWorkflow": ("dslighting.workflows.presets", "ReActWorkflow"),
    "SearchStrategy": ("dslighting.workflows.strategies", "SearchStrategy"),
    "GreedyStrategy": ("dslighting.workflows.strategies", "GreedyStrategy"),
    "BeamSearchStrategy": ("dslighting.workflows.strategies", "BeamSearchStrategy"),
    "MCTSStrategy": ("dslighting.workflows.strategies", "MCTSStrategy"),
    "EvolutionaryStrategy": ("dslighting.workflows.strategies", "EvolutionaryStrategy"),
    "build_error_history": ("dslighting.workflows.utils", "build_error_history"),
    "capture_llm_history": ("dslighting.workflows.utils", "capture_llm_history"),
    "llm_history_length": ("dslighting.workflows.utils", "llm_history_length"),
    "collect_output_files": ("dslighting.workflows.utils", "collect_output_files"),
    "extract_output_filenames_from_description": (
        "dslighting.workflows.utils",
        "extract_output_filenames_from_description",
    ),
    "find_new_output_files": ("dslighting.workflows.utils", "find_new_output_files"),
    "get_initial_sandbox_files": ("dslighting.workflows.utils", "get_initial_sandbox_files"),
    "OUTPUT_EXTENSIONS": ("dslighting.workflows.utils", "OUTPUT_EXTENSIONS"),
    "IGNORE_FILES": ("dslighting.workflows.utils", "IGNORE_FILES"),
}


def __getattr__(name: str):
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module 'dslighting.workflows' has no attribute '{name}'")

    module_name, attr_name = _LAZY_EXPORTS[name]
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(list(globals().keys()) + list(_LAZY_EXPORTS.keys()))


__all__ = sorted(_LAZY_EXPORTS.keys())
