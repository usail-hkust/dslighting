# DSAT 完整架构分析

## 📋 概述

本文档完整分析了 DSAT 框架的所有组件，为 DSLighting 2.0 的设计提供参考。

**目标**: DSLighting 2.0 应该封装所有 DSAT 组件，提供简单易用的 Agent 基类，用户无需知道 DSAT 的存在。

---

## 🏗️ DSAT 架构层次

```
┌─────────────────────────────────────────┐
│   DSLighting 2.0 (用户层)               │
│   - Agent Base Class                   │
│   - Tools                               │
│   - 简化 API                            │
└─────────────────┬───────────────────────┘
                  │ 封装
┌─────────────────▼───────────────────────┐
│   DSAT (框架层)                         │
│   - Services                           │
│   - Operators                          │
│   - Prompts                            │
│   - Workflows                          │
│   - State Management                   │
└─────────────────────────────────────────┘
```

---

## 📦 组件目录

### 1. Services (服务层)

#### 1.1 LLMService (`dsat/services/llm.py`)

**用途**: LLM 调用服务，支持多模型、成本追踪

**核心方法**:
```python
class LLMService:
    def __init__(self, model: str, temperature: float = 0.7, ...):
        """初始化 LLM 服务"""

    async def call(self, prompt: str, **kwargs) -> str:
        """调用 LLM 生成文本"""

    async def call_with_json(self, prompt: str, output_model: BaseModel) -> BaseModel:
        """调用 LLM 生成结构化 JSON 输出"""

    def get_call_history(self) -> List[Dict]:
        """获取 LLM 调用历史（用于追踪）"""
```

**关键特性**:
- 支持 LiteLLM（可切换多个 LLM 提供商）
- 自动成本追踪
- API Key 轮换
- 调用历史记录
- 结构化输出支持

---

#### 1.2 SandboxService (`dsat/services/sandbox.py`)

**用途**: 安全执行代码环境

**核心方法**:
```python
class SandboxService:
    def __init__(self, workspace: WorkspaceService, timeout: int = 600):
        """初始化沙箱服务"""

    def run_script(self, script_code: str) -> ExecutionResult:
        """以脚本模式执行代码（隔离进程）"""

    @asynccontextmanager
    async def notebook_executor(self) -> ProcessIsolatedNotebookExecutor:
        """提供 Jupyter Notebook 执行器（持久化 Kernel）"""

    def get_execution_history(self) -> List[Dict]:
        """获取执行历史"""
```

**返回类型**:
```python
class ExecutionResult:
    success: bool
    stdout: str
    stderr: str
    exc_type: Optional[str]
    artifacts: List[str]
    metadata: Dict[str, Any]
```

**关键特性**:
- 两种执行模式：script（隔离进程）、notebook（持久化 Kernel）
- 自动超时控制
- 执行历史记录
- 安全隔离（进程级别）
- matplotlib 非交互后端自动注入

---

#### 1.3 WorkspaceService (`dsat/services/workspace.py`)

**用途**: 工作区管理，负责文件系统组织

**核心方法**:
```python
class WorkspaceService:
    def __init__(self, run_name: str, base_dir: str = None):
        """初始化工作区"""

    def get_path(self, name: str) -> Path:
        """获取特定路径（logs, artifacts, state, etc.）"""

    def write_file(self, content: str, path_name: str, sub_path: str = None):
        """写入文件到指定目录"""

    def link_data_to_workspace(self, source_data_dir: Path):
        """链接或复制数据到工作区"""

    def cleanup(self, keep_workspace: bool = False):
        """清理工作区"""
```

**管理的目录结构**:
```
run_dir/
├── sandbox/           # 沙箱工作目录
├── config.yaml        # 配置文件
├── workflow.py        # 工作流代码
├── logs/              # 日志文件
├── state/             # 状态文件
├── candidates/        # 候选工作流
├── artifacts/         # 产物文件
└── results.json       # 结果文件
```

