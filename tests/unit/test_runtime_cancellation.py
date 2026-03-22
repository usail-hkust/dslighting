from __future__ import annotations

import asyncio

import pytest

from dslighting.runtime.dag import BaseWorkflowActor, DagRuntime, DagRuntimeOptions, NodeResult, OpNode


class _CancelableActor(BaseWorkflowActor):
    def __init__(self) -> None:
        self.task_id = "cancel-task"

    async def _slow_op(self) -> dict[str, int]:
        await asyncio.sleep(0.05)
        return {"value": 1}

    async def _fast_op(self) -> dict[str, int]:
        return {"value": 2}

    def initial_nodes(self) -> list[OpNode]:
        return [
            OpNode(
                node_id="slow",
                task_id=self.task_id,
                op_type="custom",
                operator_name="slow",
                payload={"callable": self._slow_op},
            ),
            OpNode(
                node_id="fast",
                task_id=self.task_id,
                op_type="custom",
                operator_name="fast",
                payload={"callable": self._fast_op},
            ),
        ]

    def on_node_result(self, result: NodeResult):
        _ = result
        return [], False


@pytest.mark.asyncio
async def test_request_cancellation_stops_new_scheduling_and_marks_remaining_nodes() -> None:
    runtime = DagRuntime(
        options=DagRuntimeOptions(
            enabled=True,
            max_inflight_nodes=1,
            node_timeout_seconds=2.0,
        )
    )
    actor = _CancelableActor()

    run_task = asyncio.create_task(runtime.run_actor(actor))
    await asyncio.sleep(0.01)
    runtime.request_cancellation("test cancellation")
    summary = await run_task

    assert summary.successful_nodes == 1
    assert summary.cancelled_nodes == 1
    assert summary.failed_nodes == 0
    assert summary.last_error is not None
    assert "cancelled" in summary.last_error.lower()
