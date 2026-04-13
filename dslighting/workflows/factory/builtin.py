"""Built-in workflow factory implementations.

This module contains the concrete workflow factories used by DSLightingRunner.
All built-ins inherit from BaseWorkflowFactory so the factory hierarchy is single-rooted.
"""

from __future__ import annotations

import inspect
import logging
from typing import Any, Dict, Optional, Type

from dslighting.benchmark.core.base import BaseBenchmark
from dslighting.config import OutputContractConfig
from dslighting.error import ConfigurationError, DynamicImportError
from dslighting.ops.code import ExecuteAndTestOperator
from dslighting.ops.llm.basic import (
    GenerateCodeAndPlanOperator,
    LLMBasedReviewOperator,
    PlanOperator,
)
from dslighting.ops.presets import AFlowReviewOperator, AFlowReviseOperator, ScEnsembleOperator
from dslighting.ops.presets.automind import ComplexityScorerOperator, PlanDecomposerOperator
from dslighting.ops.presets.dsagent import (
    DevelopPlanOperator,
    ExecutePlanOperator,
    ReviseLogOperator,
)
from dslighting.core.visualization_policy import (
    resolve_visualization_policy_from_config,
    should_force_noninteractive_backend,
)
from dslighting.services.llm import LLMService
from dslighting.services.data_analysis_provider import create_data_perception_runtime
from dslighting.services.sandbox import SandboxService
from dslighting.services.vdb import VDBService
from dslighting.services.workspace import WorkspaceService
from dslighting.state.dsagent import DSAgentState
from dslighting.state.search.journal import JournalState
from dslighting.utils.dynamic_import import import_workflow_from_string
from dslighting.workflows.base import BaseWorkflow
from dslighting.workflows.factory.base import BaseWorkflowFactory
from dslighting.workflows.manual.autokaggle_workflow import AutoKaggleWorkflow
from dslighting.workflows.manual.data_interpreter_workflow import DataInterpreterWorkflow
from dslighting.workflows.manual.deepanalyze_workflow import DeepAnalyzeWorkflow
from dslighting.workflows.manual.dsagent_workflow import DSAgentWorkflow
from dslighting.workflows.manual.my_custom_agent_workflow import MyCustomAgentWorkflow
from dslighting.workflows.search.aflow_workflow import AFlowWorkflow
from dslighting.workflows.search.aide_workflow import AIDEWorkflow
from dslighting.workflows.search.automind_workflow import AutoMindWorkflow
from dslighting.workflows.search.react.context_manager import (
    build_react_context_config,
)
from dslighting.workflows.search.react.validation import (
    validate_react_operator_params,
)
from dslighting.workflows.search.react.workflow import ReActWorkflow

logger = logging.getLogger(__name__)


def _resolve_sandbox_env(config: Any) -> Optional[Dict[str, str]]:
    parameters = getattr(config.run, "parameters", None) or {}
    sandbox_env = parameters.get("sandbox_env")
    if not isinstance(sandbox_env, dict):
        return None
    return {str(key): str(value) for key, value in sandbox_env.items() if value is not None}


def _create_sandbox_service(workspace: WorkspaceService, config: Any) -> SandboxService:
    backend_type = getattr(config.sandbox, "backend", "local")
    backend_type_option = getattr(config.sandbox, "backend_type", "docker")
    api_key = getattr(config.sandbox, "api_key", None)
    visualization_policy = resolve_visualization_policy_from_config(config)
    force_noninteractive_backend = should_force_noninteractive_backend(visualization_policy)
    env_overrides = _resolve_sandbox_env(config) or {}
    if force_noninteractive_backend:
        env_overrides = {**env_overrides, "MPLBACKEND": "Agg"}

    from dslighting.services.sandbox_backends.backends.base import SandboxBackendConfig
    from dslighting.services.sandbox_backends.backends.local import LocalSandboxBackend

    backend_config = SandboxBackendConfig(
        timeout=config.sandbox.timeout,
        env_vars=dict(env_overrides),
    )

    if backend_type == "e2b":
        from dslighting.services.sandbox_backends.backends.e2b import E2BSandboxBackend

        backend = E2BSandboxBackend(config=backend_config, api_key=api_key)
    elif backend_type == "ds_sandbox":
        from dslighting.services.sandbox_backends.backends.ds_sandbox import DSSandboxBackend

        backend = DSSandboxBackend(config=backend_config, backend_type=backend_type_option)
    else:
        backend = LocalSandboxBackend(
            config=backend_config,
            env_overrides=env_overrides,
        )

    return SandboxService(
        workspace=workspace,
        backend=backend,
        timeout=config.sandbox.timeout,
        env_overrides=env_overrides,
        auto_matplotlib=force_noninteractive_backend,
        visualization_policy=visualization_policy,
    )