---

#### 1.4 DataAnalyzer (`dsat/services/data_analyzer.py`)

**用途**: 数据分析服务，自动分析数据集结构

**核心方法**:
```python
class DataAnalyzer:
    def analyze(self, data_dir: Path, output_filename: str, task_type: Optional[TaskType] = None) -> str:
        """完整分析：结构 + schema + I/O 指令"""

    def analyze_data(self, data_dir: Path, task_type: Optional[TaskType] = None) -> str:
        """仅分析数据（不包含 I/O 指令）"""

    def generate_io_instructions(self, output_filename: str, optimization_context: bool = False) -> str:
        """生成标准 I/O 指令"""
```

**分析内容**:
- 文件树生成（智能截断）
- 数据 schema 分析（列类型、缺失值、基数）
- Kaggle 提交格式分析（sample_submission.csv）
- 标准 I/O 指令生成

---

#### 1.5 VDBService (`dsat/services/vdb.py`)

**用途**: 向量数据库服务，用于案例检索 (RAG)

**核心方法**:
```python
class VDBService:
    def __init__(self, case_dir: str, model_name: str = "BAAI/llm-embedder"):
        """初始化向量数据库"""

    def retrieve(self, query: str, top_k: int) -> List[str]:
        """检索最相似的案例文本"""

    async def search(self, query: str, top_k: int = 5):
        """异步搜索接口"""
```

**关键特性**:
- 使用 Transformer 嵌入模型
- CLS pooling
- 余弦相似度搜索
- 用于案例检索增强生成

---

### 2. State Management (状态管理)

#### 2.1 JournalState (`dsat/services/states/journal.py`)

**用途**: 管理搜索树状态（用于 AIDE/AutoMind 等搜索型工作流）

**核心数据结构**:
```python
class Node(BaseModel):
    code: str
    plan: str
    id: str
    parent_id: Optional[str]
    children_ids: Set[str]

    # 执行结果
    term_out: str
    exec_time: float
    exc_type: Optional[str]
    exec_metadata: Dict[str, Any]

    # LLM 记录
    task_context: Dict[str, Any]
    generate_prompt: Optional[str]
    llm_generate: Optional[Dict[str, Any]]
    review_context: Optional[Dict[str, Any]]
    llm_review: Optional[Dict[str, Any]]

    # 审查结果
    analysis: str
    metric: MetricValue
    is_buggy: bool
    step: int

    def absorb_exec_result(self, exec_result: ExecutionResult):
        """吸收执行结果到节点"""

class JournalState(State):
    nodes: Dict[str, Node]

    def append(self, node: Node, parent: Optional[Node] = None):
        """添加节点到日志"""

    def get_best_node(self) -> Optional[Node]:
        """获取最佳性能节点"""

    def generate_summary(self, max_nodes: int = 3) -> str:
        """生成成功尝试的摘要"""
```

**用途**: 维护搜索树，记录所有尝试、执行结果、评分

---

#### 2.2 Experience (`dsat/services/states/experience.py`)

**用途**: 管理元优化经验（用于 AFlow 等进化搜索工作流）

**核心方法**:
```python
class Experience(State):
    def __init__(self, workspace: WorkspaceService):
        """初始化经验数据库"""

    def get_experience_summary(self, parent_round_num: Optional[int]) -> str:
        """获取特定父候选人的修改历史"""

    def select_parent_candidate(self, top_k: int) -> Optional[WorkflowCandidate]:
        """使用 softmax 选择父候选人（探索-利用平衡）"""

    def record_score(self, round_num: int, fitness: float, code: str, ...):
        """记录工作流分数"""

    def record_experience(self, parent_round: int, child_round: int, modification: str, score_before: float, score_after: float):
        """记录修改结果到经验日志"""
```

**用途**: 记录哪些修改成功/失败，指导元优化器

---

### 3. Operators (操作器层)

