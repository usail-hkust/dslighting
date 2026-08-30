"""dslighting.tools.dsflow.core.operator_helpers

Operator registration, library integration, and mutation helpers for DSFlow.
"""

from __future__ import annotations

import inspect
import logging
import re
from types import SimpleNamespace
from typing import Any, Dict, Optional, Type

from dslighting.ops.base import Operator
from dslighting.ops.presets.dsflow import (
    DSCodeGenOperator,
    DSCodeRefineOperator,
    DSDataAcqValidOperator,
    DSDataInspectOperator,
    DSProblemAnalysisOperator,
    DSSubmissionValidOperator,
    ExecutePythonOperator,
    ReviewOperator,
    ReviseOperator,
    ScEnsembleOperator,
)
from dslighting.tools.dsflow.core.models import DSFlowOptimizeResponse, ProposedOperator
from dslighting.tools.dsflow.core.models import TaskContext as _TaskContext
from dslighting.tools.dsflow.operators import fix_operator_imports, import_operator_from_code
from dslighting.tools.dsflow.prompts import (
    build_operator_repair_prompt,
    build_optimizer_prompt,
    build_workflow_repair_prompt,
)
from dslighting.utils.dynamic_import import import_workflow_from_string

logger = logging.getLogger(__name__)

_CUSTOM_OPERATORS: Dict[str, Type[Operator]] = {}
CUSTOM_OPERATORS_AVAILABLE = False