def _resolve_rag_settings(config: Any, workflow_name: str) -> tuple[bool, str]:
    params = getattr(config.workflow, "params", None) or {}
    enable_rag = params.get("enable_rag", False)
    case_dir = params.get("case_dir", "experience_replay")

    if not isinstance(enable_rag, bool):
        raise ConfigurationError(
            f"`{workflow_name}.enable_rag` must be a boolean, got: {type(enable_rag).__name__}",
            error_code="CFG-002",
        )
    if not isinstance(case_dir, str) or not case_dir.strip():
        raise ConfigurationError(
            f"`{workflow_name}.case_dir` must be a non-empty string",
            error_code="CFG-002",
        )
    return enable_rag, case_dir


def _resolve_agent_runtime_settings(config: Any) -> tuple[int, int, int, int, Any]:
    agent_runtime = getattr(config, "agent_runtime", None)
    observation = getattr(agent_runtime, "observation", None)
    context = getattr(agent_runtime, "context", None)

    max_steps_value = int(getattr(agent_runtime, "max_steps", 10) or 10)
    obs_max_tokens_value = int(getattr(observation, "max_tokens", 4000) or 4000)
    obs_head_tokens_value = int(getattr(observation, "head_tokens", 2000) or 2000)
    obs_tail_tokens_value = int(getattr(observation, "tail_tokens", 2000) or 2000)
    raw_context = context.model_dump() if hasattr(context, "model_dump") else context

    if max_steps_value <= 0:
        raise ConfigurationError(
            "`agent_runtime.max_steps` must be > 0",
            error_code="CFG-002",
        )
    try:
        context_config = build_react_context_config(raw_context)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(
            f"Invalid `agent_runtime.context`: {exc}",
            error_code="CFG-002",
        ) from None

    try:
        validate_react_operator_params(
            obs_max_tokens=obs_max_tokens_value,
            obs_head_tokens=obs_head_tokens_value,
            obs_tail_tokens=obs_tail_tokens_value,
        )
    except ValueError as exc:
        raise ConfigurationError(str(exc), error_code="CFG-002") from None

    return (
        max_steps_value,
        obs_max_tokens_value,
        obs_head_tokens_value,
        obs_tail_tokens_value,
        context_config,
    )


def _resolve_output_contract_settings(config: Any) -> OutputContractConfig:
    raw = getattr(config, "output_contract", None)
    if isinstance(raw, OutputContractConfig):
        return raw
    if raw is None:
        return OutputContractConfig()
    if hasattr(raw, "model_dump"):
        raw = raw.model_dump()
    if not isinstance(raw, dict):
        raise ConfigurationError(
            "`output_contract` must be a dictionary or OutputContractConfig",
            error_code="CFG-002",
        )
    return OutputContractConfig(**raw)


class AIDEWorkflowFactory(BaseWorkflowFactory):
    def _get_workflow_name(self) -> str:
        return "aide"

    def create_workflow(
        self, config: Any, benchmark: Optional[BaseBenchmark] = None
    ) -> AIDEWorkflow:
        workspace_base = None
        if config.workflow and config.workflow.params:
            workspace_base = config.workflow.params.get("workspace_base_dir")
        workspace = WorkspaceService(run_name=config.run.run_name, base_dir=workspace_base)
        llm_service = LLMService(config=config.llm)
        sandbox_service = _create_sandbox_service(workspace, config)
        state = JournalState()

        operators = {
            "generate": GenerateCodeAndPlanOperator(llm_service=llm_service),
            "execute": ExecuteAndTestOperator(sandbox_service=sandbox_service),
            "review": LLMBasedReviewOperator(llm_service=llm_service),
        }
        services = {
            "llm": llm_service,
            "sandbox": sandbox_service,
            "state": state,
            "workspace": workspace,
        }
        return AIDEWorkflow(
            operators=operators,
            services=services,
            agent_config=config.agent.model_dump(),
            benchmark=benchmark,
        )