#### 3.1 Operator Base (`dsat/operators/base.py`)

**基础抽象类**:
```python
class Operator(ABC):
    def __init__(self, llm_service: Optional[LLMService] = None, name: Optional[str] = None):
        self.llm_service = llm_service
        self.name = name

    @abstractmethod
    async def __call__(self, *args, **kwargs) -> Any:
        raise NotImplementedError
```

**所有操作器都继承自这个基类**

---

#### 3.2 GenerateCodeAndPlanOperator (`dsat/operators/llm_basic.py`)

**用途**: 生成计划和代码

```python
class GenerateCodeAndPlanOperator(Operator):
    async def __call__(self, system_prompt: str, user_prompt: str = "") -> tuple[str, str]:
        """生成 (plan, code) 元组"""
```

---

#### 3.3 PlanOperator (`dsat/operators/llm_basic.py`)

**用途**: 创建结构化计划

```python
class PlanOperator(Operator):
    async def __call__(self, user_request: str) -> Plan:
        """生成结构化 JSON 计划"""
```

---

#### 3.4 ReviewOperator (`dsat/operators/llm_basic.py`)

**用途**: 审查代码输出并评分

```python
class ReviewOperator(Operator):
    async def __call__(self, prompt_context: Dict) -> ReviewResult:
        """审查输出并返回评分"""
```

**返回类型**:
```python
class ReviewResult(BaseModel):
    summary: str
    metric_value: Optional[float]
    lower_is_better: bool
    is_buggy: bool
```

---

#### 3.5 ExecuteAndTestOperator (`dsat/operators/code.py`)

**用途**: 执行代码（封装 SandboxService）

```python
class ExecuteAndTestOperator(Operator):
    def __init__(self, sandbox_service: SandboxService):
        self.sandbox = sandbox_service

    async def __call__(self, code: str, mode: str = "script", executor_context: Any = None) -> ExecutionResult:
        """执行代码并返回结果"""
```

**支持模式**:
- `script`: 隔离进程执行
- `notebook`: 持久化 Jupyter Kernel 执行

---

### 4. Prompts (提示词层)

#### 4.1 Common Prompts (`dsat/prompts/common.py`)

**通用提示词组件**:
```python
def create_draft_prompt(task_context: Dict, memory_summary: str, retrieved_knowledge: Optional[str] = None) -> str:
    """创建初始草稿提示词"""
```

**包含**:
- 角色定义
- 任务目标
- I/O 要求
- 实现指南
- 响应格式规范

---

#### 4.2 AIDE Prompts (`dsat/prompts/aide_prompt.py`)

**搜索型工作流提示词**:
```python
def create_improve_prompt(task_context, memory_summary, previous_code, previous_analysis, ...) -> str:
    """改进现有解决方案"""

def create_debug_prompt(task_context, buggy_code, error_history, ...) -> str:
    """调试失败解决方案"""
```

---

#### 4.3 Data Interpreter Prompts (`dsat/prompts/data_interpreter_prompt.py`)

**计划执行型提示词**:
```python
PLAN_SYSTEM_MESSAGE = """
计划器系统消息
"""

GENERATE_CODE_PROMPT = """
生成代码提示词模板
"""

REFLECT_AND_DEBUG_PROMPT = """
反思和调试提示词模板
"""

FINALIZE_OUTPUT_PROMPT = """
最终输出生成提示词模板
"""
```

---

### 5. Workflows (工作流层)

#### 5.1 DSATWorkflow Base (`dsat/workflows/base.py`)

**所有工作流的基类**:
```python
class DSATWorkflow(ABC):
    def __init__(self, operators: Dict[str, Operator], services: Dict[str, Any], agent_config: Dict[str, Any]):
        self.operators = operators
        self.services = services
        self.agent_config = agent_config

    @abstractmethod
    async def solve(self, description: str, io_instructions: str, data_dir: Path, output_path: Path) -> None:
        """解决任务的主方法"""
        raise NotImplementedError
```

