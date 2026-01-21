# dsat/workflows/factory.py

from abc import ABC, abstractmethod
import inspect
import logging
from typing import Dict, Any, Optional, Type

# --- Core configuration and interface imports ---
from dsat.config import DSATConfig
from dsat.workflows.base import DSATWorkflow
from dsat.benchmark.benchmark import BaseBenchmark

# --- Services imports ---
from dsat.services.workspace import WorkspaceService
from dsat.services.llm import LLMService
from dsat.services.sandbox import SandboxService
from dsat.services.vdb import VDBService

# --- State management imports ---
from dsat.services.states.journal import JournalState
from dsat.services.states.dsa_log import DSAgentState

# --- Operators imports ---
# General operators
from dsat.operators.llm_basic import GenerateCodeAndPlanOperator, ReviewOperator, PlanOperator
from dsat.operators.code import ExecuteAndTestOperator
# AutoMind specific operators
from dsat.operators.automind_ops import ComplexityScorerOperator, PlanDecomposerOperator
# DS-Agent specific operators
from dsat.operators.dsagent_ops import DevelopPlanOperator, ExecutePlanOperator, ReviseLogOperator
# AutoKaggle specific operators
from dsat.operators.autokaggle_ops import *  # Import all new operators

from dsat.operators.aflow_ops import ScEnsembleOperator, ReviewOperator as AFlowReviewOperator, ReviseOperator as AFlowReviseOperator
from dsat.utils.dynamic_import import import_workflow_from_string
from dsat.common.exceptions import DynamicImportError


# --- Concrete workflow imports ---
from dsat.workflows.search.automind_workflow import AutoMindWorkflow
from dsat.workflows.search.aide_workflow import AIDEWorkflow
from dsat.workflows.search.aflow_workflow import AFlowWorkflow
from dsat.workflows.manual.deepanalyze_workflow import DeepAnalyzeWorkflow
from dsat.workflows.manual.dsagent_workflow import DSAgentWorkflow
from dsat.workflows.manual.data_interpreter_workflow import DataInterpreterWorkflow
from dsat.workflows.manual.autokaggle_workflow import AutoKaggleWorkflow
from dsat.workflows.manual.my_custom_agent_workflow import MyCustomAgentWorkflow

logger = logging.getLogger(__name__)


class WorkflowFactory(ABC):
    """
    Abstract base class for workflow factories.
    
    Defines a unified interface for creating workflow instances based on configuration.
    This follows the factory pattern, separating object creation logic from usage.
    """
    @abstractmethod
    def create_workflow(self, config: DSATConfig, benchmark: Optional[BaseBenchmark] = None) -> DSATWorkflow:
        """
        Create and return a configured workflow instance based on the provided configuration.

        Args:
            config: Complete DSATConfig object containing all runtime parameters.

        Returns:
            A fully initialized DSATWorkflow instance ready to execute solve() method.
        """
        raise NotImplementedError


