# DSLighting v1.9.11 发布说明

## 🎉 新功能

### API Key 多轮转支持

**功能描述：**
新增完整的 API key 轮转机制，支持配置多个 API key 并自动轮转使用，提供更好的负载均衡和故障转移能力。

**核心特性：**
- ✅ 支持多个 API key 配置（列表格式）
- ✅ 自动 Round-Robin 轮转
- ✅ 故障自动转移（当前 key 失败时切换到下一个）
- ✅ 线程安全的 key 管理器
- ✅ 完全向后兼容单一 key 配置

---

## 📖 配置方式

### 方式 1：环境变量 LLM_MODEL_CONFIGS（推荐）

在 `.env` 文件中配置多个模型，每个模型支持多个 API key：

```bash
LLM_MODEL_CONFIGS='{
  "glm-4.7": {
    "api_key": ["sk-key1...", "sk-key2...", "sk-key3..."],
    "api_base": "https://open.bigmodel.cn/api/paas/v4",
    "temperature": 1.0,
    "provider": "openai"
  },
  "openai/deepseek-ai/DeepSeek-V3": {
    "api_key": ["sk-ds1...", "sk-ds2...", "sk-ds3..."],
    "api_base": "https://api.siliconflow.cn/v1",
    "temperature": 1.0
  },
  "gpt-4o": {
    "api_key": "sk-single-key...",
    "api_base": "https://api.openai.com/v1",
    "temperature": 0.7
  }
}'
```

### 方式 2：代码中配置

```python
import dslighting

# 多个 key（支持轮转）
agent = dslighting.Agent(
    workflow="aide",
    model="gpt-4o",
    api_keys=["sk-key1...", "sk-key2...", "sk-key3..."],
    api_base="https://api.openai.com/v1"
)

# 单个 key（向后兼容）
agent = dslighting.Agent(
    workflow="aide",
    model="gpt-4o",
    api_key="sk-single-key...",
    api_base="https://api.openai.com/v1"
)
```

---

## 🔧 配置优先级

当存在多种配置方式时，优先级从高到低为：

1. **代码参数**（`agent(api_keys=[...])`）
2. **LLM_MODEL_CONFIGS** 中的模型配置
3. **简单环境变量**（`API_KEY`, `LLM_MODEL` 等）
4. **默认配置**

---

## 💡 使用示例

### 示例 1：硅基流动（SiliconFlow）多 key

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

# 自动轮转使用多个 key
agent = dslighting.Agent(model="openai/deepseek-ai/DeepSeek-V3")
result = agent.run(data)
```

### 示例 2：多个 Provider 混合配置

```bash
# .env
LLM_MODEL_CONFIGS='{
  "gpt-4o": {
    "api_key": ["sk-openai-1...", "sk-openai-2..."],
    "api_base": "https://api.openai.com/v1"
  },
  "claude-3-5-sonnet": {
    "api_key": ["sk-ant-1...", "sk-ant-2..."],
    "api_base": "https://api.anthropic.com/v1"
  }
}'
```

### 示例 3：手动控制 key 轮转

```python
import dslighting
from dslighting.core.api_key_manager import APIKeyManager

# 初始化 agent
agent = dslighting.Agent(
    workflow="aide",
    model="gpt-4o",
    api_keys=["sk-key1...", "sk-key2...", "sk-key3..."]
)

# 获取 key 管理器
manager = APIKeyManager.get_manager("gpt-4o", ["sk-key1...", "sk-key2...", "sk-key3..."])

# 查看当前 key
print(f"当前 key: {manager.get_current_key()}")

# 手动轮转到下一个 key
next_key = manager.rotate_key()
print(f"下一个 key: {next_key}")

# 标记当前 key 失败并轮转
new_key = manager.mark_key_failed()
print(f"故障转移后: {new_key}")
```

---

## 🔍 技术细节

### 修改的文件（3 个）

1. **`dsat/config.py`** - LLMConfig 模型
   - 新增 `api_keys` 字段（支持列表）
   - 新增 `get_api_keys()` 方法（统一获取接口）
   - 保持向后兼容（`api_key` 字段）

2. **`dslighting/core/config_builder.py`** - 配置构建器
   - 完善 `_load_model_configs()` 方法
   - 自动将 `api_key` 列表转换为 `api_keys`
   - 添加 placeholder key 检测（"your_key"）

3. **`dslighting/core/api_key_manager.py`** - 新增 Key 管理器
   - `APIKeyManager` 类（线程安全）
   - Round-Robin 轮转算法
   - 故障转移机制
   - 按模型管理 key

### 新增功能

```python
# LLMConfig 新增方法
class LLMConfig(BaseModel):
    api_keys: Optional[List[str]] = None

    def get_api_keys(self) -> List[str]:
        """获取 key 列表，优先级: api_keys > api_key > []"""
        if self.api_keys:
            return self.api_keys
        elif self.api_key:
            return [self.api_key]
        else:
            return []

