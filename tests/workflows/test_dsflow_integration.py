from pathlib import Path
from types import SimpleNamespace

import pytest

from dslighting.config import DSFlowConfig
from dslighting.core import ConfigBuilder
from dslighting.core.application.agent_config_builder import AgentConfigBuilder
from dslighting.ops.base import Operator
from dslighting.ops.presets.dsflow import DSDataInspectOperator, ExecutePythonOperator
from dslighting.runner import DSLightingRunner
from dslighting.tools.dsflow.core.evaluation_helpers import EvaluationHelpers
from dslighting.tools.dsflow.operators import fix_operator_imports
from dslighting.utils.dynamic_import import import_workflow_from_string
from dslighting.workflows.factory.builtin import DynamicWorkflowFactory
from dslighting.workflows.factory.registry import default_workflow_registry
from dslighting.workflows.templates.dsflow import get_initial_dsflow_workflow_code


def _agent_config_builder(**init_kwargs):
    return AgentConfigBuilder(
        workflow_name="dsflow",
        model="gpt-4o-mini",
        api_key="test-key",
        api_keys=None,
        api_base="https://example.invalid/v1",
        provider=None,
        temperature=0.0,
        timeout=30,
        keep_workspace=True,
        sandbox_backend=None,
        sandbox_backend_type=None,
        sandbox_timeout=None,
        sandbox_api_key=None,
        init_kwargs=init_kwargs,
    )


def test_dsflow_is_registered_with_expected_defaults() -> None:
    assert "dsflow" in default_workflow_registry.list_workflows()
    assert default_workflow_registry.resolve("dsflow")._get_workflow_name() == "dsflow"
    config = DSFlowConfig()
    assert config.max_rounds == 4
    assert config.top_k_selection == 2
    assert config.coarse_capture == "code"
    assert config.best_workflow_path is None


def test_agent_builder_maps_dsflow_namespace_to_typed_config() -> None:
    config = _agent_config_builder(dsflow={"max_rounds": 2, "task_sample_size": 1}).build(
        task_id="demo", run_kwargs={}
    )

    assert config.workflow.name == "dsflow"
    assert config.dsflow.max_rounds == 2
    assert config.dsflow.task_sample_size == 1
    assert "dsflow" not in config.run.parameters


def test_config_builder_maps_dsflow_namespace_to_typed_config() -> None:
    config = ConfigBuilder().build_config(
        workflow="dsflow",
        model="gpt-4o-mini",
        api_key="test-key",
        dsflow={"max_rounds": 2, "best_workflow_path": "/tmp/best.py"},
    )

    assert config.dsflow.max_rounds == 2
    assert config.dsflow.best_workflow_path == "/tmp/best.py"


def test_dsflow_factory_creates_optimizer_with_builtin_operators(tmp_path: Path) -> None:
    config = ConfigBuilder().build_config(
        workflow="dsflow",
        model="gpt-4o-mini",
        api_key="test-key",
        workspace_dir=str(tmp_path),
        run_name="dsflow-factory-test",
        dsflow={"operator_library_path": str(tmp_path / "operators.json")},
    )

    optimizer = default_workflow_registry.resolve("dsflow").create_workflow(config)

    operator_names = set(optimizer.export_operator_classes())
    assert {"DSDataInspect", "DSCodeGen", "ExecutePython"} <= operator_names
    assert optimizer.workspace.get_path("run_dir").is_dir()

    optimizer.experience.set("probe", {"score": 1.0})
    snapshot = optimizer.experience.snapshot()
    optimizer.experience.clear()
    assert optimizer.experience.restore(snapshot)
    assert optimizer.experience.get("probe") == {"score": 1.0}


