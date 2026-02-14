
from abc import ABC, abstractmethod
import inspect
import logging
from typing import Dict, Any, Optional, Type

# --- Core configuration and interface imports ---
from dslighting.workflows.base import BaseWorkflow
from dslighting.benchmark.core.base import BaseBenchmark

# --- Services imports ---
from dslighting.services.workspace import WorkspaceService
from dslighting.services.llm import LLMService
from dslighting.services.sandbox import SandboxService
from dslighting.services.vdb import VDBService

# --- State management imports ---
from dslighting.state.search.journal import JournalState
from dslighting.state.dsagent import DSAgentState

# --- Operators imports ---
# General operators
from dslighting.ops.llm.basic import GenerateCodeAndPlanOperator, LLMBasedReviewOperator, PlanOperator
from dslighting.ops.code import ExecuteAndTestOperator
# AutoMind specific operators
from dslighting.ops.presets.automind import ComplexityScorerOperator, PlanDecomposerOperator
# DS-Agent specific operators
from dslighting.ops.presets.dsagent import DevelopPlanOperator, ExecutePlanOperator, ReviseLogOperator
# AutoKaggle specific operators
from dslighting.ops.presets.autokaggle import *  # Import all new operators

from dslighting.ops.presets import ScEnsembleOperator, AFlowReviewOperator, AFlowReviseOperator
from dslighting.utils.dynamic_import import import_workflow_from_string
from dslighting.error import DynamicImportError


# --- Concrete workflow imports ---
from dslighting.workflows.search.automind_workflow import AutoMindWorkflow
from dslighting.workflows.search.aide_workflow import AIDEWorkflow
from dslighting.workflows.search.aflow_workflow import AFlowWorkflow
from dslighting.workflows.manual.deepanalyze_workflow import DeepAnalyzeWorkflow
from dslighting.workflows.manual.dsagent_workflow import DSAgentWorkflow
from dslighting.workflows.manual.data_interpreter_workflow import DataInterpreterWorkflow
from dslighting.workflows.manual.autokaggle_workflow import AutoKaggleWorkflow
from dslighting.workflows.manual.my_custom_agent_workflow import MyCustomAgentWorkflow

logger = logging.getLogger(__name__)


def _resolve_sandbox_env(config: Any) -> Optional[Dict[str, str]]:
    parameters = getattr(config.run, "parameters", None) or {}
    sandbox_env = parameters.get("sandbox_env")
    if not isinstance(sandbox_env, dict):
        return None
    return {
        str(key): str(value)
        for key, value in sandbox_env.items()
        if value is not None
    }


def _create_sandbox_service(workspace: WorkspaceService, config: Any) -> SandboxService:
    # Get sandbox backend configuration
    backend_type = getattr(config.sandbox, "backend", "local")
    backend_type_option = getattr(config.sandbox, "backend_type", "docker")
    api_key = getattr(config.sandbox, "api_key", None)

    # Import backend classes
    from dslighting.services.sandbox_backends.backends.base import SandboxBackendConfig
    from dslighting.services.sandbox_backends.backends.local import LocalSandboxBackend

    # Create backend configuration
    backend_config = SandboxBackendConfig(
        timeout=config.sandbox.timeout,
    )

    # Select and create the appropriate backend
    if backend_type == "e2b":
        from dslighting.services.sandbox_backends.backends.e2b import E2BSandboxBackend
        backend = E2BSandboxBackend(
            config=backend_config,
            api_key=api_key,
        )
    elif backend_type == "ds_sandbox":
        from dslighting.services.sandbox_backends.backends.ds_sandbox import DSSandboxBackend
        backend = DSSandboxBackend(
            config=backend_config,
            backend_type=backend_type_option,
        )
    else:
        # Default to local backend
        # Note: workspace_path will be provided by SandboxService at execution time
        backend = LocalSandboxBackend(
            config=backend_config,
            env_overrides=_resolve_sandbox_env(config),
        )

    return SandboxService(
        workspace=workspace,
        backend=backend,
        timeout=config.sandbox.timeout,
        env_overrides=_resolve_sandbox_env(config),
    )


