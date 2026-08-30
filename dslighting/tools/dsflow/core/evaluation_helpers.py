"""dslighting.tools.dsflow.core.evaluation_helpers

Scoring, plan extraction, and evaluation helpers for DSFlow.
"""

from __future__ import annotations

import contextlib
import json
import logging
import re
import shutil
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from dslighting.core.data.perception import DataPerceptionRuntime
from dslighting.error import DynamicImportError
from dslighting.services.sandbox import SandboxService
from dslighting.tools.dsflow.core.models import EvalCandidate as _EvalCandidate
from dslighting.tools.dsflow.core.models import PlanScreeningResponse
from dslighting.tools.dsflow.core.models import TaskContext as _TaskContext
from dslighting.tools.dsflow.runtime import PlanCheckpoint as _PlanCheckpoint
from dslighting.tools.dsflow.runtime import StopAfterLLMCalls as _StopAfterLLMCalls
from dslighting.utils.dynamic_import import import_workflow_from_string
from dslighting.utils.parsing import parse_plan_and_code

logger = logging.getLogger(__name__)


class EvaluationHelpers:
    @staticmethod
    def _sanitize_workflow_code(workflow_code: str) -> str:
        """
        Apply light-touch fixes for common LLM workflow code issues.

        Focus: remove backslashes inside f-string expressions (SyntaxError).
        """
        code = workflow_code or ""
        fixed = code

        # Saved workflows from the standalone DSFlow repository used the old
        # ``dsat`` package name. Accept them in test mode without requiring a
        # manual rewrite.
        fixed = fixed.replace(
            "from dsat.workflows.base import DSATWorkflow",
            "from dslighting.workflows.base import BaseWorkflow",
        )
        fixed = fixed.replace(
            "from dsat.workflows.base import BaseWorkflow",
            "from dslighting.workflows.base import BaseWorkflow",
        )
        fixed = fixed.replace("DSATWorkflow", "BaseWorkflow")

        # Replace quoted f-string placeholders with repr(...) to avoid backslashes in expressions.
        # Example: '{last_error.replace(\"'\", \"\\\\'\")}' -> {repr(last_error)}
        pattern_single = re.compile(
            r"""(['"])\{\s*([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\.replace\(\s*['"]'['"]\s*,\s*['"]\\'['"]\s*\)\s*\}\1"""
        )
        pattern_double = re.compile(
            r"""(['"])\{\s*([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\.replace\(\s*['"]"['"]\s*,\s*['"]\\\"['"]\s*\)\s*\}\1"""
        )
        fixed = pattern_single.sub(r"{repr(\2)}", fixed)
        fixed = pattern_double.sub(r"{repr(\2)}", fixed)

        # If any remaining backslash-escaped replacements exist, strip the backslash to keep f-strings valid.
        fixed = re.sub(
            r"""replace\(\s*['"]'['"]\s*,\s*['"]\\'['"]\s*\)""",
            'replace("\'", "\'")',
            fixed,
        )
        fixed = re.sub(
            r"""replace\(\s*['"]\"['"]\s*,\s*['"]\\\"['"]\s*\)""",
            "replace('\"', '\"')",
            fixed,
        )

        # Replace f-string expressions like {'\\n'.join(items)} with {chr(10).join(items)}.
        fixed = re.sub(
            r"""\{\s*['"](?:\\n|\n)['"]\s*\.join\(\s*([^)]+?)\s*\)\s*\}""",
            r"{chr(10).join(\1)}",
            fixed,
            flags=re.S,
        )
        fixed = re.sub(
            r"""\{\s*['"](?:\\t|\t)['"]\s*\.join\(\s*([^)]+?)\s*\)\s*\}""",
            r"{chr(9).join(\1)}",
            fixed,
            flags=re.S,
        )

        if fixed != code:
            logger.info("Applied workflow code auto-fix: f-string backslash cleanup")
        return fixed

    @staticmethod
    def _build_no_execute_sandbox(inner: SandboxService, llm_proxy: _StopAfterLLMCalls):
        class _SandboxNoExecute:
            def __init__(self, inner_service: SandboxService, proxy: _StopAfterLLMCalls):
                self._inner = inner_service
                self._llm_proxy = proxy

            def run_script(self, code: str, *args, **kwargs):  # noqa: ANN001
                # Capture the final generated script (the one about to be executed),
                # then stop the candidate to avoid expensive execution in coarse screening.
                if isinstance(code, str) and code.strip():
                    self._llm_proxy.python_code = code.strip()
                payload = {
                    "plan": (self._llm_proxy.plan or "").strip(),
                    "python_code": (self._llm_proxy.python_code or "").strip(),
                }
                raise _PlanCheckpoint(json.dumps(payload))

            def __getattr__(self, name: str):  # noqa: ANN001
                return getattr(self._inner, name)

        return _SandboxNoExecute(inner, llm_proxy)

    @staticmethod
    def _build_execute_checkpoint(llm_proxy: _StopAfterLLMCalls):
        class _ExecutePythonCheckpoint:
            def __init__(self, proxy: _StopAfterLLMCalls):
                self._llm_proxy = proxy

            async def __call__(self, code: str, *args, **kwargs):  # noqa: ANN001
                if isinstance(code, str) and code.strip():
                    self._llm_proxy.python_code = code.strip()
                payload = {
                    "plan": (self._llm_proxy.plan or "").strip(),
                    "python_code": (self._llm_proxy.python_code or "").strip(),
                }
                raise _PlanCheckpoint(json.dumps(payload))

        return _ExecutePythonCheckpoint(llm_proxy)

    def _record_score(
        self,
        *,
        round_num: int,
        fitness: float,
        code: str,
        score_type: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        current_usage = self.llm_service.get_usage_summary()
        last_usage = self._last_usage_summary or {}
        usage_delta = {
            "prompt_tokens": current_usage.get("prompt_tokens", 0)
            - last_usage.get("prompt_tokens", 0),
            "completion_tokens": current_usage.get("completion_tokens", 0)
            - last_usage.get("completion_tokens", 0),
            "total_tokens": current_usage.get("total_tokens", 0)
            - last_usage.get("total_tokens", 0),
            "total_cost": round(
                float(current_usage.get("total_cost", 0.0) - last_usage.get("total_cost", 0.0)),
                12,
            ),
            "call_count": current_usage.get("call_count", 0) - last_usage.get("call_count", 0),
        }
        self._last_usage_summary = current_usage

        enriched: Dict[str, Any] = dict(extra or {})
        telemetry = enriched.get("telemetry")
        if not isinstance(telemetry, dict):
            telemetry = {}
            enriched["telemetry"] = telemetry

        telemetry.setdefault(
            "recorded_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )
        telemetry.setdefault("llm_usage_total", current_usage)
        telemetry.setdefault("llm_usage_delta", usage_delta)
        now_perf = time.perf_counter()
        last_perf = getattr(self, "_last_score_perf", now_perf)
        start_perf = getattr(self, "_score_perf_start", now_perf)
        telemetry.setdefault("wall_time_delta_seconds", round(float(now_perf - last_perf), 4))
        telemetry.setdefault("wall_time_total_seconds", round(float(now_perf - start_perf), 4))
        self._last_score_perf = now_perf

        self.experience.record_score(
            round_num,
            fitness,
            code,
            score_type=score_type,
            extra=enriched,
        )

    def _record_final_selection(
        self, *, candidate: _EvalCandidate, selection_extra: Dict[str, Any]
    ) -> None:
        self._record_score(
            round_num=candidate.round_num,
            fitness=candidate.fitness,
            code=candidate.code,
            score_type="final_selection",
            extra=selection_extra,
        )

    def _compute_normalized_fine_map(
        self, fine_candidates: list[_EvalCandidate]
    ) -> tuple[dict[int, float], str]:
        normalization = (
            str(getattr(self.dsflow_config, "final_fine_normalization", "rank")).strip().lower()
        )
        if normalization not in {"none", "minmax", "rank"}:
            normalization = "rank"

        if not fine_candidates:
            return {}, normalization

        fine_scores = [float(c.fitness) for c in fine_candidates]

        if normalization == "none":
            return {id(c): float(c.fitness) for c in fine_candidates}, normalization

        if normalization == "minmax":
            lo = min(fine_scores)
            hi = max(fine_scores)
            if hi == lo:
                return {id(c): 1.0 for c in fine_candidates}, normalization
            return {
                id(c): (float(c.fitness) - lo) / (hi - lo) for c in fine_candidates
            }, normalization

        # normalization == "rank"
        unique_scores = sorted(set(fine_scores), reverse=True)
        if len(unique_scores) <= 1:
            return {id(c): 1.0 for c in fine_candidates}, normalization
        score_to_norm = {
            s: 1.0 - (i / (len(unique_scores) - 1)) for i, s in enumerate(unique_scores)
        }
        return {id(c): score_to_norm[float(c.fitness)] for c in fine_candidates}, normalization

    def _select_final_candidate(
        self, fine_candidates: list[_EvalCandidate]
    ) -> tuple[_EvalCandidate, Dict[str, Any]]:
        """
        Select a final best candidate after fine evaluation.

        Returns:
            (best_candidate, selection_extra)
        """
        evaluated = [c for c in fine_candidates if c.fine_evaluated]
        if not evaluated:
            raise ValueError("No fine-evaluated candidates available for final selection.")

        selection_mode = (
            str(getattr(self.dsflow_config, "final_selection_mode", "fine")).strip().lower()
        )
        if selection_mode not in {"fine", "weighted"}:
            selection_mode = "fine"

        # Fine-only selection (tie-break by coarse score).
        if selection_mode == "fine":
            best = max(evaluated, key=lambda c: (c.fitness, c.coarse_score))
            extra: Dict[str, Any] = {
                "coarse_score": best.coarse_score,
                "selection_mode": "fine",
                "modification": best.modification,
            }
            return best, extra

        # Weighted selection.
        weight_fine = float(getattr(self.dsflow_config, "weight_fine", 0.5))
        weight_coarse = float(getattr(self.dsflow_config, "weight_coarse", 0.5))
        denom = weight_fine + weight_coarse
        if denom <= 0:
            # Degenerate configuration: fall back to fine-only selection.
            best = max(evaluated, key=lambda c: (c.fitness, c.coarse_score))
            extra = {
                "coarse_score": best.coarse_score,
                "selection_mode": "fine",
                "modification": best.modification,
            }
            return best, extra

        fine_norm_map, normalization = self._compute_normalized_fine_map(evaluated)

        def combined(c: _EvalCandidate) -> float:
            norm_fine = float(fine_norm_map.get(id(c), float(c.fitness)))
            return (weight_fine * norm_fine + weight_coarse * float(c.coarse_score)) / denom

        best = max(evaluated, key=lambda c: (combined(c), c.fitness, c.coarse_score))
        best_norm_fine = float(fine_norm_map.get(id(best), float(best.fitness)))
        best_combined = float(combined(best))

        extra = {
            "coarse_score": best.coarse_score,
            "selection_mode": "weighted",
            "modification": best.modification,
            "combined_score": best_combined,
            "normalized_fine": best_norm_fine,
            "weight_fine": weight_fine,
            "weight_coarse": weight_coarse,
            "normalization": normalization,
        }
        return best, extra

    async def _coarse_score(
        self,
        workflow_code: str,
        modification: str,
        raw_description: str,
        base_report: str,
        data_dir: Path,
        output_filename: str,
    ) -> float:
        """
        Run a cheap coarse screening pass and score the candidate with a judge LLM.

        Default behavior captures the FINAL `python_code` right before execution (but does not execute it),
        so the score reflects changes from added operators and downstream workflow logic, not just the initial plan.
        """
        ok, missing = self._validate_workflow_operators(workflow_code)
        if not ok:
            available = sorted(self._available_operator_names())
            shown_available = available[:40]
            suffix = " ..." if len(available) > len(shown_available) else ""
            logger.warning(
                "Rejecting candidate '%s': uses undefined operators %s. Available operators: %s%s",
                (modification or "").strip(),
                missing,
                shown_available,
                suffix,
            )
            return 0.0

        description = f"{raw_description}\n{base_report}"
        output_path = self.workspace.get_path("artifacts") / output_filename

        capture_mode = str(getattr(self.dsflow_config, "coarse_capture", "code")).strip().lower()
        if capture_mode not in {"plan", "code"}:
            capture_mode = "code"

        plan_text = ""
        python_code = ""

        if capture_mode == "code":
            plan_text, python_code = await self._extract_plan_and_python_code_from_workflow(
                workflow_code=workflow_code,
                description=description,
                data_dir=data_dir,
                output_path=output_path,
                max_llm_calls=int(getattr(self.dsflow_config, "coarse_max_llm_calls", 6)),
            )

        if not plan_text.strip():
            plan_text = await self._extract_plan_from_first_llm_call(
                workflow_code=workflow_code,
                description=description,
                data_dir=data_dir,
                output_path=output_path,
            )
        if not plan_text.strip():
            return 0.0

        if python_code.strip():
            try:
                compile(python_code, "<dsflow_coarse_candidate>", "exec")
            except SyntaxError as e:
                logger.warning("Rejecting candidate due to invalid generated python_code: %s", e)
                return 0.0

        shown_code = python_code.strip()
        if len(shown_code) > 4000:
            shown_code = shown_code[:4000] + "\n...[truncated]..."

        code_section = ""
        if shown_code:
            code_section = (
                f"## Generated Python Code (NOT executed)\n```python\n{shown_code}\n```\n\n"
            )

        screening_prompt = (
            "You are a STRICT evaluator for DSFlow candidate workflows. Your job is to FILTER OUT weak candidates "
            "before expensive execution.\n\n"
            f"## Candidate Modification\n{modification}\n\n"
            "## Task\n"
            f"{raw_description}\n\n"
            "## Plan (from candidate)\n"
            f"{plan_text}\n\n"
            f"{code_section}"
            "Return a JSON object with fields: thought (string) and score (0-10 float)."
        )
        try:
            judge = await self.llm_service.call_with_json(
                screening_prompt,
                output_model=PlanScreeningResponse,
            )
            score = float(judge.score)
        except Exception as e:
            logger.warning("Coarse plan scoring failed: %s", e)
            return 0.0

        score = max(0.0, min(10.0, score))
        return score / 10.0

    async def _extract_plan_and_python_code_from_workflow(
        self,
        *,
        workflow_code: str,
        description: str,
        data_dir: Path,
        output_path: Path,
        max_llm_calls: int,
    ) -> tuple[str, str]:
        """
        Execute a candidate workflow with an LLM proxy and stop right before it executes code.

        Returns (plan_text, python_code). Both may be empty on failure.
        """
        io_instructions = DataPerceptionRuntime.generate_io_instructions(
            output_path.name, optimization_context=False
        )

        try:
            workflow_code = self._sanitize_workflow_code(workflow_code)
            workflow_class = import_workflow_from_string(workflow_code)
        except DynamicImportError as e:
            logger.warning("Invalid workflow code (dynamic import failed): %s", e)
            return "", ""

        llm_proxy = _StopAfterLLMCalls(
            self.llm_service,
            stop_after=max(2, int(max_llm_calls)),
            stop_on_python_code=False,
        )
        operators = self._build_operator_instances(llm_proxy)
        # If the workflow uses the standard ExecutePython operator, stop there.
        if isinstance(operators, dict) and "ExecutePython" in operators:
            operators["ExecutePython"] = self._build_execute_checkpoint(llm_proxy)
        instance_services = {
            "llm": llm_proxy,
            # Even if a candidate bypasses ExecutePython and calls sandbox_service directly,
            # block execution in coarse screening.
            "sandbox": self._build_no_execute_sandbox(self.sandbox_service, llm_proxy),
            "workspace": self.workspace,
            "data_perception": self.data_perception,
        }
        instance = workflow_class(
            operators=operators,
            services=instance_services,
            agent_config={},
        )

        with contextlib.suppress(Exception):
            self.workspace.link_data_to_workspace(data_dir)

        try:
            await instance.solve(description, io_instructions, data_dir, output_path)
        except _PlanCheckpoint:
            pass
        except Exception as e:
            logger.debug("Candidate failed during coarse code capture: %s", e)

        plan_text = (llm_proxy.plan or "").strip()
        python_code = (llm_proxy.python_code or "").strip()

        if not plan_text and llm_proxy.last_content:
            plan_text = self._extract_plan_from_content(llm_proxy.last_content)
        if not python_code and llm_proxy.last_content:
            python_code = self._extract_python_code_from_content(llm_proxy.last_content)

        return plan_text, python_code

    async def _extract_plan_from_first_llm_call(
        self,
        workflow_code: str,
        description: str,
        data_dir: Path,
        output_path: Path,
    ) -> str:
        """Execute workflow with an LLM proxy that stops after the first LLM call."""
        io_instructions = DataPerceptionRuntime.generate_io_instructions(
            output_path.name, optimization_context=False
        )

        try:
            workflow_code = self._sanitize_workflow_code(workflow_code)
            workflow_class = import_workflow_from_string(workflow_code)
        except DynamicImportError as e:
            logger.warning("Invalid workflow code (dynamic import failed): %s", e)
            return ""

        llm_proxy = _StopAfterLLMCalls(self.llm_service, stop_after=1)
        operators = self._build_operator_instances(llm_proxy)
        if isinstance(operators, dict) and "ExecutePython" in operators:
            operators["ExecutePython"] = self._build_execute_checkpoint(llm_proxy)
        instance_services = {
            "llm": llm_proxy,
            "sandbox": self._build_no_execute_sandbox(self.sandbox_service, llm_proxy),
            "workspace": self.workspace,
            "data_perception": self.data_perception,
        }
        instance = workflow_class(
            operators=operators,
            services=instance_services,
            agent_config={},
        )

        with contextlib.suppress(Exception):
            self.workspace.link_data_to_workspace(data_dir)

        try:
            await instance.solve(description, io_instructions, data_dir, output_path)
        except _PlanCheckpoint as e:
            content = e.content
        except Exception as e:
            logger.debug("Candidate failed before checkpoint: %s", e)
            content = llm_proxy.last_content or ""
        else:
            content = llm_proxy.last_content or ""

        return self._extract_plan_from_content(content)

    @staticmethod
    def _extract_plan_from_content(content: str) -> str:
        text = (content or "").strip()
        if not text:
            return ""
        # If it's JSON, try to pull a "plan" field.
        if text.startswith("{") and text.endswith("}"):
            with contextlib.suppress(Exception):
                payload = json.loads(text)
                if isinstance(payload, dict):
                    plan = payload.get("plan")
                    if isinstance(plan, str) and plan.strip():
                        return plan.strip()
        plan, _ = parse_plan_and_code(text)
        return plan

    @staticmethod
    def _extract_python_code_from_content(content: str) -> str:
        text = (content or "").strip()
        if not text:
            return ""
        if text.startswith("{") and text.endswith("}"):
            with contextlib.suppress(Exception):
                payload = json.loads(text)
                if isinstance(payload, dict):
                    code = payload.get("python_code")
                    if isinstance(code, str) and code.strip():
                        return code.strip()
        _plan, code = parse_plan_and_code(text)
        code = (code or "").strip()
        if code.startswith("# ERROR: Could not parse code block"):
            return ""
        return code

    async def _fine_evaluate(
        self,
        workflow_code: str,
        tasks: list[_TaskContext],
    ) -> float:
        scores: list[float] = []
        analyzer = self.data_perception or DataPerceptionRuntime()

        try:
            workflow_code = self._sanitize_workflow_code(workflow_code)
            workflow_class = import_workflow_from_string(workflow_code)
        except DynamicImportError as e:
            logger.warning("Workflow evaluation failed due to invalid code: %s", e)
            return 0.0

        instance_services = {
            "llm": self.llm_service,
            "sandbox": self.sandbox_service,
            "workspace": self.workspace,
            "data_perception": self.data_perception,
        }
        operators = self._build_operator_instances(self.llm_service)
        instance = workflow_class(
            operators=operators,
            services=instance_services,
            agent_config={},
        )

        for task in tasks:
            if self._progress_enabled():
                logger.info("DSFlow progress: evaluating task '%s' (1/1)", task.competition_id)

            unique_id = uuid.uuid4().hex[:6]
            output_name = f"validation_{task.competition_id}_{unique_id}.csv"
            output_path = self.workspace.get_path("artifacts") / output_name

            io_instructions = analyzer.generate_io_instructions(
                output_path.name, optimization_context=False
            )
            description = f"{task.raw_description}\n{task.base_report}"

            try:
                self.workspace.link_data_to_workspace(task.data_dir)
                await instance.solve(description, io_instructions, task.data_dir, output_path)

                sandbox_workdir = self.workspace.get_path("sandbox_workdir")
                generated_file = sandbox_workdir / output_path.name
                if generated_file.exists() and generated_file.resolve() != output_path.resolve():
                    shutil.copy(generated_file, output_path)

                score = await self._grade_submission(output_path, task.competition_id)
                scores.append(float(score))

            except Exception as e:
                logger.warning(
                    "Workflow fine evaluation failed for %s: %s",
                    task.competition_id,
                    e,
                    exc_info=False,
                )
                scores.append(0.0)

            finally:
                if output_path.exists():
                    with contextlib.suppress(OSError):
                        output_path.unlink()

        return sum(scores) / len(scores) if scores else 0.0

    async def _grade_submission(self, submission_path: Path, competition_id: str) -> float:
        """Grade through the active DSLighting benchmark contract."""
        if not submission_path.exists() or self.benchmark is None:
            return 0.0

        grade = getattr(self.benchmark, "grade", None)
        if not callable(grade):
            return 0.0

        try:
            result = grade(submission_path, competition_id=competition_id)
        except TypeError:
            result = grade(submission_path)

        if hasattr(result, "__await__"):
            result = await result
        try:
            return float(result)
        except (TypeError, ValueError):
            return 0.0
