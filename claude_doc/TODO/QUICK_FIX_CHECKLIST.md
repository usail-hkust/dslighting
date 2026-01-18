# DSLighting v1.9.7+ 快速修复清单

**创建时间：** 2026-01-18
**目标版本：** v1.9.8 或 v1.10.0
**预计总工作量：** 2-4 周

---

## ⚡ 立即可执行的任务（< 1 小时）

### 1. 移除 DEBUG print 语句 🔴 最高优先级
**文件：** `dslighting/core/agent.py`
**行数：** 335-591（约 26 处）
**工作量：** 30 分钟

**步骤：**
```bash
# 1. 搜索所有 DEBUG 语句
grep -n "\[DEBUG\]" dslighting/core/agent.py

# 2. 删除或替换为 logger.debug()
# 示例：
# print(f"[DEBUG] Loading data...")
# 改为：
# self.logger.debug(f"Loading data...")

# 3. 验证
grep -r "\[DEBUG\]" dslighting/
# 应该返回空（除了 registry 目录下的 prepare.py）
```

**验证方法：**
```bash
# 运行一个简单测试
python -c "
import dslighting
agent = dslighting.Agent(workflow='aide')
print('✅ Agent 初始化成功')
"
```

---

## 📅 本周任务（1-3 天）

### 2. 创建自定义异常类
**文件：** `dslighting/exceptions.py`（新建）
**工作量：** 1 小时

**内容：**
```python
"""DSLighting 自定义异常类"""

class DSLightingError(Exception):
    """DSLighting 基础异常类"""
    pass


class ConfigurationError(DSLightingError):
    """配置相关错误"""
    pass


class DataLoadError(DSLightingError):
    """数据加载错误"""
    pass


class WorkflowError(DSLightingError):
    """工作流执行错误"""
    pass


class LLMError(DSLightingError):
    """LLM 相关错误"""
    pass


class ValidationError(DSLightingError):
    """验证错误"""
    pass
```

**使用示例：**
```python
# 在代码中使用
from dslighting.exceptions import DataLoadError, ConfigurationError

if not data:
    raise DataLoadError(
        "Either 'data' or 'task_id' must be provided. "
        "Example: agent.run(task_id='bike-sharing-demand')"
    )
```

---

### 3. 建立 pytest 框架
**工作量：** 0.5 天

**步骤：**

1. **创建目录结构：**
```bash
mkdir -p tests/{unit,integration,fixtures/{data,configs}}
touch tests/{__init__.py,conftest.py}
touch tests/unit/__init__.py
touch tests/integration/__init__.py
```

2. **创建 `tests/conftest.py`：**
```python
"""pytest 配置和 fixtures"""

import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def temp_dir():
    """临时目录 fixture"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_data():
    """示例数据 fixture"""
    import pandas as pd
    return pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [2, 4, 6, 8, 10]
    })


@pytest.fixture
def mock_llm_response():
    """Mock LLM 响应"""
    return {
        "id": "test",
        "choices": [{
            "message": {
                "content": "Test response",
                "role": "assistant"
            }
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20
        }
    }
```

3. **更新 `pyproject.toml`：**
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "-v",
    "--tb=short",
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "slow: Slow running tests",
]
```

4. **创建第一个测试 `tests/unit/test_agent_init.py`：**
```python
"""测试 Agent 初始化"""

import pytest
import dslighting


def test_agent_init_default():
    """测试默认初始化"""
    agent = dslighting.Agent(workflow="aide")
    assert agent is not None
    assert agent.workflow == "aide"


def test_agent_init_with_model():
    """测试指定模型初始化"""
    agent = dslighting.Agent(
        workflow="aide",
        model="gpt-4o"
    )
    assert agent.model == "gpt-4o"


@pytest.mark.parametrize("workflow", [
    "aide",
    "autokaggle",
    "data_interpreter",
    "automind",
    "dsagent",
    "deepanalyze",
])
def test_all_workflows(workflow):
    """测试所有工作流可以初始化"""
    agent = dslighting.Agent(workflow=workflow)
    assert agent.workflow == workflow
```

5. **验证：**
```bash
# 安装 pytest（如果还没有）
pip install pytest

# 运行测试
pytest tests/ -v