class AutoMindWorkflowFactory(BaseWorkflowFactory):
    def _get_workflow_name(self) -> str:
        return "automind"

    def create_workflow(
        self, config: Any, benchmark: Optional[BaseBenchmark] = None
    ) -> AutoMindWorkflow:
        workspace = WorkspaceService(run_name=config.run.run_name)
        llm_service = LLMService(config=config.llm)
        sandbox_service = _create_sandbox_service(workspace, config)

        enable_rag, case_dir = _resolve_rag_settings(config, "automind")
        vdb_service = None
        if enable_rag:
            vdb_service = VDBService(case_dir=case_dir)

        state = JournalState()
        operators = {
            "generate": GenerateCodeAndPlanOperator(llm_service=llm_service),
            "execute": ExecuteAndTestOperator(sandbox_service=sandbox_service),
            "review": LLMBasedReviewOperator(llm_service=llm_service),
            "complexity_scorer": ComplexityScorerOperator(llm_service=llm_service),
            "plan_decomposer": PlanDecomposerOperator(llm_service=llm_service),
        }
        services = {
            "llm": llm_service,
            "sandbox": sandbox_service,
            "vdb": vdb_service,
            "state": state,
            "workspace": workspace,
        }
        return AutoMindWorkflow(
            operators=operators,
            services=services,
            agent_config=config.agent.model_dump(),
            benchmark=benchmark,
        )


class DSAgentWorkflowFactory(BaseWorkflowFactory):
    def _get_workflow_name(self) -> str:
        return "dsagent"

    def create_workflow(
        self, config: Any, benchmark: Optional[BaseBenchmark] = None
    ) -> DSAgentWorkflow:
        workspace = WorkspaceService(run_name=config.run.run_name)
        llm_service = LLMService(config=config.llm)
        sandbox_service = _create_sandbox_service(workspace, config)

        enable_rag, case_dir = _resolve_rag_settings(config, "dsagent")
        vdb_service = None
        if enable_rag:
            vdb_service = VDBService(case_dir=case_dir)

        state = DSAgentState()
        operators = {
            "planner": DevelopPlanOperator(
                llm_service=llm_service,
                vdb_service=vdb_service,
                agent_config=config.agent.model_dump(),
            ),
            "executor": ExecutePlanOperator(
                llm_service=llm_service,
                sandbox_service=sandbox_service,
                agent_config=config.agent.model_dump(),
            ),
            "logger": ReviseLogOperator(llm_service=llm_service),
        }
        services = {
            "llm": llm_service,
            "sandbox": sandbox_service,
            "vdb": vdb_service,
            "state": state,
            "workspace": workspace,
        }
        return DSAgentWorkflow(
            operators=operators,
            services=services,
            agent_config=config.agent.model_dump(),
        )


class DataInterpreterWorkflowFactory(BaseWorkflowFactory):
    def _get_workflow_name(self) -> str:
        return "data_interpreter"

    def create_workflow(
        self, config: Any, benchmark: Optional[BaseBenchmark] = None
    ) -> DataInterpreterWorkflow:
        workspace = WorkspaceService(run_name=config.run.run_name)
        llm_service = LLMService(config=config.llm)
        sandbox_service = _create_sandbox_service(workspace, config)

        operators = {
            "planner": PlanOperator(llm_service=llm_service),
            "generator": GenerateCodeAndPlanOperator(llm_service=llm_service),
            "debugger": GenerateCodeAndPlanOperator(llm_service=llm_service),
            "executor": ExecuteAndTestOperator(sandbox_service=sandbox_service),
        }
        services = {
            "llm": llm_service,
            "sandbox": sandbox_service,
            "workspace": workspace,
        }
        return DataInterpreterWorkflow(
            operators=operators,
            services=services,
            agent_config=config.agent.model_dump(),
        )