**这是唯一需要实现的接口！**

---

#### 5.2 AIDEWorkflow (`dsat/workflows/search/aide_workflow.py`)

**搜索型工作流示例**:

```python
class AIDEWorkflow(DSATWorkflow):
    """AIDE 迭代搜索算法"""

    async def solve(self, description, io_instructions, data_dir, output_path):
        # 1. 选择节点
        parent_node = self._select_node_to_expand()

        # 2. 创建提示词
        if parent_node is None:
            prompt = create_draft_prompt(...)
        elif parent_node.is_buggy:
            prompt = create_debug_prompt(...)
        else:
            prompt = create_improve_prompt(...)

        # 3. 生成新代码
        plan, code = await self.generate_op(system_prompt=prompt)

        # 4. 执行代码
        exec_result = await self.execute_op(code=code, mode="script")

        # 5. 审查和评分
        review = await self.review_op(prompt_context=...)

        # 6. 添加到状态
        self.state.append(new_node, parent_node)
```

**关键点**:
- 使用 `JournalState` 管理搜索树
- 三种提示词模式：draft, debug, improve
- 迭代搜索最佳解决方案
- 支持基准测试验证

---

#### 5.3 DataInterpreterWorkflow (`dsat/workflows/manual/data_interpreter_workflow.py`)

**计划执行型工作流示例**:

```python
class DataInterpreterWorkflow(DSATWorkflow):
    """计划执行循环"""

    async def solve(self, description, io_instructions, data_dir, output_path):
        # 1. 创建计划
        plan = await self.planner_op(user_request=full_context)

        # 2. 在 Notebook 中执行任务
        async with self.sandbox_service.notebook_executor() as notebook:
            for task in plan.tasks:
                # 生成代码
                prompt = GENERATE_CODE_PROMPT.format(...)
                _, code = await self.generator_op(system_prompt=prompt)

                # 执行代码
                result = await self.executor_op(code=code, mode="notebook", executor_context=notebook)

                # 如果失败，调试
                if not result.success:
                    debug_prompt = REFLECT_AND_DEBUG_PROMPT.format(...)
                    _, fixed_code = await self.debugger_op(system_prompt=debug_prompt)
                    result = await self.executor_op(code=fixed_code, mode="notebook", executor_context=notebook)

        # 3. 生成最终输出
        finalize_prompt = FINALIZE_OUTPUT_PROMPT.format(...)
        _, final_code = await self.generator_op(system_prompt=finalize_prompt)
        await self.executor_op(code=final_code, mode="notebook", executor_context=notebook)
```

**关键点**:
- 使用 `PlanOperator` 创建结构化计划
- 使用 Notebook 模式保持状态
- 任务级重试机制
- 生成执行报告

---

## 🎯 DSLighting 2.0 需要暴露的组件

### 核心原则

**用户不应该知道 DSAT 的存在！**

所有 DSAT 组件应该通过 DSLighting 2.0 的简洁 API 暴露。

---

### DSLighting 2.0 应该提供

#### 1. **完整的 Agent 基类**