class WorkflowFactory(ABC):
    """
    Abstract base class for workflow factories.
    
    Defines a unified interface for creating workflow instances based on configuration.
    This follows the factory pattern, separating object creation logic from usage.
    """
    @abstractmethod
    def create_workflow(self, config: Any, benchmark: Optional[BaseBenchmark] = None) -> BaseWorkflow:
        """
        Create and return a configured workflow instance based on the provided configuration.

        Args:
            config: Complete workflow configuration object containing all runtime parameters.

        Returns:
            A fully initialized workflow instance ready to execute solve() method.
        """
        raise NotImplementedError


# ==============================================================================
# ==                            AIDE WORKFLOW FACTORY                           ==
# ==============================================================================
class AIDEWorkflowFactory(WorkflowFactory):
    """A specialized factory for creating and assembling AIDEWorkflow."""
    def create_workflow(self, config: Any, benchmark: Optional[BaseBenchmark] = None) -> AIDEWorkflow:
        logger.info("AIDEWorkflowFactory: Assembling AIDE workflow...")

        workspace_base = None
        if config.workflow and config.workflow.params:
            workspace_base = config.workflow.params.get("workspace_base_dir")
        workspace = WorkspaceService(run_name=config.run.name, base_dir=workspace_base)
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

        workflow = AIDEWorkflow(
            operators=operators,
            services=services,
            agent_config=config.agent.model_dump(),
            benchmark=benchmark
        )

        logger.info("AIDE workflow assembled successfully.")
        return workflow


# ==============================================================================
# ==                          AUTOMIND WORKFLOW FACTORY                         ==
# ==============================================================================
class AutoMindWorkflowFactory(WorkflowFactory):
    """
    A specialized factory for creating and assembling AutoMindWorkflow.

    This class encapsulates all the complexity required to create AutoMindWorkflow,
    including instantiating its dependent services, state managers and operators.
    """
    def create_workflow(self, config: Any, benchmark: Optional[BaseBenchmark] = None) -> AutoMindWorkflow:
        """
        Build a fully functional AutoMindWorkflow instance.
        """
        logger.info("AutoMindWorkflowFactory: Assembling AutoMind workflow...")

        # 1. Instantiate all base services required by this workflow
        logger.debug("Instantiating services...")
        workspace = WorkspaceService(run_name=config.run.name)
        llm_service = LLMService(config=config.llm)
        sandbox_service = _create_sandbox_service(workspace, config)

        # VDBService (RAG) is optional - can be disabled via enable_rag parameter
        enable_rag = config.workflow.params.get('enable_rag', True)
        vdb_service = None
        if enable_rag:
            case_dir = config.workflow.params.get('case_dir', 'experience_replay')
            vdb_service = VDBService(case_dir=case_dir)
            logger.info(f"RAG enabled: Using knowledge base from {case_dir}")
        else:
            logger.info("RAG disabled: Running without knowledge base retrieval")

        state = JournalState()
        
        # 2. Instantiate all operators required by this workflow, injecting their service dependencies
        logger.debug("Instantiating operators...")
        operators = {
            "generate": GenerateCodeAndPlanOperator(llm_service=llm_service),
            "execute": ExecuteAndTestOperator(sandbox_service=sandbox_service),
            "review": LLMBasedReviewOperator(llm_service=llm_service),
            "complexity_scorer": ComplexityScorerOperator(llm_service=llm_service),
            "plan_decomposer": PlanDecomposerOperator(llm_service=llm_service),
        }

        # 3. Package all services for injection
        services = {
            "llm": llm_service,
            "sandbox": sandbox_service,
            "vdb": vdb_service,
            "state": state,
            "workspace": workspace, # Also optionally inject workspace
        }

        logger.debug("Instantiating AutoMindWorkflow with dependencies...")
        workflow = AutoMindWorkflow(
            operators=operators,
            services=services,
            agent_config=config.agent.model_dump(),
            benchmark=benchmark
        )

        logger.info("AutoMind workflow assembled successfully.")
        return workflow