class AutoKaggleWorkflowFactory(BaseWorkflowFactory):
    def _get_workflow_name(self) -> str:
        return "autokaggle"

    def create_workflow(
        self, config: Any, benchmark: Optional[BaseBenchmark] = None
    ) -> AutoKaggleWorkflow:
        workspace = WorkspaceService(run_name=config.run.run_name)
        llm_service = LLMService(config=config.llm)
        sandbox_service = _create_sandbox_service(workspace, config)

        services = {
            "llm": llm_service,
            "sandbox": sandbox_service,
            "workspace": workspace,
        }
        return AutoKaggleWorkflow(
            operators={},
            services=services,
            agent_config=config.agent.model_dump(),
        )


class DeepAnalyzeWorkflowFactory(BaseWorkflowFactory):
    def _get_workflow_name(self) -> str:
        return "deepanalyze"

    def create_workflow(
        self,
        config: Any,
        benchmark: Optional[BaseBenchmark] = None,
    ) -> DeepAnalyzeWorkflow:
        workspace = WorkspaceService(run_name=config.run.run_name)
        llm_service = LLMService(config=config.llm)
        sandbox_service = _create_sandbox_service(workspace, config)

        operators = {"execute": ExecuteAndTestOperator(sandbox_service=sandbox_service)}
        services = {
            "llm": llm_service,
            "sandbox": sandbox_service,
            "workspace": workspace,
        }
        return DeepAnalyzeWorkflow(
            operators=operators,
            services=services,
            agent_config=config.agent.model_dump(),
            benchmark=benchmark,
        )


class MyCustomAgentWorkflowFactory(BaseWorkflowFactory):
    def _get_workflow_name(self) -> str:
        return "my_custom_agent"

    def create_workflow(
        self,
        config: Any,
        benchmark: Optional[BaseBenchmark] = None,
    ) -> MyCustomAgentWorkflow:
        workspace = WorkspaceService(run_name=config.run.run_name)
        llm_service = LLMService(config=config.llm)
        sandbox_service = _create_sandbox_service(workspace, config)

        data_perception = create_data_perception_runtime(config)
        state = JournalState()
        operators = {
            "generate": GenerateCodeAndPlanOperator(llm_service=llm_service),
            "execute": ExecuteAndTestOperator(sandbox_service=sandbox_service),
            "review": LLMBasedReviewOperator(llm_service=llm_service),
        }
        services = {
            "llm": llm_service,
            "sandbox": sandbox_service,
            "workspace": workspace,
            "data_perception": data_perception,
            "state": state,
        }
        return MyCustomAgentWorkflow(
            operators=operators,
            services=services,
            agent_config=config.agent.model_dump(),
        )


class AFlowWorkflowFactory(BaseWorkflowFactory):
    def _get_workflow_name(self) -> str:
        return "aflow"

    def create_workflow(
        self, config: Any, benchmark: Optional[BaseBenchmark] = None
    ) -> AFlowWorkflow:
        workspace_base = None
        if config.workflow and config.workflow.params:
            workspace_base = config.workflow.params.get("workspace_base_dir")
        workspace = WorkspaceService(run_name=config.run.run_name, base_dir=workspace_base)
        llm_service = LLMService(config=config.llm)
        sandbox_service = _create_sandbox_service(workspace, config)
        data_perception = create_data_perception_runtime(config)
        services = {
            "llm": llm_service,
            "workspace": workspace,
            "sandbox": sandbox_service,
            "data_perception": data_perception,
        }
        agent_config = config.agent.model_dump()
        if config.optimizer:
            agent_config["optimizer"] = config.optimizer.model_dump()
        return AFlowWorkflow(
            operators={},
            services=services,
            agent_config=agent_config,
            benchmark=benchmark,
        )


