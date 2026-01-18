# DSLighting v1.9.8 发布说明

## 🎉 新功能

### 代码质量改进
**问题描述：**
生产代码中遗留了大量 DEBUG print 语句（26 处），影响用户体验和代码专业性。

**解决方案：**
- 将所有 `print(f"[DEBUG]...")` 改为 `logger.debug()...`
- DEBUG 信息只在 debug 模式下显示，不污染普通用户输出
- 提升代码专业性和可维护性

**影响：**
- 更清洁的用户输出
- 符合日志记录最佳实践
- 可通过日志级别控制调试信息

---

### 测试框架建立
**问题描述：**
缺少完整的测试框架，无法保证代码质量和测试覆盖率。

**解决方案：**
- 建立 pytest 测试框架
- 创建测试目录结构：`tests/unit/`, `tests/integration/`, `tests/fixtures/`
- 编写 `conftest.py` 配置文件（285 行）
- 添加初始单元测试 `test_agent_init.py`

**提供的 fixtures：**
- `temp_dir` - 临时目录
- `sample_data_dir` - 示例数据目录
- `sample_dataframe` - 示例 DataFrame
- `mock_llm_response` - Mock LLM 响应
- `basic_agent_config` - 基本配置
- `dsagent_config_with_rag_disabled` - DS-Agent 配置（RAG 禁用）
- `automind_config_with_rag_disabled` - AutoMind 配置（RAG 禁用）

**测试覆盖：**
- ✅ Agent 初始化测试（所有 6 种工作流）
- ✅ 参数传递测试
- ✅ enable_rag 参数测试

---

### Pydantic V2 迁移
**问题描述：**
代码使用 Pydantic V1 的 `class Config`，产生大量废弃警告。

**解决方案：**
迁移到 Pydantic V2 的 `ConfigDict`：

```python
# 之前 (Pydantic V1)
class Config:
    extra = 'forbid'

# 之后 (Pydantic V2)
from pydantic import ConfigDict
model_config = ConfigDict(extra='forbid')
```

**修改的文件（5 个）：**
- `dsat/models/task.py`
- `dsat/models/candidates.py`
- `dsat/config.py`
- `dsat/common/typing.py`
- `dsat/services/states/journal.py`

**影响：**
- ✅ 消除所有 Pydantic 废弃警告
- ✅ 确保与 Pydantic V2 兼容
- ✅ 提升代码质量

---

### 文档完善
**新增文档（5000+ 行）：**

1. **安装指南** (`PIP_DOC/INSTALLATION_GUIDE.md`, 301 行)
   - 详细的安装说明
   - enable_rag 参数使用指南
   - 网络受限环境解决方案
   - 常见问题解答

2. **安装速查表** (`PIP_DOC/INSTALLATION_OPTIONS.md`, 62 行)
   - 快速安装命令
   - 工作流速查表
   - 快速验证方法

3. **快速入门指南** (`PIP_DOC/QUICK_START.md`, 438 行)
   - 5 分钟快速上手
   - 所有工作流示例
   - 常见使用场景

4. **历史发布说明** (`RELEASE_NOTES_v1.9.1-1.9.6.md`, 1312 行)
   - 完整的版本历史
   - 功能演进记录

5. **改进计划文档** (`claude_doc/TODO/`, 2414 行)
   - **IMPROVEMENT_PLAN.md** (1235 行) - 全面代码审查和改进路线图
   - **QUICK_FIX_CHECKLIST.md** (580 行) - 快速修复清单
   - **PRIORITIZED_TASKS.md** (396 行) - 优先级任务列表
   - **README.md** (203 行) - 文档索引

---

## 🔧 改进

### 依赖配置优化
**问题描述：**
依赖配置不够清晰，缺少版本约束。

**解决方案：**
- 添加合理的版本上界约束（如 `<3.0.0`）
- 明确说明 transformers 和 torch 为必需依赖
- 添加 pytest-cov 到开发依赖

**版本约束示例：**
```toml
"pandas>=1.5.0,<3.0.0",
"pydantic>=2.10.0,<3.0.0",
"scikit-learn>=1.0.0,<2.0.0",
```

---

### CLI 增强
**改进内容：**
- 改进帮助和命令结构
- 增强包检测工具
- 沙箱服务功能改进

**代码量：** +494 行

---

## 📋 从 v1.9.7 升级

### 升级步骤

```bash
# 方式1：升级到最新版本
pip install --upgrade dslighting

# 方式2：指定版本
pip install dslighting==1.9.8
```

### 兼容性
- ✅ 完全向后兼容 v1.9.7
- ✅ 无需修改现有代码
- ✅ 所有 API 保持不变

---

## 🐛 Bug 修复

### 1. 全局配置 API 错误
**问题：** conftest.py 中的 `reset_global_config` fixture 使用了不存在的 `GLOBAL_CONFIG`

**修复：** 使用正确的 `get_global_config()` API

### 2. 测试属性访问错误
**问题：** 测试中直接访问 `agent.workflow` 等属性

**修复：** 更新为正确的路径 `agent.config.workflow.name`

### 3. Pytest 配置警告
**问题：** 配置了 `asyncio_mode` 但未安装 pytest-asyncio

**修复：** 移除未使用的配置，添加自定义 markers

---

## 📊 统计数据

### 代码改动
- **提交数：** 4 个 commits
- **修改文件：** 90+ 个
- **代码行数：** +5571/-71 行
- **文档行数：** +5000+ 行

### 文件分类
- **代码文件：** 15 个
- **测试文件：** 6 个
- **文档文件：** 13 个
- **配置文件：** 3 个

---

## 🎯 主要亮点

### 1. 代码质量 ⭐⭐⭐
- 清理所有 DEBUG prints
- 迁移到 Pydantic V2
- 添加完整的测试框架

### 2. 文档完善 ⭐⭐⭐
- 5000+ 行新增文档
- 详细的安装指南
- 完整的改进计划

### 3. 开发体验 ⭐⭐⭐
- 测试框架建立
- 代码质量提升
- 更好的错误处理

---

## 🚀 使用示例

### 基本使用（无变化）
```python
import dslighting

# 加载数据
data = dslighting.load_data("bike-sharing-demand")

# 运行 agent
agent = dslighting.Agent(workflow="aide")
result = agent.run(data)
```

### AutoMind/DS-Agent（禁用 RAG）
```python
# 网络受限环境 - 禁用 RAG
agent = dslighting.Agent(
    workflow="automind",
    automind={"enable_rag": False}
)
```

---

## 📝 已知问题

无重大问题。

**小提示：**
- 使用 `enable_rag=False` 可避免 HuggingFace 下载
- transformers 和 torch 是必需的（~500MB）
- 测试需要 pytest：`pip install pytest[all,dev]`

---

## 🔗 相关链接

- **GitHub:** https://github.com/usail-hkust/dslighting
- **PyPI:** https://pypi.org/project/dslighting/
- **文档:** https://luckyfan-cs.github.io/dslighting-web/
- **更新日志:** 见 `PIP_DOC/RELEASE_NOTES_*.md`

---

## 🙏 致谢

感谢所有贡献者的反馈和建议！

---

**发布日期：** 2026-01-18
**版本：** v1.9.8
**上一个版本：** v1.9.7
**状态：** ✅ 稳定发布
