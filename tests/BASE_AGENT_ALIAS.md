# ✅ 完成：DSLighting 2.0 完全继承 DSAT（使用友好的别名）

## 🎯 核心改进

**现在可以使用更直观的名字了！**

### 之前的命名
```python
from dslighting import DSATWorkflow  # ← 太底层，暴露了 DSAT

class MyAgent(DSATWorkflow):  # ← 名字不直观
    pass
```

### 现在的命名（推荐）
```python
from dslighting import BaseAgent  # ✓ 更直观，符合 DSLighting 2.0！

class MyAgent(BaseAgent):  # ✓ 清晰明了
    pass
```

---

## 📋 可用的别名

DSLighting 2.0 现在提供了三个别名，都指向同一个类：

### 1. `BaseAgent`（推荐）⭐
```python
from dslighting import BaseAgent

class MyAgent(BaseAgent):
    """最直观的命名"""
    async def solve(self, description, io_instructions, data_dir, output_path):
        pass
```

### 2. `BaseWorkflow`
```python
from dslighting import BaseWorkflow

class MyAgent(BaseWorkflow):
    """强调 workflow 的概念"""
    async def solve(self, description, io_instructions, data_dir, output_path):
        pass
```

### 3. `DSATWorkflow`（原始名称）
```python
from dslighting import DSATWorkflow

class MyAgent(DSATWorkflow):
    """原始 DSAT 名称，适合知道 DSAT 的用户"""
    async def solve(self, description, io_instructions, data_dir, output_path):
        pass
```

---

## 🚀 推荐使用方式

### 方式 1: 使用 BaseAgent（最推荐）✨

```python
import dslighting
from dslighting import BaseAgent  # ← 最直观

class MyAgent(BaseAgent):  # ← 清晰明了
    """我的自定义 Agent"""

    def __init__(self, operators, services, agent_config):
        super().__init__(operators, services, agent_config)

        # 获取服务
        self.llm_service = services["llm"]
        self.sandbox_service = services["sandbox"]
        self.data_analyzer = services.get("data_analyzer")
        self.state = services["state"]

        # 获取操作器
        self.generate_op = operators["generate"]
        self.execute_op = operators["execute"]
        self.review_op = operators["review"]

    async def solve(self, description, io_instructions, data_dir, output_path):
        # 实现你的算法

        # 1. 分析数据
        data_report = self.data_analyzer.analyze(data_dir, output_path.name)

        # 2. 生成代码
        plan, code = await self.generate_op(
            system_prompt=f"Task: {description}\nData: {data_report}"
        )

        # 3. 执行代码
        result = await self.execute_op(code=code, mode="script")

        # 4. 审查结果
        review = await self.review_op(prompt_context={
            "code": code,
            "output": result.stdout
        })

        # 5. 迭代优化...
```

### 方式 2: 通过 DSLighting.Agent 使用

```python
import dslighting

# 注册后直接使用
agent = dslighting.Agent(workflow="my_agent")
result = agent.run(data="path/to/data")
```

---

## 💡 为什么使用 BaseAgent？

### 1. 更直观
```python
# ✓ 直观
class MyAgent(BaseAgent):
    pass

# ✗ 太底层
class MyAgent(DSATWorkflow):
    pass
```

### 2. 符合 DSLighting 2.0 理念
- DSLighting 2.0 的核心概念是 **Agent**
- 用户创建的是 **Agent**，不是 workflow
- `BaseAgent` 更符合这个理念

### 3. 隐藏 DSAT 实现细节
- 用户不需要知道 DSAT 的存在
- `BaseAgent` 更友好
- `DSATWorkflow` 暴露了底层框架

### 4. 灵活性
- 提供三个别名，满足不同需求
- 初级用户：`BaseAgent`
- 中级用户：`BaseWorkflow`
- 高级用户：`DSATWorkflow`

---

## 📝 完整示例

### 示例：创建搜索型 Agent

