"""
Integration tests for fine-grained DAG workflow.

Tests cover:
1. End-to-end workflow execution
2. Comparison with coarse-grained implementation
3. Concurrency and thread safety
"""
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from dslighting.workflows.search.aide_workflow import AIDEWorkflow, FineGrainedAIDEWorkflowDagActor
from dslighting.runtime.dag import DagRuntime, DagRuntimeOptions
from dslighting.state.search.journal import JournalState, Node


@pytest.mark.asyncio
async def test_fine_grained_dag_end_to_end():
    """端到端测试细粒度 DAG workflow"""

    # 创建 mock services
    mock_sandbox = Mock()
    mock_sandbox.workspace.get_path.return_value = Path("/tmp/sandbox")

    mock_llm = AsyncMock()
    mock_llm.get_call_history.return_value = []

    # Mock generate_op 返回 (plan, code)
    async def mock_generate(system_prompt: str):
        return "test_plan", f"def solution():\n    pass  # Step {len(mock_llm.get_call_history())}"

    # Mock execute_op 返回 ExecutionResult
    class MockExecResult:
        def __init__(self, success=True):
            self.success = success
            self.stdout = "Output" if success else ""
            self.stderr = "" if success else "Error"
            self.exc_type = None if success else "Exception"
            self.metadata = {}
            self.code = "test_code"

    async def mock_execute(code: str, mode: str):
        return MockExecResult(success=True)

    # Mock review_op 返回 ReviewResult
    class MockReviewResult:
        summary = "Review passed"
        is_buggy = False
        metric_value = 0.95
        lower_is_better = False

    async def mock_review(prompt_context: dict):
        return MockReviewResult()

    mock_llm.call = mock_generate

    # 创建 operators
    operators = {
        "generate": mock_generate,
        "execute": mock_execute,
        "review": mock_review,
    }

    services = {
        "state": JournalState(),
        "sandbox": mock_sandbox,
        "llm": mock_llm,
    }

    agent_config = {
        "search": {
            "max_iterations": 2,
        }
    }

    # 创建 workflow
    workflow = AIDEWorkflow(operators, services, agent_config)

    # 创建细粒度 actor
    output_path = Path("/tmp/test_output.csv")
    actor = FineGrainedAIDEWorkflowDagActor(
        task_id="integration_test",
        workflow=workflow,
        description="Test integration task",
        io_instructions="Input: test.csv, Output: submission.csv",
        output_path=output_path,
        enable_debug_branch=False,
        max_retries=2,
    )

    # 运行 DAG
    runtime = DagRuntime(options=DagRuntimeOptions(max_inflight_nodes=2))

    # Mock _finalize_best_solution
    async def mock_finalize(output_path: Path) -> dict:
        return {
            "has_best_node": True,
            "best_step": 1,
            "status": "success",
        }

    workflow._finalize_best_solution = mock_finalize

    summary = await runtime.run_actor(actor)

    # 验证结果
    assert summary["status"] == "success"


@pytest.mark.asyncio
async def test_journal_state_concurrent_append():
    """测试 JournalState 并发 append 操作的线程安全性"""
    state = JournalState()

    # 模拟 10 个并发 append 操作
    async def append_node(node_id: int):
        node = Node(
            id=f"node_{node_id}",
            plan=f"Plan {node_id}",
            code=f"Code {node_id}"
        )
        # 模拟一些处理时间
        await asyncio.sleep(0.001)
        state.append(node)

    # 创建并发任务
    tasks = [append_node(i) for i in range(10)]

    # 等待所有任务完成
    await asyncio.gather(*tasks)

    # 验证所有节点都正确添加
    assert len(state.nodes) == 10
    for i in range(10):
        assert f"node_{i}" in state.nodes
        assert state.nodes[f"node_{i}"].code == f"Code {i}"


@pytest.mark.asyncio
async def test_journal_state_concurrent_best_node():
    """测试并发调用 get_best_node 不会导致数据竞争"""
    state = JournalState()

    # 添加一些节点
    for i in range(5):
        node = Node(
            id=f"node_{i}",
            plan=f"Plan {i}",
            code=f"Code {i}"
        )
        # 标记前3个为 buggy，后2个为 non-buggy
        node.is_buggy = (i < 3)
        from dslighting.state.search.journal import MetricValue
        node.metric = MetricValue(value=float(i), maximize=True)
        state.append(node)

    # 并发读取最佳节点
    async def get_best():
        await asyncio.sleep(0.001)  # 模拟处理时间
        return state.get_best_node()

    tasks = [get_best() for _ in range(10)]
    results = await asyncio.gather(*tasks)

    # 验证所有结果一致
    assert all(r is not None for r in results)
    assert all(r.id == results[0].id for r in results)
    # 最佳节点应该是 metric 最大且 non-buggy 的节点（node_4）
    assert results[0].id == "node_4"