class OperatorHelpers:
    def _load_dynamic_operators(self) -> None:
        """Load dynamic operators from dynamic_ops.py if it exists."""
        try:
            from dslighting.tools.dsflow.operators import dynamic_ops

            # Get all operator classes from dynamic_ops module
            for name in dir(dynamic_ops):
                if name.startswith("_"):
                    continue

                obj = getattr(dynamic_ops, name)
                if not isinstance(obj, type):
                    continue

                # Check if it's an Operator subclass
                try:
                    if issubclass(obj, Operator) and obj is not Operator:
                        # Don't override builtin operators
                        if name not in self._builtin_operator_names:
                            doc = (inspect.getdoc(obj) or "").strip()
                            self.operator_catalog.register(name, obj, doc or f"{obj.__name__}")
                            logger.info("Loaded dynamic operator: %s", name)
                except TypeError:
                    continue

        except ImportError:
            logger.debug("No dynamic_ops module found, skipping dynamic operator loading")
        except Exception as e:
            logger.warning("Failed to load dynamic operators: %s", e)

    def _register_default_operators(self) -> None:
        builtin_ops: Dict[str, Type[Operator]] = {
            "ScEnsemble": ScEnsembleOperator,
            "Review": ReviewOperator,
            "Revise": ReviseOperator,
            "DSDataInspect": DSDataInspectOperator,
            "DSProblemAnalysis": DSProblemAnalysisOperator,
            "DSCodeGen": DSCodeGenOperator,
            "DSCodeRefine": DSCodeRefineOperator,
            "DSDataAcqValid": DSDataAcqValidOperator,
            "DSSubmissionValid": DSSubmissionValidOperator,
            "ExecutePython": ExecutePythonOperator,
        }

        custom_ops: Dict[str, Type[Operator]] = {}
        if CUSTOM_OPERATORS_AVAILABLE and isinstance(_CUSTOM_OPERATORS, dict):
            for name, cls in _CUSTOM_OPERATORS.items():
                if not isinstance(name, str) or not name.strip():
                    continue
                if not isinstance(cls, type) or not issubclass(cls, Operator):
                    continue
                if name in builtin_ops:
                    logger.warning("Skipping custom operator that shadows builtin: %s", name)
                    continue
                custom_ops[name] = cls

        if custom_ops:
            logger.info(
                "Loaded %d DSFlow custom operator(s) from dsflow_custom_ops.py",
                len(custom_ops),
            )

        all_ops: Dict[str, Type[Operator]] = {**builtin_ops, **custom_ops}
        self._builtin_operator_names = set(all_ops)
        for name, cls in all_ops.items():
            doc = (inspect.getdoc(cls) or "").strip()
            self.operator_catalog.register(name, cls, doc or f"{cls.__name__}")

    def _available_operator_names(self) -> set[str]:
        if self._external_operator_instances is not None:
            return {name for name in self._external_operator_instances.keys() if name}
        return set(self.operator_catalog.export_classes().keys())

    def export_operator_classes(self) -> Dict[str, Type[Operator]]:
        """
        Export operator classes for workflow test mode and dynamic factory usage.
        """
        if self._external_operator_instances is not None:
            return {name: op.__class__ for name, op in self._external_operator_instances.items()}
        return self.operator_catalog.export_classes()

    def _validate_workflow_operators(self, workflow_code: str) -> tuple[bool, list[str]]:
        used = self._extract_operator_names_used(workflow_code)
        if not used:
            return True, []

        available = self._available_operator_names()
        missing = sorted([name for name in used if name not in available])
        return (len(missing) == 0), missing

    def ensure_operators_for_workflow(self, workflow_code: str) -> None:
        """
        Ensure the operator toolbox contains every operator referenced by `workflow_code`.

        This is primarily used by "test mode" runs which evaluate a saved best_workflow.py
        without re-running meta-optimization. When an operator is missing, this method
        attempts to load its best version from the operator library.
        """
        if self._external_operator_instances is not None:
            return

        ok, missing = self._validate_workflow_operators(workflow_code)
        if ok or not missing:
            return

        if self.operator_library is None:
            raise ValueError(
                f"Workflow references undefined operators: {missing}. "
                "Enable `dsflow.operator_library_enabled` or sync custom operators."
            )

        loaded: list[str] = []
        for name in missing:
            if self.operator_catalog.has(name):
                continue

            spec = self.operator_library.get_best_version(name)
            if spec is None:
                continue

            try:
                cls = self._import_operator_from_code(
                    spec.code,
                    name,
                    description=getattr(spec, "description", "") or "",
                    inputs=getattr(spec, "inputs", "") or "",
                    outputs=getattr(spec, "outputs", "") or "",
                )
                self._validate_proposed_operator_class(cls)
                self.operator_catalog.register(
                    name, cls, self._format_library_operator_description(spec)
                )
                self._library_versions[name] = int(spec.version)
                loaded.append(name)
            except Exception as e:
                logger.warning("Failed to load operator '%s' from library: %s", name, e)

        ok2, missing2 = self._validate_workflow_operators(workflow_code)
        if ok2:
            if loaded:
                logger.info("Loaded %d missing operator(s) from library: %s", len(loaded), loaded)
            return

        raise ValueError(
            f"Workflow still references undefined operators after library load: {missing2}. "
            "Re-run meta-optimization with operator_library_enabled=True, or run sync_custom_operators."
        )

    def _register_library_operators(self, tasks: list[_TaskContext]) -> None:
        if self.operator_library is None or self._external_operator_instances is not None:
            return

        max_ops = int(getattr(self.dsflow_config, "operator_library_max_ops_in_prompt", 0))
        if max_ops <= 0:
            return

        competition_ids = [t.competition_id for t in tasks]
        inferred_task_types = sorted(self._infer_task_types(tasks))
        try:
            specs = self.operator_library.select_for_prompt(
                max_ops,
                competition_ids=competition_ids,
                task_types=inferred_task_types,
            )
        except Exception as e:
            logger.warning("Operator library selection failed: %s", e)
            return

        for spec in specs:
            name = (spec.name or "").strip()
            if not name or self.operator_catalog.has(name) or name in self._builtin_operator_names:
                continue

            try:
                cls = self._import_operator_from_code(
                    spec.code,
                    name,
                    description=getattr(spec, "description", "") or "",
                    inputs=getattr(spec, "inputs", "") or "",
                    outputs=getattr(spec, "outputs", "") or "",
                )
                self._validate_proposed_operator_class(cls)
            except Exception as e:
                logger.warning(
                    "Skipping library operator '%s' (v%d): %s",
                    name,
                    spec.version,
                    e,
                )
                continue

            self.operator_catalog.register(
                name, cls, self._format_library_operator_description(spec)
            )
            self._library_versions[name] = int(spec.version)
            logger.info("Loaded operator from library: %s (v%d)", name, spec.version)

    @staticmethod
    def _format_library_operator_description(spec) -> str:  # noqa: ANN001
        desc = (getattr(spec, "description", "") or "").strip()
        inputs = (getattr(spec, "inputs", "") or "").strip()
        outputs = (getattr(spec, "outputs", "") or "").strip()
        triggers = (getattr(spec, "triggers", "") or "").strip()
        if len(triggers) > 160:
            triggers = triggers[:160] + "..."
        if len(inputs) > 140:
            inputs = inputs[:140] + "..."
        if len(outputs) > 140:
            outputs = outputs[:140] + "..."
        task_types = list(getattr(spec, "task_types", []) or [])
        if len(task_types) > 6:
            task_types = task_types[:6]

        meta_parts = [
            f"lib v{getattr(spec, 'version', 1)}",
            f"succ {getattr(spec, 'successes', 0)}/{getattr(spec, 'uses', 0)}",
        ]
        if task_types:
            meta_parts.append(f"tasks: {', '.join(task_types)}")
        if inputs:
            meta_parts.append(f"in: {inputs}")
        if outputs:
            meta_parts.append(f"out: {outputs}")
        if triggers:
            meta_parts.append(f"triggers: {triggers}")
        meta = "; ".join(meta_parts)
        return f"{desc} ({meta})".strip()

    def _record_operator_library_outcome(
        self,
        *,
        workflow_code: str,
        success: bool,
        tasks: list[_TaskContext],
    ) -> None:
        if self.operator_library is None or not self._library_versions:
            return

        used = self._extract_operator_names_used(workflow_code)
        if not used:
            return

        competition_ids = [t.competition_id for t in tasks]
        for name in used:
            version = self._library_versions.get(name)
            if version is None:
                continue
            self.operator_library.record_outcome(
                name,
                version,
                success=bool(success),
                competition_ids=competition_ids,
            )

    @staticmethod
    def _extract_operator_names_used(workflow_code: str) -> set[str]:
        code = workflow_code or ""
        names = set(re.findall(r"self\.operators\s*\[\s*['\"]([^'\"]+)['\"]\s*\]", code))
        names.update(re.findall(r"self\.operators\.get\(\s*['\"]([^'\"]+)['\"]", code))
        return {n.strip() for n in names if n and n.strip()}

    async def _mutate_workflow(
        self, parent_code: str, parent_score: float, parent_round_num: int, task_hint: str
    ) -> tuple[str, str, str]:
        """
        Mutate workflow using LLM optimizer.

        Returns:
            tuple[str, str, str]: (graph_code, modification_summary, thought_process)
        """
        experience_str = self.experience.get_experience_summary(parent_round_num)
        operator_catalog = self.operator_catalog.describe()
        base_prompt = self._build_optimizer_prompt(
            experience=experience_str,
            parent_score=parent_score,
            parent_code=parent_code,
            operator_catalog=operator_catalog,
            task_hint=task_hint,
        )

        max_attempts = max(
            1, int(getattr(self.dsflow_config, "workflow_generation_max_attempts", 1))
        )
        last_error = ""
        last_code = ""
        last_resp: Optional[DSFlowOptimizeResponse] = None

        for attempt in range(max_attempts):
            if attempt == 0:
                prompt = base_prompt
            else:
                prompt = build_workflow_repair_prompt(
                    error_message=last_error,
                    invalid_code=last_code,
                    operator_catalog=operator_catalog,
                )

            resp = await self.llm_service.call_with_json(
                prompt, output_model=DSFlowOptimizeResponse
            )

            if resp.thought:
                logger.info(
                    "Meta-optimizer thought (round %d attempt %d/%d): %s",
                    parent_round_num,
                    attempt + 1,
                    max_attempts,
                    resp.thought[:200] + "...",
                )

            candidate_code = resp.graph
            sanitize = getattr(self, "_sanitize_workflow_code", None)
            if callable(sanitize):
                candidate_code = sanitize(candidate_code)

            try:
                import_workflow_from_string(candidate_code)
            except Exception as e:
                last_error = str(e)
                last_code = candidate_code
                last_resp = resp
                logger.warning(
                    "Generated workflow invalid (round %d attempt %d/%d): %s",
                    parent_round_num,
                    attempt + 1,
                    max_attempts,
                    last_error,
                )
                continue

            await self._register_proposed_operators(resp.operators)
            return candidate_code, resp.modification, resp.thought

        if last_resp is not None:
            await self._register_proposed_operators(last_resp.operators)
            return last_code or last_resp.graph, last_resp.modification, last_resp.thought

        return "", "", ""

    @staticmethod
    def _build_optimizer_prompt(
        experience: str,
        parent_score: float,
        parent_code: str,
        operator_catalog: str,
        task_hint: str,
    ) -> str:
        return build_optimizer_prompt(
            experience=experience,
            parent_score=parent_score,
            parent_code=parent_code,
            operator_catalog=operator_catalog,
            task_hint=task_hint,
        )

    async def _register_proposed_operators(self, proposed: list[ProposedOperator]) -> None:
        if not proposed:
            return

        max_attempts = max(
            1, int(getattr(self.dsflow_config, "operator_generation_max_attempts", 1))
        )
        operator_catalog = self.operator_catalog.describe()
        existing_names = sorted(self._available_operator_names())
        shown_existing = existing_names[:80]
        existing_label = ", ".join(shown_existing)
        if len(existing_names) > len(shown_existing):
            existing_label += ", ..."

        for spec in proposed:
            current_spec = spec
            last_error = ""
            for attempt in range(max_attempts):
                name = (current_spec.name or "").strip()
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
                    last_error = f"Invalid operator name: {current_spec.name!r}"
                elif name in self._builtin_operator_names:
                    last_error = f"Operator name shadows builtin: {name}"
                else:
                    try:
                        self._register_operator_spec(current_spec)
                        last_error = ""
                        break
                    except Exception as e:
                        last_error = str(e)

                if attempt + 1 >= max_attempts:
                    logger.warning(
                        "Failed to register operator '%s' after %d attempt(s): %s",
                        name or current_spec.name,
                        attempt + 1,
                        last_error,
                    )
                    break

                try:
                    current_spec = await self._repair_operator_spec(
                        current_spec,
                        error_message=last_error,
                        operator_catalog=operator_catalog,
                        existing_names=existing_label,
                    )
                except Exception as e:
                    logger.warning(
                        "Operator repair failed for '%s': %s", name or current_spec.name, e
                    )
                    break
            if last_error:
                continue

    def _register_operator_spec(self, spec: ProposedOperator) -> None:
        name = spec.name.strip()

        cls = self._import_operator_from_code(
            spec.code,
            name,
            description=getattr(spec, "description", "") or "",
            inputs=getattr(spec, "inputs", "") or "",
            outputs=getattr(spec, "outputs", "") or "",
        )
        self._validate_proposed_operator_class(cls)
        self._test_instantiate_operator(cls, name)

        effective_inputs = (getattr(spec, "inputs", "") or "").strip()
        effective_outputs = (getattr(spec, "outputs", "") or "").strip()
        if not effective_inputs or not effective_outputs:
            inferred_inputs, inferred_outputs = self._infer_operator_contract(cls)
            if not effective_inputs:
                effective_inputs = inferred_inputs or "(no inputs)"
            if not effective_outputs:
                effective_outputs = inferred_outputs or "Any"

        version: Optional[int] = None
        if self.operator_library is not None:
            try:
                version = self.operator_library.add_version(
                    name,
                    code=spec.code,
                    description=spec.description,
                    inputs=effective_inputs,
                    outputs=effective_outputs,
                    triggers=getattr(spec, "triggers", "") or "",
                    task_types=getattr(spec, "task_types", []) or [],
                )
            except Exception as e:
                logger.warning("Failed to persist operator '%s' to library: %s", name, e)

        if self.operator_catalog.has(name):
            logger.info(
                "Operator '%s' already exists; stored version=%s in library (not overriding).",
                name,
                version,
            )
            return

        desc = (spec.description or "").strip()
        triggers = (getattr(spec, "triggers", "") or "").strip()
        task_types = [
            t for t in (getattr(spec, "task_types", []) or []) if isinstance(t, str) and t.strip()
        ]
        if version is not None:
            desc = self._format_library_operator_description(
                SimpleNamespace(
                    description=spec.description,
                    inputs=effective_inputs,
                    outputs=effective_outputs,
                    triggers=triggers,
                    task_types=task_types,
                    version=version,
                    uses=0,
                    successes=0,
                )
            )
            self._library_versions[name] = int(version)
        else:
            meta_parts: list[str] = []
            shown_inputs = effective_inputs.strip()
            shown_outputs = effective_outputs.strip()
            if len(shown_inputs) > 140:
                shown_inputs = shown_inputs[:140] + "..."
            if len(shown_outputs) > 140:
                shown_outputs = shown_outputs[:140] + "..."
            if task_types:
                meta_parts.append(f"tasks: {', '.join(task_types[:6])}")
            if shown_inputs:
                meta_parts.append(f"in: {shown_inputs}")
            if shown_outputs:
                meta_parts.append(f"out: {shown_outputs}")
            if triggers:
                shown_triggers = triggers[:160] + "..." if len(triggers) > 160 else triggers
                meta_parts.append(f"triggers: {shown_triggers}")
            if meta_parts:
                desc = f"{desc} ({'; '.join(meta_parts)})".strip()

        self.operator_catalog.register(name, cls, desc)
        logger.info("Registered new operator: %s", name)

    async def _repair_operator_spec(
        self,
        spec: ProposedOperator,
        *,
        error_message: str,
        operator_catalog: str,
        existing_names: str,
    ) -> ProposedOperator:
        payload = (
            f"name: {spec.name}\n"
            f"description: {spec.description}\n"
            f"inputs: {spec.inputs}\n"
            f"outputs: {spec.outputs}\n"
            f"triggers: {spec.triggers}\n"
            f"task_types: {spec.task_types}\n"
            f"code:\n{spec.code}\n"
        )
        prompt = build_operator_repair_prompt(
            error_message=error_message,
            operator_spec=payload,
            operator_catalog=operator_catalog,
            existing_names=existing_names,
        )
        repaired = await self.llm_service.call_with_json(prompt, output_model=ProposedOperator)
        return repaired

    @staticmethod
    def _format_annotation(annotation: Any) -> str:
        try:
            if isinstance(annotation, type):
                return annotation.__name__
        except Exception:
            pass
        return str(annotation).replace("typing.", "")

    @classmethod
    def _infer_operator_contract(cls, operator_cls: Type[Operator]) -> tuple[str, str]:
        try:
            sig = inspect.signature(getattr(operator_cls, "__call__"))
        except Exception:
            return "", "Any"

        inputs: list[str] = []
        for param in sig.parameters.values():
            if param.name == "self":
                continue
            name = param.name
            if param.kind is inspect.Parameter.VAR_POSITIONAL:
                name = f"*{name}"
            elif param.kind is inspect.Parameter.VAR_KEYWORD:
                name = f"**{name}"

            ann = ""
            if param.annotation is not inspect._empty:
                ann = cls._format_annotation(param.annotation)
            inputs.append(f"- {name}{(': ' + ann) if ann else ''}")

        ret = sig.return_annotation
        outputs = "Any"
        if ret is not inspect._empty:
            rendered = cls._format_annotation(ret).strip()
            outputs = rendered or "Any"

        return "\n".join(inputs).strip(), outputs

    @staticmethod
    def _validate_proposed_operator_class(cls: Type[Operator]) -> None:
        if not inspect.iscoroutinefunction(getattr(cls, "__call__", None)):
            raise TypeError("Proposed operator must implement `async def __call__(...)`.")

        init_sig = inspect.signature(cls.__init__)
        required_params = []
        allowed = {
            "llm_service",
            "sandbox_service",
            "workspace",
            "operators",
            "data_perception",
        }
        for param in init_sig.parameters.values():
            if param.name == "self":
                continue
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
            if param.default is inspect._empty:
                required_params.append(param.name)

        unsupported = [name for name in required_params if name not in allowed]
        if unsupported:
            raise TypeError(
                "Proposed operator has unsupported required __init__ params: "
                f"{unsupported}. Allowed: {sorted(allowed)}."
            )

        doc = (inspect.getdoc(cls) or "").strip()
        if "inputs:" not in doc.lower() or "outputs:" not in doc.lower():
            raise TypeError(
                "Proposed operator must include a class docstring with 'Inputs:' and 'Outputs:'."
            )

    def _test_instantiate_operator(self, cls: Type[Operator], name: str) -> None:
        if self._external_operator_instances is not None:
            return
        try:
            operators = self.operator_catalog.build(
                self.llm_service,
                self.sandbox_service,
                self.workspace,
                self.data_perception,
            )
            self.operator_catalog._instantiate(
                cls=cls,
                llm_service=self.llm_service,
                sandbox_service=self.sandbox_service,
                workspace=self.workspace,
                operators=operators,
                data_perception=self.data_perception,
            )
        except Exception as e:
            raise TypeError(f"Operator '{name}' failed instantiation smoke test: {e}") from e

        allowed = {
            "self",
            "llm_service",
            "sandbox_service",
            "workspace",
            "name",
            "operators",
            "data_perception",
        }
        for param in inspect.signature(cls.__init__).parameters.values():
            if param.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                continue
            if param.name in allowed:
                continue
            if param.default is inspect.Parameter.empty:
                raise TypeError(
                    f"Unsupported required constructor arg: {param.name}. "
                    "Use llm_service/sandbox_service/workspace/operators/data_perception "
                    "(or give defaults)."
                )

    @staticmethod
    def _fix_operator_imports(code: str) -> str:
        return fix_operator_imports(code)

    @staticmethod
    def _import_operator_from_code(
        code: str,
        class_name: str,
        *,
        description: str = "",
        inputs: str = "",
        outputs: str = "",
    ) -> Type[Operator]:
        return import_operator_from_code(
            code,
            class_name,
            description=description,
            inputs=inputs,
            outputs=outputs,
        )

    def _build_operator_instances(self, llm_service) -> Dict[str, Any]:  # noqa: ANN001
        if self._external_operator_instances is not None:
            return self._external_operator_instances
        return self.operator_catalog.build(
            llm_service,
            self.sandbox_service,
            self.workspace,
            self.data_perception,
        )
