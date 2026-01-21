# 直接使用 DSLighting 2.0 BaseAgent - 不需要注册！

## ✅ 正确理解

您说得完全对！用户**不需要修改源代码**，**不需要注册**，就可以直接使用 BaseAgent！

## 🎯 DSLighting 2.0 核心协议

DSLighting 2.0 提供了核心协议，用户可以直接继承和使用：

```python
from dslighting import BaseAgent, Action, Context, Tool
from dslighting.core.agent import Agent

class MyAgent(Agent):  # 直接继承 Agent
    """
    我的自定义 Agent
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 自定义初始化

    def run(self, data, **kwargs):
        """
        运行 Agent
        """
        # 使用父类的 LLM、Sandbox 等能力
        return super().run(data, **kwargs)
```

## 📝 三种使用方式

### 方式1: 直接实例化（最简单）✅

```python
import dslighting
from intelligent_llm_agent.agent import MyIntelligentAgent

# 创建 Agent
agent = MyIntelligentAgent(
    model="gpt-4o",
    temperature=0.7,
    max_iterations=5
)

# 加载数据
data = dslighting.load_data("bike-sharing-demand")

# 运行
result = agent.run(data)
print(f"Score: {result.score}")
```

**优点**:
- ✅ 不需要修改任何源代码
- ✅ 直接使用
- ✅ 继承所有 DSLighting 功能（LLM、Sandbox、Evaluator）

### 方式2: 作为自定义 workflow ⚠️

这需要注册，但**不是必须的**！

```python
# 这需要注册到 factory.py
agent = dslighting.Agent(
    workflow="my_custom_agent",  # 需要注册
    model="gpt-4o"
)
```

**用户不注册就无法使用这种方式**，但还有方式1可以用！

### 方式3: 使用 BaseAgent Protocol（最灵活）✅

```python
from dslighting import BaseAgent, Action, Context, Tool

class MyAgent:
    """实现 BaseAgent 协议"""
    def __init__(self):
        self.tools = {...}

    def plan(self, ctx: Context) -> Action:
        """
        核心方法：决定下一步动作
        """
        # 使用 LLM 决策
        tool_name = self._ask_llm(ctx)

        return Action(tool=tool_name, args={...})

    def run(self, data):
        """运行 Agent"""
        # 创建 Context
        ctx = Context(task="...", data=data, tools=self.tools)

        # 循环规划和执行
        while not done:
            action = self.plan(ctx)
            self._execute(action)

        return result
```

## 🔧 具体实现对比

### ❌ 错误理解：必须注册

```python
# ❌ 这样想是错的
"用户必须注册才能使用自定义 Agent"
```

### ✅ 正确理解：直接继承

```python
# ✅ 正确：直接继承 Agent
class MyAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

# 直接使用
agent = MyAgent(model="gpt-4o")
result = agent.run(data)
```

## 🎓 BaseAgent vs Agent

### BaseAgent（Protocol）
```python
from dslighting import BaseAgent

# 只是一个接口定义
class MyAgent:
    def plan(self, ctx: Context) -> Action:
        ...
```

**用途**: 定义 Agent 的接口规范

### Agent（具体实现）
```python
from dslighting.core.agent import Agent

# 完整的 Agent 实现，包含：
# - LLM 集成
# - Sandbox 执行
# - Evaluator 评估
# - Workspace 管理

class MyAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
```

**用途**: 继承所有 DSLighting 能力

## 💡 实际使用建议

### 推荐方式：继承 Agent

```python
from dslighting.core.agent import Agent

class MyIntelligentAgent(Agent):
    """
    我的智能 Agent

    继承 Agent，自动获得：
    - ✓ LLM 服务
    - ✓ Sandbox 执行
    - ✓ 评估器
    - ✓ 工作区管理
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 自定义初始化

    def run(self, data, **kwargs):
        """运行逻辑"""
        # 使用父类的完整流程
        return super().run(data, **kwargs)

# 使用
agent = MyIntelligentAgent(model="gpt-4o")
result = agent.run(data)
```

### 极简方式：只使用核心协议

```python
from dslighting import BaseAgent, Action, Context

class SimpleAgent:
    """极简 Agent"""
    def plan(self, ctx: Context) -> Action:
        # 决策逻辑
        return Action(tool="...", args={...})

# 使用
agent = SimpleAgent()
action = agent.plan(context)
```

## 📊 总结

| 特性 | 继承 Agent | 实现 BaseAgent Protocol |
|------|-----------|----------------------|
| **需要注册** | ❌ 不需要 | ❌ 不需要 |
| **LLM 支持** | ✅ 自动继承 | ⚠️ 需要自己实现 |
| **Sandbox** | ✅ 自动继承 | ⚠️ 需要自己实现 |
| **复杂度** | 低 | 中 |
| **灵活性** | 中 | 高 |
| **推荐** | ✅ 是 | ⚠️ 高级用户 |

## 🚀 快速开始

### 立即使用（不需要注册）

```python
# 1. 导入
import dslighting
from intelligent_llm_agent.agent import MyIntelligentAgent

# 2. 创建
agent = MyIntelligentAgent(model="gpt-4o")

# 3. 运行
data = dslighting.load_data("bike-sharing-demand")
result = agent.run(data)

# 4. 结果
print(f"Score: {result.score}")
```

**就这么简单！不需要注册，不需要修改源代码！**

## ✨ 关键点

1. **BaseAgent** 是一个 Protocol（接口定义）
2. **Agent** 是具体实现，包含所有功能
3. **用户可以**：
   - ✅ 直接继承 `Agent`
   - ✅ 实现 `BaseAgent` Protocol
   - ✅ 不需要注册就能使用
4. **注册只是**：
   - 为了使用 `Agent(workflow="my_agent")` 这种语法
   - 但这不是唯一方式！

## 🎯 结论

**您的理解完全正确**：

> "如果用户都要注册，那么他无法改源代码不可能注册啊"

对！用户**不需要注册**，可以直接：
1. 继承 `Agent` 类
2. 实现自定义逻辑
3. 直接使用

**注册只是可选的便利功能**，不是必须的！

---

**文件位置**:
- Agent 实现: `/Users/liufan/Applications/Github/test_pip_dslighting/intelligent_llm_agent/agent.py`
- 测试文件: `/Users/liufan/Applications/Github/test_pip_dslighting/test_intelligent_agent.py`
