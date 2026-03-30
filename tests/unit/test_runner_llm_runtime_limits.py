from __future__ import annotations

import sys
import types
import weakref

import pytest

from dslighting.config import DSLightingConfig, WorkflowConfig
from dslighting.error import ConfigurationError
from dslighting.runtime.dag.types import DagRuntimeOptions
from dslighting.services.llm.service import LLMService


@pytest.fixture(autouse=True)
def _reset_llm_service_concurrency_state():
    LLMService._global_limit = None
    LLMService._model_limits = {}
    LLMService._global_semaphores = weakref.WeakKeyDictionary()
    LLMService._model_semaphores = weakref.WeakKeyDictionary()
    yield
    LLMService._global_limit = None
    LLMService._model_limits = {}
    LLMService._global_semaphores = weakref.WeakKeyDictionary()
    LLMService._model_semaphores = weakref.WeakKeyDictionary()


def _stub_runner_optional_dependencies() -> None:
    sys.modules.setdefault("nbformat", types.ModuleType("nbformat"))

    nbclient_module = sys.modules.setdefault("nbclient", types.ModuleType("nbclient"))
    if not hasattr(nbclient_module, "NotebookClient"):
        nbclient_module.NotebookClient = object

    torch_module = sys.modules.setdefault("torch", types.ModuleType("torch"))
    if not hasattr(torch_module, "device"):
        torch_module.device = lambda *args, **kwargs: "cpu"
    if not hasattr(torch_module, "cuda"):
        torch_module.cuda = types.SimpleNamespace(is_available=lambda: False)
    if not hasattr(torch_module, "Tensor"):
        torch_module.Tensor = object

    transformers_module = sys.modules.setdefault(
        "transformers",
        types.ModuleType("transformers"),
    )
    if not hasattr(transformers_module, "AutoModel"):
        transformers_module.AutoModel = object
    if not hasattr(transformers_module, "AutoTokenizer"):
        transformers_module.AutoTokenizer = object

    exceptions_module = sys.modules.setdefault(
        "nbclient.exceptions",
        types.ModuleType("nbclient.exceptions"),
    )
    for name in ("CellExecutionError", "CellTimeoutError", "DeadKernelError"):
        if not hasattr(exceptions_module, name):
            setattr(exceptions_module, name, RuntimeError)


def _build_runner():
    _stub_runner_optional_dependencies()
    from dslighting.runner import DSLightingRunner

    return DSLightingRunner(
        DSLightingConfig(workflow=WorkflowConfig(name="aide", params={}))
    )


def test_runner_freezes_llm_runtime_limits_for_same_signature() -> None:
    runner = _build_runner()
    config = DSLightingConfig(workflow=WorkflowConfig(name="aide", params={}))
    dag_options = DagRuntimeOptions(
        llm_global_max_concurrency=4,
        llm_model_quotas={"gpt-4o": 2},
    )

    runner._configure_llm_runtime_limits(
        task_id="task-a",
        task_config=config,
        dag_options=dag_options,
    )
    runner._configure_llm_runtime_limits(
        task_id="task-b",
        task_config=config,
        dag_options=dag_options,
    )

    assert runner._llm_runtime_limit_source_task == "task-a"
    assert runner._llm_runtime_limit_signature == (4, (("gpt-4o", 2),))
    assert LLMService._global_limit == 4
    assert LLMService._model_limits == {"gpt-4o": 2}


def test_runner_rejects_conflicting_task_level_llm_limits() -> None:
    runner = _build_runner()
    config = DSLightingConfig(workflow=WorkflowConfig(name="aide", params={}))

    runner._configure_llm_runtime_limits(
        task_id="task-a",
        task_config=config,
        dag_options=DagRuntimeOptions(llm_global_max_concurrency=4),
    )

    with pytest.raises(ConfigurationError, match="Conflicting task-level LLM concurrency settings"):
        runner._configure_llm_runtime_limits(
            task_id="task-b",
            task_config=config,
            dag_options=DagRuntimeOptions(llm_global_max_concurrency=8),
        )