@pytest.mark.asyncio
async def test_runner_loads_saved_dsflow_without_meta_optimization(tmp_path: Path) -> None:
    workflow_path = tmp_path / "best_workflow.py"
    workflow_path.write_text(get_initial_dsflow_workflow_code(), encoding="utf-8")
    config = ConfigBuilder().build_config(
        workflow="dsflow",
        model="gpt-4o-mini",
        api_key="test-key",
        workspace_dir=str(tmp_path),
        run_name="dsflow-saved-test",
        dsflow={
            "best_workflow_path": str(workflow_path),
            "operator_library_path": str(tmp_path / "operators.json"),
        },
    )

    class Benchmark:
        mode = None

        def set_mode(self, mode: str) -> None:
            self.mode = mode

    benchmark = Benchmark()
    runner = DSLightingRunner(config)
    runner.benchmark = benchmark

    workflow, _llm, _sandbox, _workspace = await runner._create_workflow_instance(config)

    assert workflow.__class__.__name__ == "Workflow"
    assert benchmark.mode == "test"


def test_dsflow_seed_is_a_valid_dynamic_workflow() -> None:
    workflow_class = import_workflow_from_string(get_initial_dsflow_workflow_code())
    assert workflow_class.__name__ == "Workflow"


def test_dsflow_sanitizes_standalone_saved_workflow() -> None:
    legacy_code = """
from dsat.workflows.base import DSATWorkflow

class Workflow(DSATWorkflow):
    pass
"""
    sanitized = EvaluationHelpers._sanitize_workflow_code(legacy_code)

    assert "dsat" not in sanitized
    assert "class Workflow(BaseWorkflow)" in sanitized
    assert import_workflow_from_string(sanitized).__name__ == "Workflow"


def test_standalone_operator_sandbox_call_is_migrated_to_async() -> None:
    legacy_code = """
from dsat.operators.base import Operator

class ExecuteSafe(Operator):
    async def __call__(self, code):
        return self._sandbox.run_script(code)
"""
    migrated = fix_operator_imports(legacy_code)

    assert "from dslighting.ops.base import Operator" in migrated
    assert "return await self._sandbox.run_script(code)" in migrated


@pytest.mark.asyncio
async def test_data_inspect_uses_injected_data_perception(tmp_path: Path) -> None:
    class FakeWorkspace:
        def get_path(self, name: str) -> Path:
            assert name == "sandbox_workdir"
            return tmp_path

    class FakePerception:
        def analyze_data(self, data_dir: Path, task_type: str) -> str:
            assert data_dir == tmp_path
            assert task_type == "kaggle"
            return "## Data Schema Analysis\ncolumn: int64\n\n## Other\nignored"

    operator = DSDataInspectOperator(
        sandbox_service=SimpleNamespace(workspace=FakeWorkspace()),
        data_perception=FakePerception(),
    )

    assert await operator() == "## Data Schema Analysis\ncolumn: int64"


@pytest.mark.asyncio
async def test_execute_python_awaits_async_sandbox() -> None:
    sentinel = object()

    class FakeSandbox:
        async def run_script(self, code: str):
            assert code == "print('ok')"
            return sentinel

    operator = ExecutePythonOperator(sandbox_service=FakeSandbox())

    assert await operator("print('ok')") is sentinel


@pytest.mark.asyncio
async def test_fine_grading_awaits_dslighting_benchmark(tmp_path: Path) -> None:
    submission = tmp_path / "submission.csv"
    submission.write_text("id,target\n1,0\n", encoding="utf-8")

    class Benchmark:
        async def grade(self, path: Path, competition_id: str) -> float:
            assert path == submission
            assert competition_id == "competition"
            return 0.75

    helper = SimpleNamespace(benchmark=Benchmark())
    score = await EvaluationHelpers._grade_submission(
        helper,
        submission,
        "competition",
    )
    assert score == 0.75


def test_dynamic_factory_injects_data_perception_into_operator() -> None:
    sentinel = object()

    class NeedsPerception(Operator):
        def __init__(self, data_perception):
            super().__init__()
            self.data_perception = data_perception

        async def __call__(self):
            return None

    operator = DynamicWorkflowFactory._instantiate_operator(
        cls=NeedsPerception,
        llm_service=object(),
        sandbox_service=object(),
        workspace=object(),
        operators={},
        data_perception=sentinel,
    )
    assert operator.data_perception is sentinel