```python
# dslighting/agents/llm_agent.py (提议)

from dslighting.agents.base import BaseAgent, Action, Context, Tool
from typing import Dict, Any, Optional
from pathlib import Path

class LLMAgent(BaseAgent):
    """
    完整的 LLM Agent 基类

    封装了所有 DSAT 功能：
    - LLM 服务
    - 沙箱执行
    - 状态管理
    - 操作器
    - 提示词管理
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_iterations: int = 5,
        workspace_dir: Optional[str] = None,
        enable_notebook: bool = False,
        ...
    ):
        """
        初始化 Agent

        自动创建：
        - LLMService
        - SandboxService
        - WorkspaceService
        - DataAnalyzer
        - 所有 Operators
        """
        super().__init__()

        # 自动初始化所有服务（用户不知道 DSAT 存在）
        self._initialize_services()

    @abstractmethod
    async def plan(self, context: Context) -> Action:
        """
        用户需要实现的唯一方法

        Args:
            context: 包含任务描述、数据信息、历史记录

        Returns:
            Action: 要执行的操作
        """
        raise NotImplementedError

    # ========== 用户提供的能力 ==========

    async def generate_code(self, prompt: str) -> str:
        """使用 LLM 生成代码"""

    async def execute_code(self, code: str, mode: str = "script") -> ExecutionResult:
        """在沙箱中执行代码"""

    async def review_output(self, code: str, output: str) -> ReviewResult:
        """审查代码输出"""

    async def create_plan(self, user_request: str) -> Plan:
        """创建结构化计划"""

    def analyze_data(self, data_dir: Path) -> str:
        """分析数据集"""

    def get_memory_summary(self) -> str:
        """获取历史记忆摘要"""

    # ========== 内部实现（用户不直接调用） ==========

    def _initialize_services(self):
        """初始化所有 DSAT 服务（内部方法）"""
        # 用户不需要知道这些细节
        pass
```

---

#### 2. **统一的工具系统**

```python
# dslighting/tools/registry.py (提议)

class ToolRegistry:
    """工具注册表"""

    def register_tool(self, name: str, tool: Tool):
        """注册工具"""

    def get_tool(self, name: str) -> Tool:
        """获取工具"""

# 预定义工具
class CodeExecutionTool(Tool):
    """代码执行工具（封装 Sandbox）"""

class DataAnalysisTool(Tool):
    """数据分析工具（封装 DataAnalyzer）"""

class LLMPromptTool(Tool):
    """LLM 提示词工具（封装 LLMService）"""
```

---

#### 3. **简化的状态管理**

```python
# dslighting/agents/memory.py (提议)

class AgentMemory:
    """Agent 记忆系统（封装 JournalState）"""

    def add_attempt(self, code: str, plan: str, result: ExecutionResult, score: float):
        """添加尝试记录"""

    def get_best_attempt(self) -> Optional[Attempt]:
        """获取最佳尝试"""

    def get_summary(self) -> str:
        """获取记忆摘要（用于提示词）"""

    def get_error_history(self, max_depth: int = 3) -> str:
        """获取错误历史"""
```

---

#### 4. **简化的配置**

```python
# 用户配置（不需要知道 DSAT）

from dslighting import LLMAgent

class MyAgent(LLMAgent):
    def __init__(self):
        super().__init__(
            model="gpt-4o",
            temperature=0.7,
            max_iterations=5,
        )

    async def plan(self, context: Context) -> Action:
        # 获取数据摘要
        data_report = self.analyze_data(context.data_dir)

        # 获取历史记忆
        memory = self.get_memory_summary()

        # 生成代码
        prompt = f"""
        Task: {context.task_description}
        Data: {data_report}
        Past Attempts: {memory}
        """

        code = await self.generate_code(prompt)

        # 执行代码
        result = await self.execute_code(code)

        # 审查结果
        review = await self.review_output(code, result.stdout)

        # 决定下一步
        if review.is_buggy:
            # 调试
            return Action.debug(code, result.stderr)
        else:
            # 记录成功
            self.memory.add_attempt(code, "", result, review.metric_value)
            return Action.success(code)
```

---

## 📊 对比：当前 vs 理想

### 当前（❌ 用户需要知道 DSAT）

```python
# 用户需要导入 DSAT
from dsat.workflows.base import DSATWorkflow
from dsat.services.llm import LLMService
from dsat.services.sandbox import SandboxService
from dsat.operators.llm_basic import GenerateCodeAndPlanOperator

# 用户需要手动创建服务
workspace = WorkspaceService(run_name="test")
llm_service = LLMService(model="gpt-4o")
sandbox_service = SandboxService(workspace=workspace)

# 用户需要手动创建操作器
operators = {
    "generate": GenerateCodeAndPlanOperator(llm_service=llm_service),
    "execute": ExecuteAndTestOperator(sandbox_service=sandbox_service),
}

# 用户需要知道服务字典
services = {
    "llm": llm_service,
    "sandbox": sandbox_service,
}

# 用户需要实现 DSATWorkflow 接口
class MyWorkflow(DSATWorkflow):
    async def solve(self, description, io_instructions, data_dir, output_path):
        # ...
```

