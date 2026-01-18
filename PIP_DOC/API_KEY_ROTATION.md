# API Key Rotation - 使用指南

## 概述

DSLighting 支持多个 API key 轮转使用，提供以下优势：

- ✅ **负载均衡**：多个 key 分担请求压力
- ✅ **故障转移**：一个 key 失败自动切换到下一个
- ✅ **配额管理**：避免单个 key 达到速率限制
- ✅ **高可用性**：提高整体服务的可用性

## 配置方式

### 方式 1：环境变量配置（推荐）

在 `.env` 文件中配置 `LLM_MODEL_CONFIGS`：

```bash
# .env 文件
LLM_MODEL_CONFIGS='{
  "glm-4.7": {
    "api_key": ["sk-key1...", "sk-key2...", "sk-key3..."],
    "api_base": "https://open.bigmodel.cn/api/paas/v4",
    "temperature": 1.0,
    "provider": "openai"
  },
  "openai/deepseek-ai/DeepSeek-V3": {
    "api_key": ["sk-ds1...", "sk-ds2..."],
    "api_base": "https://api.siliconflow.cn/v1",
    "temperature": 1.0
  },
  "gpt-4o": {
    "api_key": "sk-openai-single-key...",
    "api_base": "https://api.openai.com/v1",
    "temperature": 0.7
  }
}'
```

### 方式 2：代码中直接配置

```python
import dslighting

# 方式 2a: 使用 api_keys 参数
agent = dslighting.Agent(
    workflow="aide",
    model="gpt-4o",
    api_keys=["sk-key1...", "sk-key2...", "sk-key3..."],  # 多个 key
    api_base="https://api.openai.com/v1"
)

# 方式 2b: 单个 key（向后兼容）
agent = dslighting.Agent(
    workflow="aide",
    model="gpt-4o",
    api_key="sk-key1...",  # 单个 key
    api_base="https://api.openai.com/v1"
)
```

## 配置优先级

当存在多种配置方式时，优先级从高到低为：

1. **代码参数**（`agent(api_keys=[...])`）
2. **LLM_MODEL_CONFIGS** 中的模型配置
3. **简单环境变量**（`API_KEY`, `LLM_MODEL` 等）
4. **默认配置**

## 详细示例

### 示例 1：多个 provider 的 key 轮转

```bash
# .env
LLM_MODEL_CONFIGS='{
  "gpt-4o": {
    "api_key": ["sk-key1...", "sk-key2...", "sk-key3..."],
    "api_base": "https://api.openai.com/v1"
  },
  "claude-3-5-sonnet": {
    "api_key": ["sk-ant-1...", "sk-ant-2..."],
    "api_base": "https://api.anthropic.com/v1"
  }
}'
```

```python
import dslighting

# 使用 GPT-4o（会自动轮转 3 个 key）
agent1 = dslighting.Agent(model="gpt-4o")

# 使用 Claude（会自动轮转 2 个 key）
agent2 = dslighting.Agent(model="claude-3-5-sonnet")
```

### 示例 2：硅基流动（SiliconFlow）多 key

```bash
# .env
LLM_MODEL_CONFIGS='{
  "openai/deepseek-ai/DeepSeek-V3": {
    "api_key": [
      "sk-siliconflow-key1...",
      "sk-siliconflow-key2...",
      "sk-siliconflow-key3..."
    ],
    "api_base": "https://api.siliconflow.cn/v1",
    "temperature": 1.0
  }
}'
```

```python
import dslighting

# 自动轮转使用 SiliconFlow 的多个 key
agent = dslighting.Agent(model="openai/deepseek-ai/DeepSeek-V3")
```

### 示例 3：混合配置（部分模型多 key，部分单 key）

```bash
# .env
LLM_MODEL_CONFIGS='{
  "glm-4.7": {
    "api_key": ["sk-key1...", "sk-key2..."],
    "api_base": "https://open.bigmodel.cn/api/paas/v4",
    "temperature": 1.0
  },
  "gpt-4o-mini": {
    "api_key": "sk-single-key...",
    "api_base": "https://api.openai.com/v1"
  }
}'
```

```python
import dslighting

# GLM-4.7 会轮转 2 个 key
agent1 = dslighting.Agent(model="glm-4.7")

# GPT-4o-mini 使用单个 key
agent2 = dslighting.Agent(model="gpt-4o-mini")
```

## API Key 轮转机制

### 自动轮转

DSLighting 实现了智能的 API key 轮转机制：

1. **Round-Robin 轮转**：按顺序轮流使用每个 key
2. **故障转移**：当前 key 失败时自动切换到下一个
3. **线程安全**：多线程环境下安全使用

### 轮转策略

```python
from dslighting.core.api_key_manager import APIKeyManager

# 获取某个模型的 key 管理器
manager = APIKeyManager.get_manager(
    model_name="gpt-4o",
    api_keys=["sk-key1...", "sk-key2...", "sk-key3..."]
)

# 获取当前 key
current_key = manager.get_current_key()  # "sk-key1..."

# 手动轮转到下一个 key
next_key = manager.rotate_key()  # "sk-key2..."

# 标记当前 key 失败并轮转
new_key = manager.mark_key_failed()  # "sk-key3..."
```

## 高级用法

### 自定义轮转逻辑