# ==============================================================================
# ==                            AIDE WORKFLOW FACTORY                           ==
# ==============================================================================
class AIDEWorkflowFactory(WorkflowFactory):
    """A specialized factory for creating and assembling AIDEWorkflow."""
    def create_workflow(self, config: DSATConfig, benchmark: Optional[BaseBenchmark] = None) -> AIDEWorkflow:
        logger.info("AIDEWorkflowFactory: Assembling AIDE workflow...")

        workspace_base = None
        if config.workflow and config.workflow.params:
            workspace_base = config.workflow.params.get("workspace_base_dir")
        workspace = WorkspaceService(run_name=config.run.name, base_dir=workspace_base)
        llm_service = LLMService(config=config.llm)
        sandbox_service = SandboxService(workspace=workspace, timeout=config.sandbox.timeout)
        state = JournalState()

        operators = {
            "generate": GenerateCodeAndPlanOperator(llm_service=llm_service),
            "execute": ExecuteAndTestOperator(sandbox_service=sandbox_service),
            "review": ReviewOperator(llm_service=llm_service),
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
    def create_workflow(self, config: DSATConfig, benchmark: Optional[BaseBenchmark] = None) -> AutoMindWorkflow:
        """
        Build a fully functional AutoMindWorkflow instance.
        """
        logger.info("AutoMindWorkflowFactory: Assembling AutoMind workflow...")

        # 1. Instantiate all base services required by this workflow
        logger.debug("Instantiating services...")
        workspace = WorkspaceService(run_name=config.run.name)
        llm_service = LLMService(config=config.llm)
        sandbox_service = SandboxService(workspace=workspace, timeout=config.sandbox.timeout)

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
            "review": ReviewOperator(llm_service=llm_service),
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
    def create_workflow(self, config: DSATConfig, benchmark: Optional[BaseBenchmark] = None) -> DSAgentWorkflow:
        logger.info("DSAgentWorkflowFactory: Assembling DS-Agent workflow...")

        workspace = WorkspaceService(run_name=config.run.name)
        llm_service = LLMService(config=config.llm)
        sandbox_service = SandboxService(workspace=workspace, timeout=config.sandbox.timeout)

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
    def create_workflow(self, config: DSATConfig, benchmark: Optional[BaseBenchmark] = None) -> DataInterpreterWorkflow:
        logger.info("DataInterpreterWorkflowFactory: Assembling Data Interpreter workflow...")

        workspace = WorkspaceService(run_name=config.run.name)
        llm_service = LLMService(config=config.llm)
        sandbox_service = SandboxService(workspace=workspace, timeout=config.sandbox.timeout)

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
    def create_workflow(self, config: DSATConfig, benchmark: Optional[BaseBenchmark] = None) -> AutoKaggleWorkflow:
        logger.info("AutoKaggleWorkflowFactory: Assembling AutoKaggle SOP workflow...")

        workspace = WorkspaceService(run_name=config.run.name)
        llm_service = LLMService(config=config.llm)
        sandbox_service = SandboxService(workspace=workspace, timeout=config.sandbox.timeout)
        
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
        config: DSATConfig,
        benchmark: Optional[BaseBenchmark] = None,
    ) -> DeepAnalyzeWorkflow:
        logger.info("DeepAnalyzeWorkflowFactory: Assembling DeepAnalyze workflow...")

        workspace = WorkspaceService(run_name=config.run.name)
        llm_service = LLMService(config=config.llm)
        sandbox_service = SandboxService(workspace=workspace, timeout=config.sandbox.timeout)

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

    这是一个示例 Factory，展示如何创建自定义 Agent 的工厂类。
    """
    def create_workflow(self, config: DSATConfig, benchmark: Optional[BaseBenchmark] = None) -> MyCustomAgentWorkflow:
        logger.info("MyCustomAgentWorkflowFactory: Assembling MyCustomAgent workflow...")

        workspace = WorkspaceService(run_name=config.run.name)
        llm_service = LLMService(config=config.llm)
        sandbox_service = SandboxService(workspace=workspace, timeout=config.sandbox.timeout)
        data_analyzer = DataAnalyzer()
        state = JournalState()

        operators = {
            "generate": GenerateCodeAndPlanOperator(llm_service=llm_service),
            "execute": ExecuteAndTestOperator(sandbox_service=sandbox_service),
            "review": ReviewOperator(llm_service=llm_service),
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
    def create_workflow(self, config: DSATConfig, benchmark: Optional[BaseBenchmark] = None) -> AFlowWorkflow:
        logger.info("AFlowWorkflowFactory: Assembling AFlow workflow...")

        workspace_base = None
        if config.workflow and config.workflow.params:
            workspace_base = config.workflow.params.get("workspace_base_dir")
        workspace = WorkspaceService(run_name=config.run.name, base_dir=workspace_base)
        llm_service = LLMService(config=config.llm)
        # Add SandboxService for code execution capabilities
        sandbox_service = SandboxService(workspace=workspace, timeout=config.sandbox.timeout)
        
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

    def create_workflow(self, config: DSATConfig, benchmark: Optional[BaseBenchmark] = None) -> DSATWorkflow:
        logger.info(f"DynamicWorkflowFactory: Instantiating workflow from code string...")
        
        workspace = WorkspaceService(run_name=config.run.name)
        llm_service = LLMService(config=config.llm)
        sandbox_service = SandboxService(workspace=workspace, timeout=config.sandbox.timeout)

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