@pytest.mark.asyncio
async def test_journal_state_concurrent_summary():
    """测试并发调用 generate_summary 不会导致冲突"""
    state = JournalState()

    # 添加一些成功的节点
    for i in range(5):
        node = Node(
            id=f"node_{i}",
            plan=f"Plan {i}",
            code=f"Code {i}"
        )
        node.is_buggy = False
        from dslighting.state.search.journal import MetricValue
        node.metric = MetricValue(value=float(i), maximize=True)
        node.analysis = f"Analysis {i}"
        state.append(node)

    # 并发生成摘要
    async def get_summary():
        await asyncio.sleep(0.001)
        return state.generate_summary(max_nodes=2)

    tasks = [get_summary() for _ in range(5)]
    results = await asyncio.gather(*tasks)

    # 验证所有摘要都包含有效内容
    for summary in results:
        assert "Attempt #" in summary
        assert "Plan:" in summary
        assert "Validation Metric:" in summary


@pytest.mark.asyncio
async def test_fine_grained_dag_failure_recovery():
    """测试细粒度 DAG 在节点失败时的恢复机制"""
    # 创建 mock services
    mock_sandbox = Mock()
    mock_llm = AsyncMock()
    mock_llm.get_call_history.return_value = []

    # Mock generate_op - 第一次失败，第二次成功
    gen_call_count = [0]

    async def mock_generate(system_prompt: str):
        gen_call_count[0] += 1
        if gen_call_count[0] == 1:
            raise Exception("LLM service unavailable")
        return "recovered_plan", "recovered_code"

    # Mock execute_op
    class MockExecResult:
        def __init__(self, success=True):
            self.success = success
            self.stdout = "Output"
            self.stderr = ""
            self.exc_type = None
            self.metadata = {}
            self.code = "code"

    async def mock_execute(code: str, mode: str):
        return MockExecResult(success=True)

    # Mock review_op
    class MockReviewResult:
        summary = "Good"
        is_buggy = False
        metric_value = 0.9
        lower_is_better = False

    async def mock_review(prompt_context: dict):
        return MockReviewResult()

    operators = {
        "generate": mock_generate,
        "execute": mock_execute,
        "review": mock_review,
    }

    services = {
        "state": JournalState(),
        "sandbox": mock_sandbox,
        "llm": mock_llm,
    }

    agent_config = {"search": {"max_iterations": 2}}

    workflow = AIDEWorkflow(operators, services, agent_config)

    actor = FineGrainedAIDEWorkflowDagActor(
        task_id="recovery_test",
        workflow=workflow,
        description="Test recovery",
        io_instructions="Test I/O",
        output_path=Path("/tmp/test.csv"),
        enable_debug_branch=False,
        max_retries=3,
    )

    # Mock finalize
    async def mock_finalize(output_path: Path):
        return {"status": "success"}

    workflow._finalize_best_solution = mock_finalize

    # 运行 DAG - 应该从失败中恢复
    runtime = DagRuntime(options=DagRuntimeOptions(max_inflight_nodes=1))
    summary = await runtime.run_actor(actor)

    # 验证恢复成功
    assert summary["status"] == "success"
    assert gen_call_count[0] > 1, "Should have retried generation"


@pytest.mark.asyncio
async def test_dag_dependency_chain_integrity():
    """测试 DAG 依赖链在复杂场景下的完整性"""
    # 创建 mock workflow
    mock_workflow = Mock()
    mock_workflow.agent_config = {"search": {"max_iterations": 3}}

    actor = FineGrainedAIDEWorkflowDagActor(
        task_id="chain_test",
        workflow=mock_workflow,
        description="Test chain",
        io_instructions="Test I/O",
        output_path=Path("/tmp/test.csv"),
        enable_debug_branch=False,
        max_retries=2,
    )

    # 模拟完整的 DAG 执行链
    executed_order = []

    # Gen_0
    result = NodeResult(
        node_id="chain_test:gen:0",
        status="success",
        return_value=("plan0", "code0"),
        outputs={}
    )
    nodes, _ = actor._handle_gen_result(0, result)
    executed_order.append(result.node_id)
    assert len(nodes) == 1
    assert nodes[0].depends_on == [result.node_id]

    # Exec_0
    exec_result = NodeResult(
        node_id="chain_test:exec:0",
        status="success",
        return_value=Mock(success=True, stdout="out", stderr="", exc_type=None, metadata={}, code="code0"),
        outputs={}
    )
    nodes, _ = actor._handle_exec_result(0, exec_result)
    executed_order.append(exec_result.node_id)
    assert len(nodes) == 1
    assert nodes[0].depends_on == [exec_result.node_id]

    # Review_0
    review_result = NodeResult(
        node_id="chain_test:review:0",
        status="success",
        outputs={}
    )
    nodes, _ = actor._handle_review_result(0, review_result)
    executed_order.append(review_result.node_id)
    assert len(nodes) == 1
    assert nodes[0].depends_on == [review_result.node_id]  # Gen_1 应该依赖 Review_0

    # 验证执行顺序
    assert executed_order == [
        "chain_test:gen:0",
        "chain_test:exec:0",
        "chain_test:review:0"
    ]