# ==============================================================================
# ==                          DS-AGENT WORKFLOW FACTORY                         ==
# ==============================================================================
class DSAgentWorkflowFactory(WorkflowFactory):
    """A specialized factory for creating and assembling DSAgentWorkflow."""
    def create_workflow(self, config: Any, benchmark: Optional[BaseBenchmark] = None) -> DSAgentWorkflow:
        logger.info("DSAgentWorkflowFactory: Assembling DS-Agent workflow...")

        workspace = WorkspaceService(run_name=config.run.name)
        llm_service = LLMService(config=config.llm)
        sandbox_service = _create_sandbox_service(workspace, config)

        # VDBService (RAG) is optional - can be disabled via enable_rag parameter
        enable_rag = config.workflow.params.get('enable_rag', True)
        vdb_service = None
        if enable_rag:
            case_dir = config.workflow.params.get('case_dir', 'experience_replay')
            vdb_service = VDBService(case_dir=case_dir)
            logger.info(f"RAG enabled: Using knowledge base from {case_dir}")
        else:
            logger.info("RAG disabled: Running without knowledge base retrieval")

        state = DSAgentState()

        operators = {
            "planner": DevelopPlanOperator(llm_service=llm_service, vdb_service=vdb_service),
            "executor": ExecutePlanOperator(llm_service=llm_service, sandbox_service=sandbox_service),
            "logger": ReviseLogOperator(llm_service=llm_service),
        }
        
        services = {
            "llm": llm_service,
            "sandbox": sandbox_service,
            "vdb": vdb_service,
            "state": state,
            "workspace": workspace,
        }
        
        workflow = DSAgentWorkflow(
            operators=operators,
            services=services,
            agent_config=config.agent.model_dump()
        )

        logger.info("DS-Agent workflow assembled successfully.")
        return workflow


# ==============================================================================
# ==                      DATA INTERPRETER WORKFLOW FACTORY                     ==
# ==============================================================================
class DataInterpreterWorkflowFactory(WorkflowFactory):
    """A specialized factory for creating and assembling DataInterpreterWorkflow."""
    def create_workflow(self, config: Any, benchmark: Optional[BaseBenchmark] = None) -> DataInterpreterWorkflow:
        logger.info("DataInterpreterWorkflowFactory: Assembling Data Interpreter workflow...")

        workspace = WorkspaceService(run_name=config.run.name)
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

        workflow = DataInterpreterWorkflow(
            operators=operators,
            services=services,
            agent_config=config.agent.model_dump()
        )

        logger.info("Data Interpreter workflow assembled successfully.")
        return workflow


# ==============================================================================
# ==                      AUTOKAGGLE SOP WORKFLOW FACTORY                     ==
# ==============================================================================
class AutoKaggleWorkflowFactory(WorkflowFactory):
    """A specialized factory for creating and assembling the dynamic AutoKaggleWorkflow."""
    def create_workflow(self, config: Any, benchmark: Optional[BaseBenchmark] = None) -> AutoKaggleWorkflow:
        logger.info("AutoKaggleWorkflowFactory: Assembling AutoKaggle SOP workflow...")

        workspace = WorkspaceService(run_name=config.run.name)
        llm_service = LLMService(config=config.llm)
        sandbox_service = _create_sandbox_service(workspace, config)
        
        services = {
            "llm": llm_service,
            "sandbox": sandbox_service,
            "workspace": workspace,
        }

        # The workflow now instantiates its own operators, so we pass an empty dict
        workflow = AutoKaggleWorkflow(
            operators={}, 
            services=services,
            agent_config=config.agent.model_dump()
        )

        logger.info("AutoKaggle SOP workflow assembled successfully.")
        return workflow


# ==============================================================================
# ==                      DEEPANALYZE WORKFLOW FACTORY                         ==
# ==============================================================================
class DeepAnalyzeWorkflowFactory(WorkflowFactory):
    """Factory for assembling DeepAnalyzeWorkflow."""

    def create_workflow(
        self,
        config: Any,
        benchmark: Optional[BaseBenchmark] = None,
    ) -> DeepAnalyzeWorkflow:
        logger.info("DeepAnalyzeWorkflowFactory: Assembling DeepAnalyze workflow...")

        workspace = WorkspaceService(run_name=config.run.name)
        llm_service = LLMService(config=config.llm)
        sandbox_service = _create_sandbox_service(workspace, config)

        operators = {
            "execute": ExecuteAndTestOperator(sandbox_service=sandbox_service),
        }

        services = {
            "llm": llm_service,
            "sandbox": sandbox_service,
            "workspace": workspace,
        }

        workflow = DeepAnalyzeWorkflow(
            operators=operators,
            services=services,
            agent_config=config.agent.model_dump(),
            benchmark=benchmark,
        )

        logger.info("DeepAnalyze workflow assembled successfully.")
        return workflow