# APIKeyManager 核心方法
APIKeyManager.get_manager(model_name, api_keys)  # 获取/创建管理器
manager.get_current_key()  # 获取当前 key
manager.rotate_key()  # 轮转到下一个
manager.mark_key_failed()  # 标记失败并轮转
manager.get_all_keys()  # 获取所有 key
manager.reset(new_keys)  # 重置 key 列表
```

---

## 📋 从 v1.9.10 升级

### 升级步骤

```bash
# 升级到最新版本
pip install --upgrade dslighting==1.9.11
```

### 兼容性
- ✅ 完全向后兼容 v1.9.10
- ✅ 无需修改现有代码
- ✅ 所有 API 保持不变
- ✅ 单一 key 配置继续工作

---

## 🚀 高级特性

### 线程安全

```python
# 多线程环境下安全使用
from concurrent.futures import ThreadPoolExecutor
from dslighting.core.api_key_manager import APIKeyManager

def run_agent(data):
    agent = dslighting.Agent(
        workflow="aide",
        model="gpt-4o",
        api_keys=["sk-key1...", "sk-key2..."]
    )
    return agent.run(data)

# 多线程并发执行
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(run_agent, datasets))
```

### 动态更新 keys

```python
from dslighting.core.api_key_manager import APIKeyManager

manager = APIKeyManager.get_manager("gpt-4o", ["sk-key1...", "sk-key2..."])

# 动态添加新 key
new_keys = ["sk-key1...", "sk-key2...", "sk-key3...", "sk-key4..."]
manager.reset(new_keys)
```

---

## 📚 文档更新

### 新增文档

- **`PIP_DOC/API_KEY_ROTATION.md`** - API Key 轮转完整指南
  - 配置方式说明
  - 详细使用示例
  - 最佳实践
  - 常见问题解答
  - 故障排除指南

---

## 📊 统计数据

### 代码改动
- **新增文件：** 1 个（`api_key_manager.py`）
- **修改文件：** 3 个
- **新增文档：** 1 个
- **代码行数：** +220 行（含文档）

### 功能亮点
- ✅ 多 API key 轮转
- ✅ 故障自动转移
- ✅ 线程安全
- ✅ 向后兼容
- ✅ 详细日志

---

## 🎯 使用场景

### 场景 1：生产环境高可用

```bash
# 配置多个 OpenAI key，避免单点故障
LLM_MODEL_CONFIGS='{
  "gpt-4o": {
    "api_key": [
      "sk-account1-key...",
      "sk-account2-key...",
      "sk-account3-key..."
    ],
    "api_base": "https://api.openai.com/v1"
  }
}'
```

### 场景 2：配额管理

```bash
# 多个 key 分担请求压力
LLM_MODEL_CONFIGS='{
  "openai/deepseek-ai/DeepSeek-V3": {
    "api_key": [
      "sk-siliconflow-1...",
      "sk-siliconflow-2...",
      "sk-siliconflow-3...",
      "sk-siliconflow-4...",
      "sk-siliconflow-5..."
    ],
    "api_base": "https://api.siliconflow.cn/v1"
  }
}'
```

### 场景 3：混合 Provider

```bash
# 同时使用多个 provider
LLM_MODEL_CONFIGS='{
  "gpt-4o": {
    "api_key": ["sk-openai-1...", "sk-openai-2..."],
    "api_base": "https://api.openai.com/v1"
  },
  "claude-3-5-sonnet": {
    "api_key": ["sk-ant-1...", "sk-ant-2..."],
    "api_base": "https://api.anthropic.com/v1"
  },
  "glm-4.7": {
    "api_key": ["your-zhipu-key..."],
    "api_base": "https://open.bigmodel.cn/api/paas/v4",
    "provider": "openai"
  }
}'
```

---

## 📝 最佳实践

### 1. Key 数量建议
- **开发环境**：1-2 个 key
- **测试环境**：2-3 个 key
- **生产环境**：3-5 个 key
- **高并发场景**：5-10 个 key

### 2. Key 来源多样化
- 从不同账户获取 key
- 使用不同的 provider
- 避免所有 key 共享配额

### 3. 监控和日志
```python
import logging
logging.basicConfig(level=logging.INFO)

# 查看轮转日志
# INFO: APIKeyManager initialized for 'gpt-4o' with 3 keys
# INFO: Rotated API key for 'gpt-4o'. Remaining keys: 3
```

---

## 🔗 相关链接

- **GitHub:** https://github.com/usail-hkust/dslighting
- **PyPI:** https://pypi.org/project/dslighting/
- **文档:** https://luckyfan-cs.github.io/dslighting-web/
- **v1.9.10 发布说明:** 见 `PIP_DOC/RELEASE_NOTES_v1.9.10.md`

---

## 🙏 致谢

感谢用户反馈和建议！

---

**发布日期：** 2026-01-18
**版本：** v1.9.11
**上一个版本：** v1.9.10
**状态：** ✅ 稳定发布