**问题**:
- ❌ 暴露了内部实现细节
- ❌ 用户需要理解 DSAT 架构
- ❌ 代码冗长
- ❌ 不符合 DSLighting 2.0 理念

---

### 理想（✅ 用户只知道 DSLighting）

```python
# 用户只导入 DSLighting
from dslighting import LLMAgent, Context, Action

# 用户只需继承和实现 plan()
class MyAgent(LLMAgent):
    def __init__(self):
        super().__init__(model="gpt-4o", max_iterations=5)

    async def plan(self, context: Context) -> Action:
        # 分析数据
        data_info = self.analyze_data(context.data_dir)

        # 生成代码
        code = await self.generate_code(f"{context.task}\n\n{data_info}")

        # 执行代码
        result = await self.execute_code(code)

        # 审查并决定
        if result.success:
            return Action.success(result)
        else:
            return Action.retry(code, result.stderr)

# 使用
agent = MyAgent()
await agent.run(
    task="预测 bike demand",
    data_dir=Path("data/bike-sharing-demand"),
    output_path=Path("submission.csv")
)
```

**优势**:
- ✅ 完全隐藏 DSAT 细节
- ✅ 代码简洁
- ✅ 符合 DSLighting 2.0 理念
- ✅ 用户友好

---

## 🎯 总结

### DSAT 完整组件列表

#### Services (7个)
1. ✅ LLMService - LLM 调用
2. ✅ SandboxService - 代码执行
3. ✅ WorkspaceService - 工作区管理
4. ✅ DataAnalyzer - 数据分析
5. ✅ VDBService - 向量数据库
6. ✅ JournalState - 搜索树状态
7. ✅ Experience - 元优化状态

#### Operators (5个)
1. ✅ GenerateCodeAndPlanOperator - 生成代码和计划
2. ✅ PlanOperator - 创建结构化计划
3. ✅ ReviewOperator - 审查和评分
4. ✅ ExecuteAndTestOperator - 执行代码
5. ✅ SummarizeOperator - 生成摘要

#### Prompts (多个)
1. ✅ 通用提示词组件
2. ✅ AIDE 搜索提示词
3. ✅ Data Interpreter 提示词
4. ✅ AutoKaggle 提示词
5. ✅ DSMark 提示词

#### Workflows (多个)
1. ✅ DSATWorkflow 基类
2. ✅ AIDEWorkflow - 搜索型
3. ✅ DataInterpreterWorkflow - 计划执行型
4. ✅ AutoKaggleWorkflow - Kaggle 优化
5. ✅ DSMarkWorkflow - 深度分析
6. ✅ AutoMindWorkflow - 混合型
7. ✅ AFlowWorkflow - 元进化型

---

### DSLighting 2.0 需要做什么

1. ✅ 创建 `LLMAgent` 基类，封装所有 DSAT 服务
2. ✅ 提供 `plan()` 方法作为用户唯一需要实现的接口
3. ✅ 暴露简洁的方法：`generate_code()`, `execute_code()`, `review_output()`, `analyze_data()`
4. ✅ 提供简化状态管理：`AgentMemory`
5. ✅ 提供工具系统：`ToolRegistry`
6. ✅ 完全隐藏 DSAT 实现细节

---

**文件位置**: `/Users/liufan/Applications/Github/test_pip_dslighting/DSAT_COMPLETE_ARCHITECTURE.md`
**创建日期**: 2026-01-18
**状态**: ✅ 完整分析完成