# ==============================================================================
# ==                      MY CUSTOM AGENT WORKFLOW FACTORY                      ==
# ==============================================================================
class MyCustomAgentWorkflowFactory(WorkflowFactory):
    """
    Factory for MyCustomAgentWorkflow.

    This is an example factory demonstrating how to create a custom Agent factory class.
    """
    def create_workflow(self, config: Any, benchmark: Optional[BaseBenchmark] = None) -> MyCustomAgentWorkflow:
        logger.info("MyCustomAgentWorkflowFactory: Assembling MyCustomAgent workflow...")

        workspace = WorkspaceService(run_name=config.run.name)
        llm_service = LLMService(config=config.llm)
        sandbox_service = _create_sandbox_service(workspace, config)
        # Lazy import to avoid unnecessary dependency
        from dslighting.services.data_analyzer import DataAnalyzer
        data_analyzer = DataAnalyzer()
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
            "data_analyzer": data_analyzer,
            "state": state,
        }

        workflow = MyCustomAgentWorkflow(
            operators=operators,
            services=services,
            agent_config=config.agent.model_dump()
        )

        logger.info("MyCustomAgent workflow assembled successfully.")
        return workflow


# ==============================================================================
# ==                            AFLOW WORKFLOW FACTORY                          ==
# ==============================================================================
class AFlowWorkflowFactory(WorkflowFactory):
    """A specialized factory for creating and assembling AFlowWorkflow."""
    def create_workflow(self, config: Any, benchmark: Optional[BaseBenchmark] = None) -> AFlowWorkflow:
        logger.info("AFlowWorkflowFactory: Assembling AFlow workflow...")

        workspace_base = None
        if config.workflow and config.workflow.params:
            workspace_base = config.workflow.params.get("workspace_base_dir")
        workspace = WorkspaceService(run_name=config.run.name, base_dir=workspace_base)
        llm_service = LLMService(config=config.llm)
        # Add SandboxService for code execution capabilities
        sandbox_service = _create_sandbox_service(workspace, config)
        
        services = {
            "llm": llm_service,
            "workspace": workspace,
            "sandbox": sandbox_service,
        }

        agent_config = config.agent.model_dump()
        if config.optimizer:
            agent_config["optimizer"] = config.optimizer.model_dump()

        workflow = AFlowWorkflow(
            operators={},  # AFlow creates its own operators
            services=services,
            agent_config=agent_config,
            benchmark=benchmark,  # Pass the benchmark instance
        )

        logger.info("AFlow workflow assembled successfully.")
        return workflow


class DynamicWorkflowFactory(WorkflowFactory):
    """
    A factory that creates a workflow instance from a Python code string at runtime.
    This is used by the AFLOW paradigm to evaluate its discovered "best" workflow.
    """
    def __init__(
        self,
        code_string: str,
        operator_classes: Optional[Dict[str, Type["Operator"]]] = None,
    ):
        self.code_string = code_string
        self.operator_classes = operator_classes
        try:
            self.workflow_class = import_workflow_from_string(self.code_string)
        except DynamicImportError as e:
            raise ValueError("Failed to dynamically import 'Workflow' class from the provided code string.") from e

    def create_workflow(self, config: Any, benchmark: Optional[BaseBenchmark] = None) -> BaseWorkflow:
        logger.info(f"DynamicWorkflowFactory: Instantiating workflow from code string...")
        
        workspace = WorkspaceService(run_name=config.run.name)
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
        
        # Instantiate the dynamically imported class
        workflow_instance = self.workflow_class(
            operators=operators,
            services=services,
            agent_config=config.agent.model_dump()
        )
        logger.info("Dynamically-loaded workflow instantiated successfully.")
        return workflow_instance

    def _build_operator_instances(
        self,
        llm_service: LLMService,
        sandbox_service: SandboxService,
        workspace: WorkspaceService,
    ) -> Dict[str, Any]:
        """
        Build operator instances for a dynamically imported workflow.

        - Default: provide AFLOW operators (backwards compatible).
        - Override: callers may pass `operator_classes` to inject a custom toolbox.
        """
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