# 应该看到：
# tests/unit/test_agent_init.py::test_agent_init_default PASSED
# tests/unit/test_agent_init.py::test_agent_init_with_model PASSED
# tests/unit/test_agent_init.py::test_all_workflows[aide] PASSED
# ...
```

---

### 4. 优化依赖配置
**文件：** `pyproject.toml`
**工作量：** 1 小时

**当前问题：**
```toml
[project.optional-dependencies]
full = [...]  # 与 dependencies 完全相同
```

**修复方案：**
```toml
[project.optional-dependencies]
# 核心功能（无 ML 框架）
core = [
    "pandas>=1.5.0,<3.0.0",
    "pydantic>=2.10.0,<3.0.0",
    "python-dotenv>=1.0.0",
    "openai>=1.0.0",
    "anthropic>=0.34.0",
    "litellm>=1.80.0",
    "rich>=13.0.0",
    "scikit-learn>=1.0.0,<2.0.0",
    "diskcache",
    "tenacity",
    "appdirs",
    "pyyaml",
    "tqdm",
    "py7zr",
]

# RAG 支持（需要 ML 框架）
rag = [
    "transformers>=4.30.0",
    "torch>=2.0.0",
]

# Jupyter 支持（data_interpreter 需要）
jupyter = [
    "nbformat>=5.0.0",
    "nbclient>=0.5.0",
    "ipykernel>=7.0.0",
]

# 完整安装
all = ["dslighting[core,rag,jupyter]"]

# 开发工具
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]
```

**更新文档：**
在 `PIP_DOC/README_PIP.md` 中添加：
```markdown
## 安装选项

### 基本安装（推荐）
适用于 AIDE、AutoKaggle 等基本工作流：
```bash
pip install dslighting[core]
```

### 完整安装
包含 RAG 和 Jupyter 支持：
```bash
pip install dslighting[all]
```

### 开发安装
```bash
pip install dslighting[all,dev]
```
```

---

## 🗓️ 第 2 周任务（2-5 天）

### 5. 核心模块单元测试
**工作量：** 3-5 天

**测试文件清单：**

#### 5.1 `tests/unit/test_data_loader.py`
```python
"""测试 DataLoader"""

import pytest
from dslighting.core.data_loader import DataLoader, LoadedData
import pandas as pd


def test_load_built_in_dataset():
    """测试加载内置数据集"""
    loader = DataLoader()
    data = loader.load("bike-sharing-demand")
    assert isinstance(data, LoadedData)
    assert data.train_df is not None
    assert data.test_df is not None


def test_load_custom_csv(tmp_path):
    """测试加载自定义 CSV"""
    # 创建测试数据
    df = pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})
    csv_path = tmp_path / "test.csv"
    df.to_csv(csv_path, index=False)

    # 加载
    loader = DataLoader()
    data = loader.load(str(csv_path))
    assert isinstance(data, LoadedData)


def test_load_invalid_dataset():
    """测试加载无效数据集"""
    loader = DataLoader()
    with pytest.raises(DataLoadError):
        loader.load("non-existent-dataset")
```

#### 5.2 `tests/unit/test_config_builder.py`
```python
"""测试 ConfigBuilder"""

import pytest
from dslighting.core.config_builder import ConfigBuilder


def test_build_aide_config():
    """测试构建 AIDE 配置"""
    builder = ConfigBuilder()
    config = builder.build(
        workflow="aide",
        model="gpt-4o",
        temperature=0.7
    )
    assert config.workflow == "aide"
    assert config.llm.model == "gpt-4o"


def test_build_dsagent_config_with_enable_rag():
    """测试 DS-Agent 配置（含 enable_rag）"""
    builder = ConfigBuilder()
    config = builder.build(
        workflow="dsagent",
        dsagent={"enable_rag": False}
    )
    assert config.workflow.params["enable_rag"] is False
```

#### 5.3 `tests/unit/test_task_detector.py`
```python
"""测试 TaskDetector"""

import pytest
from dslighting.core.task_detector import TaskDetector


def test_detect_kaggle_task():
    """测试识别 Kaggle 任务"""
    detector = TaskDetector()
    task_type = detector.detect("bike-sharing-demand")
    assert task_type == "kaggle"


def test_recommend_workflow_for_kaggle():
    """测试为 Kaggle 任务推荐工作流"""
    detector = TaskDetector()
    workflow = detector.recommend("bike-sharing-demand")
    assert workflow in ["aide", "autokaggle"]
```

---

### 6. 集成测试（简化版）
**工作量：** 2-3 天

#### 6.1 `tests/integration/test_enable_rag.py`
```python
"""测试 enable_rag 参数"""

