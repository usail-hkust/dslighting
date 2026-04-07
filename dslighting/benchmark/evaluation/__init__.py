"""Benchmark evaluation exports resolved lazily."""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "EvaluationContractResolver",
    "EvaluationOutcome",
    "EvaluationSemantics",
    "TaskEvaluationContract",
    "TaskEvaluationContractRef",
    "TaskEvaluationService",
    "TaskJudgeContract",
]

_EXPORT_MAP = {
    "EvaluationContractResolver": (
        "dslighting.benchmark.evaluation.contract_resolver",
        "EvaluationContractResolver",
    ),
    "EvaluationOutcome": ("dslighting.benchmark.evaluation.outcome", "EvaluationOutcome"),
    "EvaluationSemantics": ("dslighting.benchmark.evaluation.models", "EvaluationSemantics"),
    "TaskEvaluationContract": (
        "dslighting.benchmark.evaluation.models",
        "TaskEvaluationContract",
    ),
    "TaskEvaluationContractRef": (
        "dslighting.benchmark.evaluation.models",
        "TaskEvaluationContractRef",
    ),
    "TaskEvaluationService": ("dslighting.benchmark.evaluation.service", "TaskEvaluationService"),
    "TaskJudgeContract": ("dslighting.benchmark.evaluation.models", "TaskJudgeContract"),
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