```python
import dslighting
from dslighting import (
    BaseAgent,  # ← 使用友好的别名！
    JournalState,
    Node,
    MetricValue,
)
from pathlib import Path

class IntelligentSearchAgent(BaseAgent):  # ← 更清晰
    """智能搜索 Agent"""

    def __init__(self, operators, services, agent_config):
        super().__init__(operators, services, agent_config)

        self.llm_service = services["llm"]
        self.sandbox_service = services["sandbox"]
        self.data_analyzer = services.get("data_analyzer")
        self.state: JournalState = services["state"]

        self.generate_op = operators["generate"]
        self.execute_op = operators["execute"]
        self.review_op = operators["review"]

    async def solve(self, description, io_instructions, data_dir, output_path):
        """实现智能搜索算法"""

        # 1. 分析数据
        if self.data_analyzer:
            data_report = self.data_analyzer.analyze(data_dir, output_path.name)

        # 2. 迭代搜索
        max_iterations = self.agent_config.get("max_iterations", 5)

        for i in range(max_iterations):
            # 选择节点
            parent = self._select_node()

            # 生成代码
            if parent is None:
                from dsat.prompts.common import create_draft_prompt
                prompt = create_draft_prompt(
                    {"goal_and_data": f"{description}\n\n{data_report}"},
                    self.state.generate_summary()
                )
            elif parent.is_buggy:
                from dsat.prompts.aide_prompt import create_debug_prompt
                prompt = create_debug_prompt(
                    {"goal_and_data": description},
                    parent.code,
                    self._get_error_history(parent),
                    memory_summary=self.state.generate_summary()
                )
            else:
                from dsat.prompts.aide_prompt import create_improve_prompt
                from dsat.utils.context import summarize_repetitive_logs
                prompt = create_improve_prompt(
                    {"goal_and_data": description},
                    self.state.generate_summary(),
                    parent.code,
                    parent.analysis,
                    previous_output=summarize_repetitive_logs(parent.term_out)
                )

            # 生成代码
            plan, code = await self.generate_op(system_prompt=prompt)

            # 创建节点
            new_node = Node(plan=plan, code=code)

            # 执行代码
            result = await self.execute_op(code=code, mode="script")
            new_node.absorb_exec_result(result)

            # 审查结果
            if result.success:
                review = await self.review_op(prompt_context={
                    "task": description,
                    "code": code,
                    "output": result.stdout
                })
                new_node.analysis = review.summary
                new_node.metric = MetricValue(
                    value=review.metric_value or 0.0,
                    maximize=not review.lower_is_better
                )
                new_node.is_buggy = review.is_buggy
            else:
                new_node.is_buggy = True

            # 添加到状态树
            self.state.append(new_node, parent)

        # 3. 使用最佳节点
        best = self.state.get_best_node()
        if best:
            await self.execute_op(code=best.code, mode="script")

    def _select_node(self):
        if len(self.state) == 0:
            return None
        successful = [n for n in self.state.nodes.values() if not n.is_buggy]
        if not successful:
            return list(self.state.nodes.values())[-1]
        return min(successful, key=lambda n: n.metric.value or float('inf'))

    def _get_error_history(self, node, max_depth=3):
        history = []
        current = node
        depth = 0
        while current and current.is_buggy and depth < max_depth:
            history.append(f"Step #{current.step}: {current.plan}\nError: {current.exc_type}")
            depth += 1
            current = self.state.get_node(current.parent_id) if current.parent_id else None
        return "\n".join(reversed(history)) if history else "No error history"
```

---

## 🎯 总结

### 三个别名，三个用途

1. **`BaseAgent`** ⭐ - **推荐用于所有 DSLighting 2.0 用户**
   - 最直观
   - 符合 DSLighting 2.0 理念
   - 隐藏 DSAT 实现细节

2. **`BaseWorkflow`** - 适合强调 workflow 概念
   - 更灵活
   - 强调流程而非 Agent

3. **`DSATWorkflow`** - 适合高级用户
   - 暴露底层框架
   - 熟悉 DSAT 的用户

### 推荐使用

```python
# ✓ 推荐：使用 BaseAgent
from dslighting import BaseAgent

class MyAgent(BaseAgent):
    pass
```

### 这就是您想要的！

- ✅ **友好的命名**：`BaseAgent` 而不是 `DSATWorkflow`
- ✅ **完全继承 DSAT**：所有能力都保留
- ✅ **灵活的选择**：提供三个别名满足不同需求
- ✅ **更符合 DSLighting 2.0**：用户友好的 API

---

**状态**: ✅ 完成！现在可以使用 `BaseAgent` 了！

**修改文件**: `/Users/liufan/Applications/Github/dslighting/dslighting/__init__.py`