```python
import dslighting
from dslighting.core.api_key_manager import APIKeyManager

# 初始化多个 key
agent = dslighting.Agent(
    workflow="aide",
    model="gpt-4o",
    api_keys=["sk-key1...", "sk-key2...", "sk-key3..."]
)

# 在代码中访问 key 管理器
manager = APIKeyManager.get_manager("gpt-4o", ["sk-key1...", "sk-key2...", "sk-key3..."])

# 监控 key 使用情况
print(f"当前 key: {manager.get_current_key()}")
print(f"剩余 key 数量: {len(manager.get_all_keys())}")

# 如果某个请求失败，手动轮转
new_key = manager.mark_key_failed()
print(f"轮转后的 key: {new_key}")
```

### 动态更新 keys

```python
from dslighting.core.api_key_manager import APIKeyManager

# 获取现有管理器
manager = APIKeyManager.get_manager("gpt-4o", ["sk-key1...", "sk-key2..."])

# 添加新的 key（重置管理器）
new_keys = ["sk-key1...", "sk-key2...", "sk-key3...", "sk-key4..."]
manager.reset(new_keys)
print(f"更新后的 key 数量: {len(manager.get_all_keys())}")
```

## 最佳实践

### 1. Key 数量建议

- **少量使用**：2-3 个 key
- **生产环境**：3-5 个 key
- **高并发**：5-10 个 key

### 2. Key 来源多样化

```bash
# 建议从不同账户或不同 provider 获取 key
LLM_MODEL_CONFIGS='{
  "gpt-4o": {
    "api_key": [
      "sk-account1-key1...",  # 账户 1
      "sk-account2-key1...",  # 账户 2
      "sk-account3-key1..."   # 账户 3
    ],
    "api_base": "https://api.openai.com/v1"
  }
}'
```

### 3. 错误处理

```python
import dslighting
from dslighting.core.api_key_manager import APIKeyManager

try:
    agent = dslighting.Agent(
        workflow="aide",
        model="gpt-4o",
        api_keys=["sk-key1...", "sk-key2...", "sk-key3..."]
    )
    result = agent.run(data)
except Exception as e:
    # 获取管理器并轮转 key
    manager = APIKeyManager.get_manager("gpt-4o", ["sk-key1...", "sk-key2...", "sk-key3..."])
    manager.mark_key_failed()
    print(f"Key 轮转成功，新 key: {manager.get_current_key()}")
```

### 4. 监控和日志

```python
import logging

# 启用调试日志查看 key 轮转
logging.basicConfig(level=logging.INFO)

agent = dslighting.Agent(
    workflow="aide",
    model="gpt-4o",
    api_keys=["sk-key1...", "sk-key2...", "sk-key3..."]
)

# 运行时会在日志中看到：
# INFO: APIKeyManager initialized for 'gpt-4o' with 3 keys
# INFO: Rotated API key for 'gpt-4o'. Remaining keys: 3
```

## 常见问题

### Q1: 如何验证 key 轮转是否生效？

A: 启用调试日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)

agent = dslighting.Agent(
    workflow="aide",
    model="gpt-4o",
    api_keys=["sk-key1...", "sk-key2..."]
)
```

### Q2: 所有 key 都失败了怎么办？

A: 系统会尝试所有 key，如果全部失败会抛出异常。建议：

1. 配置足够数量的 key
2. 实现重试逻辑
3. 监控 key 使用状态

### Q3: 可以混合使用不同 provider 的 key 吗？

A: 不建议。同一个模型的 key 应该来自同一个 provider，但可以配置多个模型使用不同 provider：

```bash
LLM_MODEL_CONFIGS='{
  "gpt-4o": {
    "api_key": ["sk-key1...", "sk-key2..."],
    "api_base": "https://api.openai.com/v1"
  },
  "claude-3-5-sonnet": {
    "api_key": ["sk-ant-1...", "sk-ant-2..."],
    "api_base": "https://api.anthropic.com/v1"
  }
}'
```

### Q4: api_key 和 api_keys 有什么区别？

A:
- `api_key`：单个 key（字符串）
- `api_keys`：多个 key（列表），支持轮转
- 优先级：`api_keys` > `api_key`

### Q5: 如何临时禁用某个 key？

A: 从配置中移除该 key，或使用 `reset()` 方法更新 key 列表：

```python
from dslighting.core.api_key_manager import APIKeyManager

manager = APIKeyManager.get_manager("gpt-4o", ["sk-key1...", "sk-key2...", "sk-key3..."])

# 移除第一个 key
new_keys = ["sk-key2...", "sk-key3..."]
manager.reset(new_keys)
```

## 向后兼容性

✅ 完全兼容旧的单一 key 配置方式：

```python
# 旧方式（仍然支持）
agent = dslighting.Agent(
    workflow="aide",
    model="gpt-4o",
    api_key="sk-single-key..."
)

# 新方式（推荐）
agent = dslighting.Agent(
    workflow="aide",
    model="gpt-4o",
    api_keys=["sk-key1...", "sk-key2..."]
)
```

## 相关文档

- [安装指南](INSTALLATION_GUIDE.md)
- [快速开始](QUICK_START.md)
- [配置说明](../README.md)

---

**版本**: v1.9.11+
**更新日期**: 2026-01-18
