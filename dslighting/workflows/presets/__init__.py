"""Preset workflow exports resolved lazily."""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "AIDE",
    "AutoKaggle",
    "DataInterpreter",
    "DeepAnalyze",
    "DSAgent",
    "AutoMind",
    "AFlow",
    "ReAct",
    "AIDEWorkflow",
    "AutoKaggleWorkflow",
    "DataInterpreterWorkflow",
    "DeepAnalyzeWorkflow",
    "DSAgentWorkflow",
    "AutoMindWorkflow",
    "AFlowWorkflow",
    "ReActWorkflow",
]

_EXPORT_MAP = {
    "AIDEWorkflow": ("dslighting.workflows.search.aide_workflow", "AIDEWorkflow"),
    "AutoKaggleWorkflow": (
        "dslighting.workflows.manual.autokaggle_workflow",
        "AutoKaggleWorkflow",
    ),
    "DataInterpreterWorkflow": (
        "dslighting.workflows.manual.data_interpreter_workflow",
        "DataInterpreterWorkflow",
    ),
    "DeepAnalyzeWorkflow": (
        "dslighting.workflows.manual.deepanalyze_workflow",
        "DeepAnalyzeWorkflow",
    ),
    "DSAgentWorkflow": ("dslighting.workflows.manual.dsagent_workflow", "DSAgentWorkflow"),
    "AutoMindWorkflow": ("dslighting.workflows.search.automind_workflow", "AutoMindWorkflow"),
    "AFlowWorkflow": ("dslighting.workflows.search.aflow_workflow", "AFlowWorkflow"),
    "ReActWorkflow": ("dslighting.workflows.search.react.workflow", "ReActWorkflow"),
    "AIDE": ("dslighting.workflows.search.aide_workflow", "AIDEWorkflow"),
    "AutoKaggle": ("dslighting.workflows.manual.autokaggle_workflow", "AutoKaggleWorkflow"),
    "DataInterpreter": (
        "dslighting.workflows.manual.data_interpreter_workflow",
        "DataInterpreterWorkflow",
    ),
    "DeepAnalyze": ("dslighting.workflows.manual.deepanalyze_workflow", "DeepAnalyzeWorkflow"),
    "DSAgent": ("dslighting.workflows.manual.dsagent_workflow", "DSAgentWorkflow"),
    "AutoMind": ("dslighting.workflows.search.automind_workflow", "AutoMindWorkflow"),
    "AFlow": ("dslighting.workflows.search.aflow_workflow", "AFlowWorkflow"),
    "ReAct": ("dslighting.workflows.search.react.workflow", "ReActWorkflow"),
}


def __getattr__(name: str) -> Any:
    target = _EXPORT_MAP.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attr_name = target
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + list(_EXPORT_MAP.keys()))
