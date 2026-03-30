from __future__ import annotations

import weakref

import pytest

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


@pytest.mark.asyncio
async def test_configure_concurrency_limits_is_idempotent_for_same_signature() -> None:
    LLMService.configure_concurrency_limits(
        global_max_concurrency=4,
        model_quotas={"gpt-4o": 2},
    )
    global_sem_1, model_sems_1 = LLMService._get_loop_concurrency_controls()

    LLMService.configure_concurrency_limits(
        global_max_concurrency=4,
        model_quotas={"gpt-4o": 2},
    )
    global_sem_2, model_sems_2 = LLMService._get_loop_concurrency_controls()

    assert global_sem_1 is global_sem_2
    assert model_sems_1["gpt-4o"] is model_sems_2["gpt-4o"]


@pytest.mark.asyncio
async def test_configure_concurrency_limits_rebuilds_semaphores_when_signature_changes() -> None:
    LLMService.configure_concurrency_limits(
        global_max_concurrency=4,
        model_quotas={"gpt-4o": 2},
    )
    global_sem_1, model_sems_1 = LLMService._get_loop_concurrency_controls()

    LLMService.configure_concurrency_limits(
        global_max_concurrency=6,
        model_quotas={"gpt-4o": 3},
    )
    global_sem_2, model_sems_2 = LLMService._get_loop_concurrency_controls()

    assert global_sem_1 is not global_sem_2
    assert model_sems_1["gpt-4o"] is not model_sems_2["gpt-4o"]


@pytest.mark.asyncio
async def test_configure_concurrency_limits_can_clear_previous_run_state() -> None:
    LLMService.configure_concurrency_limits(
        global_max_concurrency=4,
        model_quotas={"gpt-4o": 2},
    )
    LLMService.configure_concurrency_limits(
        global_max_concurrency=None,
        model_quotas=None,
    )

    global_sem, model_sems = LLMService._get_loop_concurrency_controls()

    assert LLMService._global_limit is None
    assert LLMService._model_limits == {}
    assert global_sem is None
    assert model_sems == {}
