"""dslighting.tools.dsflow.runtime.llm_checkpoint

Helpers for early-stopping DSFlow candidate workflows during coarse screening.
"""

from __future__ import annotations

import contextlib
import json
from typing import Optional

from dslighting.services.llm import LLMService
from dslighting.utils.parsing import parse_plan_and_code


class PlanCheckpoint(BaseException):
    """Internal control-flow exception used to stop a candidate early."""

    def __init__(self, content: str):
        super().__init__("Plan checkpoint reached")
        self.content = content


class StopAfterLLMCalls:
    """LLMService wrapper that raises a checkpoint after N calls."""

    def __init__(
        self,
        inner: LLMService,
        stop_after: int = 1,
        *,
        stop_on_plan: bool = False,
        stop_on_python_code: bool = False,
    ):
        self._inner = inner
        self._stop_after = max(1, int(stop_after))
        self._stop_on_plan = bool(stop_on_plan)
        self._stop_on_python_code = bool(stop_on_python_code)
        self._count = 0
        self.last_content: Optional[str] = None
        self.plan: Optional[str] = None
        self.python_code: Optional[str] = None

    def _capture_plan_and_code(self, content: str) -> None:
        text = (content or "").strip()
        if not text:
            return

        if text.startswith("{") and text.endswith("}"):
            with contextlib.suppress(Exception):
                payload = json.loads(text)
                if isinstance(payload, dict):
                    plan = payload.get("plan")
                    if isinstance(plan, str) and plan.strip():
                        self.plan = plan.strip()
                    python_code = payload.get("python_code")
                    if isinstance(python_code, str) and python_code.strip():
                        self.python_code = python_code.strip()
                    return

        plan, code = parse_plan_and_code(text)
        if plan and plan.strip():
            self.plan = plan.strip()
        code = (code or "").strip()
        if code and not code.startswith("# ERROR: Could not parse code block"):
            self.python_code = code

    async def call(self, *args, **kwargs) -> str:  # noqa: ANN001
        content = await self._inner.call(*args, **kwargs)
        self._count += 1
        self.last_content = content
        self._capture_plan_and_code(content)
        if self._stop_on_python_code and self.python_code:
            raise PlanCheckpoint(content)
        if self._stop_on_plan and self.plan:
            raise PlanCheckpoint(content)
        if self._count >= self._stop_after:
            raise PlanCheckpoint(content)
        return content

    async def call_with_json(self, *args, **kwargs):  # noqa: ANN001
        model = await self._inner.call_with_json(*args, **kwargs)
        self._count += 1
        self.last_content = model.model_dump_json()

        with contextlib.suppress(Exception):
            data = model.model_dump()
            if isinstance(data, dict):
                plan = data.get("plan")
                if isinstance(plan, str) and plan.strip():
                    self.plan = plan.strip()
                python_code = data.get("python_code")
                if isinstance(python_code, str) and python_code.strip():
                    self.python_code = python_code

        if self._stop_on_python_code and self.python_code:
            raise PlanCheckpoint(self.last_content)
        if self._stop_on_plan and self.plan:
            raise PlanCheckpoint(self.last_content)
        if self._count >= self._stop_after:
            raise PlanCheckpoint(self.last_content)
        return model

    def __getattr__(self, name: str):  # noqa: ANN001
        return getattr(self._inner, name)