import pytest
import dslighting
from unittest.mock import patch, MagicMock


def test_dsagent_with_rag_disabled():
    """测试 DS-Agent 禁用 RAG"""
    # Mock VDBService 以避免实际下载
    with patch('dsat.workflows.factory.VDBService') as mock_vdb:
        agent = dslighting.Agent(
            workflow="dsagent",
            dsagent={"enable_rag": False}
        )

        # 验证 VDBService 不被调用
        mock_vdb.assert_not_called()


def test_automind_with_rag_disabled():
    """测试 AutoMind 禁用 RAG"""
    with patch('dsat.workflows.factory.VDBService') as mock_vdb:
        agent = dslighting.Agent(
            workflow="automind",
            automind={"enable_rag": False}
        )

        # 验证 VDBService 不被调用
        mock_vdb.assert_not_called()


def test_dsagent_with_rag_enabled():
    """测试 DS-Agent 启用 RAG"""
    with patch('dsat.workflows.factory.VDBService') as mock_vdb:
        agent = dslighting.Agent(
            workflow="dsagent",
            dsagent={"enable_rag": True}
        )

        # 验证 VDBService 被调用
        mock_vdb.assert_called_once()
```

---

## 📝 文档改进任务

### 7. 统一文档语言
**工作量：** 1-2 天

**步骤：**

1. **决定主语言：**
   - 推荐：英文（国际用户）
   - 备选：中文 + 英文版本

2. **统一代码注释：**
```python
# 中文注释改为英文
# 数据加载器  →  # Data loader
# 运行工作流  →  # Run workflow
```

3. **统一日志消息：**
```python
# 混合 → 统一
logger.info("正在加载数据...")
logger.info("Loading data...")  # 统一为英文
```

4. **统一异常消息：**
```python
# 混合 → 统一
raise DataLoadError("数据加载失败")
raise DataLoadError("Failed to load data")  # 统一为英文
```

**检查脚本：**
```bash
# 检查中文注释
grep -r "# .*[\u4e00-\u9fa5]" dslighting/ --include="*.py"

# 检查中文日志
grep -r "logger\.\(info\|warning\|error\).*[\u4e00-\u9fa5]" dslighting/ --include="*.py"
```

---

## 🎯 验证清单

### 代码质量 ✅
- [ ] 所有 DEBUG print 已移除
- [ ] 异常处理统一
- [ ] 类型提示补全（至少公共 API）
- [ ] 代码格式一致

### 测试 🧪
- [ ] pytest 框架已建立
- [ ] 核心模块有单元测试
- [ ] 至少 2 个工作流有集成测试
- [ ] 测试覆盖率 > 60%

### 文档 📚
- [ ] 文档语言统一
- [ ] README 更新
- [ ] 安装文档更新（含依赖选项）

### 依赖 📦
- [ ] 轻量依赖选项可用
- [ ] 版本约束合理
- [ ] 测试不同安装方式

---

## 📊 进度跟踪

### Week 1: 紧急修复
- [ ] 移除 DEBUG prints（Day 1）
- [ ] 创建异常类（Day 1）
- [ ] 建立 pytest 框架（Day 2-3）
- [ ] 优化依赖配置（Day 4）

### Week 2: 测试覆盖
- [ ] 核心模块单元测试（Day 1-3）
- [ ] 工作流集成测试（Day 4-5）

### Week 3-4: 完善优化
- [ ] 统一文档语言
- [ ] 补全类型提示
- [ ] 更新文档

---

## 🚀 快速开始

如果你想立即开始，执行以下命令：

```bash
# 1. 移除 DEBUG prints
cd /Users/liufan/Applications/Github/dslighting
# 手动编辑 dslighting/core/agent.py 移除 [DEBUG] 语句

# 2. 创建异常类
cat > dslighting/exceptions.py << 'EOF'
# 粘贴上面的异常类代码
EOF

# 3. 建立测试框架
mkdir -p tests/{unit,integration,fixtures/{data,configs}}
cat > tests/conftest.py << 'EOF'
# 粘贴上面的 conftest.py 代码
EOF

# 4. 运行第一个测试
cat > tests/unit/test_agent_init.py << 'EOF'
# 粘贴上面的测试代码
EOF

pytest tests/unit/test_agent_init.py -v
```

---

**最后更新：** 2026-01-18
**下一个里程碑：** v1.9.8 或 v1.10.0