class ReActWorkflowFactory(BaseWorkflowFactory):
    def _get_workflow_name(self) -> str:
        return "react"

    def create_workflow(
        self, config: Any, benchmark: Optional[BaseBenchmark] = None
    ) -> ReActWorkflow:
        workspace_base = None
        if config.workflow and config.workflow.params:
            workspace_base = config.workflow.params.get("workspace_base_dir")
        workspace = WorkspaceService(run_name=config.run.run_name, base_dir=workspace_base)
        llm_service = LLMService(config=config.llm)
        sandbox_service = _create_sandbox_service(workspace, config)

        max_steps, obs_max_tokens, obs_head_tokens, obs_tail_tokens, context_config = (
            _resolve_agent_runtime_settings(config)
        )
        output_contract_config = _resolve_output_contract_settings(config)

        from dslighting.ops.presets.react import ReActOperator

        operators = {
            "react": ReActOperator(
                llm_service=llm_service,
                max_steps=max_steps,
                obs_max_tokens=obs_max_tokens,
                obs_head_tokens=obs_head_tokens,
                obs_tail_tokens=obs_tail_tokens,
            ),
            "execute": ExecuteAndTestOperator(sandbox_service=sandbox_service),
        }
        services = {
            "llm": llm_service,
            "sandbox": sandbox_service,
            "workspace": workspace,
            "react_context_config": context_config,
            "output_contract_config": output_contract_config,
        }
        return ReActWorkflow(
            operators=operators,
            services=services,
            agent_config=config.agent.model_dump(),
            benchmark=benchmark,
        )


class DynamicWorkflowFactory(BaseWorkflowFactory):
    """Factory that instantiates a workflow class from a code string."""

    def __init__(
        self,
        code_string: str,
        operator_classes: Optional[Dict[str, Type["Operator"]]] = None,
    ):
        self.code_string = code_string
        self.operator_classes = operator_classes
        self.keep_workspace = True
        try:
            self.workflow_class = import_workflow_from_string(self.code_string)
        except DynamicImportError as e:
            raise ValueError(
                "Failed to dynamically import 'Workflow' class from the provided code string."
            ) from e

    def _get_workflow_name(self) -> str:
        return "dynamic"

    def create_agent(self, **kwargs: Any) -> BaseWorkflow:
        raise NotImplementedError(
            "DynamicWorkflowFactory is runner-only and does not support create_agent()."
        )

    def create_workflow(
        self, config: Any, benchmark: Optional[BaseBenchmark] = None
    ) -> BaseWorkflow:
        workspace = WorkspaceService(run_name=config.run.run_name)
        llm_service = LLMService(config=config.llm)
        sandbox_service = _create_sandbox_service(workspace, config)
        services = {
            "llm": llm_service,
            "sandbox": sandbox_service,
            "workspace": workspace,
        }
        operators = self._build_operator_instances(
            llm_service=llm_service,
            sandbox_service=sandbox_service,
            workspace=workspace,
        )
        return self.workflow_class(
            operators=operators,
            services=services,
            agent_config=config.agent.model_dump(),
        )

    def _build_operator_instances(
        self,
        llm_service: LLMService,
        sandbox_service: SandboxService,
        workspace: WorkspaceService,
    ) -> Dict[str, Any]:
        if not self.operator_classes:
            return {
                "ScEnsemble": ScEnsembleOperator(llm_service=llm_service),
                "Review": AFlowReviewOperator(llm_service=llm_service),
                "Revise": AFlowReviseOperator(llm_service=llm_service),
            }

        operators: Dict[str, Any] = {}
        for name, cls in self.operator_classes.items():
            operators[name] = self._instantiate_operator(
                cls=cls,
                llm_service=llm_service,
                sandbox_service=sandbox_service,
                workspace=workspace,
                operators=operators,
            )
        return operators

    @staticmethod
    def _instantiate_operator(
        cls: Type["Operator"],
        llm_service: LLMService,
        sandbox_service: SandboxService,
        workspace: WorkspaceService,
        operators: Dict[str, Any],
    ) -> Any:
        params = inspect.signature(cls.__init__).parameters
        kwargs: Dict[str, Any] = {}
        if "llm_service" in params:
            kwargs["llm_service"] = llm_service
        if "sandbox_service" in params:
            kwargs["sandbox_service"] = sandbox_service
        if "workspace" in params:
            kwargs["workspace"] = workspace
        if "operators" in params:
            kwargs["operators"] = operators
        return cls(**kwargs)  # type: ignore[arg-type]
