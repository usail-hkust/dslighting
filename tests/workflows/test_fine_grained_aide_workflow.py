"""
Unit tests for FineGrainedAIDEWorkflowDagActor.

Tests cover:
1. Data flow through Gen → Exec → Review nodes
2. Node dependency relationships
3. Retry and failure handling
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock

from dslighting.workflows.search.aide_workflow import FineGrainedAIDEWorkflowDagActor
from dslighting.runtime.dag import NodeResult


class TestFineGrainedDataFlow:
    """测试数据流在细粒度 DAG 中的传递"""

    @pytest.fixture
    def mock_workflow(self):
        """创建 mock workflow 对象"""
        workflow = Mock()
        workflow.agent_config = {"search": {"max_iterations": 3}}
        workflow.generate_op = AsyncMock(return_value=("test_plan", "test_code"))
        workflow.execute_op = AsyncMock()
        workflow.review_op = AsyncMock()
        workflow._finalize_best_solution = AsyncMock(return_value={"status": "success"})
        return workflow

    @pytest.fixture
    def actor(self, mock_workflow):
        """创建测试用的 actor 实例"""
        return FineGrainedAIDEWorkflowDagActor(
            task_id="test_task",
            workflow=mock_workflow,
            description="Test task description",
            io_instructions="Test I/O instructions",
            output_path=Path("/tmp/test_output"),
            enable_debug_branch=False,
            max_retries=3,
        )

    def test_gen_to_exec_data_passing_with_return_value(self, actor):
        """测试 Gen 节点返回值正确传递到 Exec 节点（通过 return_value）"""
        # 创建一个模拟的 Gen 节点成功结果
        result = NodeResult(
            node_id="test_task:gen:0",
            status="success",
            return_value=("my_plan", "my_code"),  # (plan, code) 元组
            outputs={}
        )

        # 调用 _handle_gen_result
        new_nodes, done = actor._handle_gen_result(0, result)

        # 验证返回结果
        assert not done, "Should not be done after successful Gen"
        assert len(new_nodes) == 1, "Should create one Exec node"

        # 验证 Exec 节点配置
        exec_node = new_nodes[0]
        assert exec_node.node_id == "test_task:exec:0"
        assert exec_node.depends_on == ["test_task:gen:0"]
        assert exec_node.payload["kwargs"]["code"] == "my_code"

    def test_gen_to_exec_data_passing_with_outputs(self, actor):
        """测试 Gen 节点 outputs 字典正确传递到 Exec 节点"""
        # 创建一个模拟的 Gen 节点成功结果（outputs 已经存在）
        result = NodeResult(
            node_id="test_task:gen:0",
            status="success",
            return_value=None,
            outputs={"plan": "my_plan", "code": "my_code"}
        )

        # 调用 _handle_gen_result
        new_nodes, done = actor._handle_gen_result(0, result)

        # 验证 Exec 节点创建成功
        assert len(new_nodes) == 1
        assert new_nodes[0].payload["kwargs"]["code"] == "my_code"

    def test_gen_failure_retry(self, actor):
        """测试 Gen 失败时的重试逻辑"""
        # 创建一个失败的 Gen 结果
        result = NodeResult(
            node_id="test_task:gen:0",
            status="failed",
            error="Generation failed",
            outputs={}
        )

        # 第一次失败：应该重试
        new_nodes, done = actor._handle_gen_result(0, result)
        assert not done, "Should not be done after first failure"
        assert len(new_nodes) == 1, "Should create retry Gen node"
        assert new_nodes[0].node_id == "test_task:gen:0"

        # 模拟多次重试直到超过最大重试次数
        for i in range(actor.max_retries):
            actor._retry_counts[result.node_id] = i
            new_nodes, done = actor._handle_gen_result(0, result)

        # 超过最大重试次数：应该终止
        assert done, "Should be done after max retries"
        assert len(new_nodes) == 0, "Should not create new nodes"

    def test_gen_empty_code_retry(self, actor):
        """测试 Gen 返回空代码时的重试逻辑"""
        # 创建一个返回空代码的 Gen 结果
        result = NodeResult(
            node_id="test_task:gen:0",
            status="success",
            return_value=("plan", ""),  # 空代码
            outputs={}
        )

        # 调用 _handle_gen_result
        new_nodes, done = actor._handle_gen_result(0, result)

        # 应该触发重试（因为代码为空）
        assert not done
        assert len(new_nodes) == 1
        assert new_nodes[0].node_id == "test_task:gen:0"

    def test_exec_to_review_data_passing(self, actor):
        """测试 Exec 节点结果正确传递到 Review 节点"""
        # 创建 mock ExecutionResult
        mock_exec_result = Mock()
        mock_exec_result.success = True
        mock_exec_result.stdout = "Execution successful"
        mock_exec_result.stderr = ""
        mock_exec_result.exc_type = None
        mock_exec_result.metadata = {"time": 1.0}
        mock_exec_result.code = "executed_code"

        # 创建 Exec 节点成功结果
        result = NodeResult(
            node_id="test_task:exec:0",
            status="success",
            return_value=mock_exec_result,
            outputs={}
        )

        # 调用 _handle_exec_result
        new_nodes, done = actor._handle_exec_result(0, result)

        # 验证 Review 节点创建成功
        assert not done
        assert len(new_nodes) == 1
        review_node = new_nodes[0]
        assert review_node.node_id == "test_task:review:0"
        assert review_node.depends_on == ["test_task:exec:0"]

        # 验证传递给 Review 的上下文
        prompt_context = review_node.payload["kwargs"]["prompt_context"]
        assert prompt_context["code"] == "executed_code"
        assert prompt_context["output"] == "Execution successful"


class TestFineGrainedDependencies:
    """测试节点依赖关系的正确性"""

    @pytest.fixture
    def actor(self):
        """创建测试用的 actor 实例"""
        mock_workflow = Mock()
        mock_workflow.agent_config = {"search": {"max_iterations": 3}}

        return FineGrainedAIDEWorkflowDagActor(
            task_id="test_task",
            workflow=mock_workflow,
            description="Test task",
            io_instructions="Test I/O",
            output_path=Path("/tmp/test"),
            enable_debug_branch=False,
            max_retries=3,
        )

    def test_review_to_gen_dependency(self, actor):
        """测试 Gen_1 正确依赖 Review_0"""
        # 模拟 Review_0 完成
        result = NodeResult(
            node_id="test_task:review:0",
            status="success",
            outputs={}
        )

        # 调用 _continue_or_finish
        new_nodes, done = actor._handle_review_result(0, result)

        # 验证 Gen_1 创建并依赖 Review_0
        assert not done
        assert len(new_nodes) == 1
        gen_node = new_nodes[0]
        assert gen_node.node_id == "test_task:gen:1"
        assert "test_task:review:0" in gen_node.depends_on, "Gen_1 should depend on Review_0"

    def test_final_iteration_creates_finalize(self, actor):
        """测试最后一次迭代创建 Finalize 节点"""
        # 模拟最后一步的 Review 完成（step=2，即第3步）
        result = NodeResult(
            node_id="test_task:review:2",
            status="success",
            outputs={}
        )

        # 调用 _continue_or_finish
        new_nodes, done = actor._continue_or_finish(2)

        # 验证 Finalize 节点创建
        assert not done
        assert len(new_nodes) == 1
        finalize_node = new_nodes[0]
        assert finalize_node.node_id == "test_task:finalize"
        assert "test_task:review:2" in finalize_node.depends_on, "Finalize should depend on last Review"

    def test_dag_chain_structure(self, actor):
        """测试完整的 DAG 链式结构"""
        # Gen_0 -> Exec_0 -> Review_0 -> Gen_1 -> Exec_1 -> Review_1 -> ...

        # 初始节点应该是 Gen_0
        initial_nodes = actor.initial_nodes()
        assert len(initial_nodes) == 1
        assert initial_nodes[0].node_id == "test_task:gen:0"
        assert initial_nodes[0].depends_on == []

        # 模拟 Gen_0 成功
        gen_result = NodeResult(
            node_id="test_task:gen:0",
            status="success",
            return_value=("plan", "code"),
            outputs={}
        )
        nodes, _ = actor._handle_gen_result(0, gen_result)
        assert nodes[0].node_id == "test_task:exec:0"
        assert "test_task:gen:0" in nodes[0].depends_on

        # 模拟 Exec_0 成功
        exec_result = NodeResult(
            node_id="test_task:exec:0",
            status="success",
            return_value=Mock(success=True, stdout="out", stderr="", exc_type=None, metadata={}),
            outputs={}
        )
        nodes, _ = actor._handle_exec_result(0, exec_result)
        assert nodes[0].node_id == "test_task:review:0"
        assert "test_task:exec:0" in nodes[0].depends_on

        # 模拟 Review_0 成功
        review_result = NodeResult(
            node_id="test_task:review:0",
            status="success",
            outputs={}
        )
        nodes, _ = actor._handle_review_result(0, review_result)
        assert nodes[0].node_id == "test_task:gen:1"
        assert "test_task:review:0" in nodes[0].depends_on


class TestFineGrainedExecFailure:
    """测试 Exec 失败时的处理"""

    @pytest.fixture
    def actor_debug_enabled(self):
        """创建启用 debug 分支的 actor"""
        mock_workflow = Mock()
        mock_workflow.agent_config = {"search": {"max_iterations": 3}}

        return FineGrainedAIDEWorkflowDagActor(
            task_id="test_task",
            workflow=mock_workflow,
            description="Test task",
            io_instructions="Test I/O",
            output_path=Path("/tmp/test"),
            enable_debug_branch=True,  # 启用 debug 分支
            max_retries=3,
        )

    @pytest.fixture
    def actor_debug_disabled(self):
        """创建禁用 debug 分支的 actor"""
        mock_workflow = Mock()
        mock_workflow.agent_config = {"search": {"max_iterations": 3}}

        return FineGrainedAIDEWorkflowDagActor(
            task_id="test_task",
            workflow=mock_workflow,
            description="Test task",
            io_instructions="Test I/O",
            output_path=Path("/tmp/test"),
            enable_debug_branch=False,  # 禁用 debug 分支
            max_retries=3,
        )

    def test_exec_failure_with_debug_branch(self, actor_debug_enabled):
        """测试 Exec 失败时启用 debug 分支的行为"""
        result = NodeResult(
            node_id="test_task:exec:0",
            status="failed",
            error="Execution failed",
            outputs={}
        )

        new_nodes, done = actor_debug_enabled._handle_exec_result(0, result)

        # 启用 debug 分支时，应该直接终止
        assert done, "Should terminate when debug branch is enabled"
        assert len(new_nodes) == 0

    def test_exec_failure_without_debug_branch(self, actor_debug_disabled):
        """测试 Exec 失败时禁用 debug 分支的行为（继续下一轮）"""
        result = NodeResult(
            node_id="test_task:exec:0",
            status="failed",
            error="Execution failed",
            outputs={}
        )

        new_nodes, done = actor_debug_disabled._handle_exec_result(0, result)

        # 禁用 debug 分支时，应该继续到下一轮
        assert not done, "Should continue when debug branch is disabled"
        assert len(new_nodes) == 1
        assert new_nodes[0].node_id == "test_task:gen:1"
