"""dslighting.tools.dsflow.operators.catalog

Operator catalog used by DSFlow to build an operator toolbox.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Dict, Type

from pydantic import BaseModel

from dslighting.core.data.perception import DataPerceptionRuntime
from dslighting.ops.base import Operator
from dslighting.services.llm import LLMService
from dslighting.services.sandbox import SandboxService
from dslighting.services.workspace import WorkspaceService


@dataclass(frozen=True)
class OperatorDef:
    cls: Type[Operator]
    description: str


class OperatorCatalog:
    def __init__(self):
        self._defs: Dict[str, OperatorDef] = {}

    def register(self, name: str, cls: Type[Operator], description: str) -> None:
        self._defs[name] = OperatorDef(cls=cls, description=(description or "").strip())

    def has(self, name: str) -> bool:
        return name in self._defs

    def export_classes(self) -> Dict[str, Type[Operator]]:
        return {name: defn.cls for name, defn in self._defs.items()}

    def describe(self) -> str:
        lines = []
        for name in sorted(self._defs):
            desc = self._defs[name].description
            cls = self._defs[name].cls
            doc = inspect.getdoc(cls) or ""

            # Extract return type annotation from __call__ method if available
            call_method = getattr(cls, "__call__", None)
            return_type = "Any"
            call_sig = ""
            return_annotation = inspect.Signature.empty
            if call_method:
                sig = inspect.signature(call_method)
                return_annotation = sig.return_annotation
                params = []
                for param in sig.parameters.values():
                    if param.name == "self":
                        continue
                    params.append(param.name)
                if len(params) > 6:
                    params = params[:6] + ["..."]
                call_sig = f"({', '.join(params)})"
                return_type = self._format_return_type(return_annotation)

            summary = self._compact_description(desc)
            outputs = self._describe_outputs(doc, return_annotation, return_type)
            if summary:
                lines.append(
                    f"- {name}{call_sig} -> {return_type} | outputs: {outputs} | {summary}"
                )
            else:
                lines.append(f"- {name}{call_sig} -> {return_type} | outputs: {outputs}")
        return "\n".join(lines)

    @staticmethod
    def _format_return_type(annotation: Any) -> str:
        if annotation in (inspect.Signature.empty, None):
            return "Any"
        if isinstance(annotation, type):
            return annotation.__name__
        text = str(annotation).replace("typing.", "")
        text = text.replace("<class '", "").replace("'>", "")
        text = text.replace("dslighting.ops.dsflow_ops.", "")
        text = text.replace("dslighting.ops.dsflow_custom_ops.", "")
        text = text.replace("dslighting.tools.dsflow.operators.dynamic_ops.", "")
        text = text.replace("dslighting.utils.typing.", "")
        if text in ("typing.Any", "Any"):
            return "Any"
        return text

    @classmethod
    def _describe_outputs(cls, doc: str, annotation: Any, return_type: str) -> str:
        # Prefer structured fields for Pydantic models.
        if isinstance(annotation, type):
            try:
                if issubclass(annotation, BaseModel):
                    fields = []
                    for name, field in annotation.model_fields.items():
                        ann = field.annotation
                        fields.append(f"{name}: {cls._format_return_type(ann)}")
                    if fields:
                        payload = ", ".join(fields)
                        payload = cls._truncate_text(payload, 140)
                        return f"{annotation.__name__}({payload})"
                    return annotation.__name__
            except Exception:
                pass

        doc_outputs = cls._extract_outputs_from_docstring(doc)
        if doc_outputs:
            return doc_outputs
        return return_type or "Any"

    @staticmethod
    def _extract_outputs_from_docstring(doc: str) -> str:
        if not doc:
            return ""
        lines = [ln.strip() for ln in doc.splitlines()]
        start = None
        for idx, line in enumerate(lines):
            if line.lower().startswith("outputs:"):
                start = idx + 1
                break
        if start is None:
            return ""
        collected: list[str] = []
        for line in lines[start:]:
            lower = line.lower()
            if lower.startswith("inputs:") or lower.startswith("call signature:"):
                break
            if not line:
                continue
            collected.append(line.lstrip("- ").strip())
        if not collected:
            return ""
        text = " ".join(collected)
        text = " ".join(text.split())
        return OperatorCatalog._truncate_text(text, 140)

    @staticmethod
    def _truncate_text(text: str, limit: int) -> str:
        if len(text) <= limit:
            return text
        return text[:limit] + "..."

    @staticmethod
    def _compact_description(desc: str) -> str:
        text = (desc or "").strip()
        if not text:
            return ""
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        for line in lines:
            lower = line.lower()
            if lower.startswith("inputs:") or lower.startswith("outputs:"):
                continue
            if lower.startswith("call signature:"):
                continue
            summary = line
            if len(summary) > 140:
                summary = summary[:140] + "..."
            return summary
        summary = lines[0] if lines else ""
        if len(summary) > 140:
            summary = summary[:140] + "..."
        return summary

    def build(
        self,
        llm_service: LLMService,
        sandbox_service: SandboxService,
        workspace: WorkspaceService,
        data_perception: DataPerceptionRuntime | None = None,
    ) -> Dict[str, Operator]:
        operators: Dict[str, Operator] = {}
        for name, defn in self._defs.items():
            operators[name] = self._instantiate(
                defn.cls,
                llm_service,
                sandbox_service,
                workspace,
                operators,
                data_perception,
            )
        return operators

    @staticmethod
    def _instantiate(
        cls: Type[Operator],
        llm_service: LLMService,
        sandbox_service: SandboxService,
        workspace: WorkspaceService,
        operators: Dict[str, Operator] | None = None,
        data_perception: DataPerceptionRuntime | None = None,
    ) -> Operator:
        params = inspect.signature(cls.__init__).parameters
        kwargs: Dict[str, Any] = {}
        if "llm_service" in params:
            kwargs["llm_service"] = llm_service
        if "sandbox_service" in params:
            kwargs["sandbox_service"] = sandbox_service
        if "workspace" in params:
            kwargs["workspace"] = workspace
        if "operators" in params:
            kwargs["operators"] = operators if operators is not None else {}
        if "data_perception" in params:
            kwargs["data_perception"] = data_perception
        return cls(**kwargs)  # type: ignore[arg-type]
