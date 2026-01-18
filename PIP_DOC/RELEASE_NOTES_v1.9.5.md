# DSLighting v1.9.5 发布说明

## 🐛 Bug 修复

### data_interpreter Workflow Matplotlib 导入错误

**问题描述**:
在 data_interpreter workflow 中，如果环境没有安装 matplotlib，会出现以下错误：

```
ModuleNotFoundError: No module named 'matplotlib'
```

**原因**:
notebook 初始化代码（`NOTEBOOK_INIT_CODE`）中强制导入了 matplotlib：
```python
import matplotlib.pyplot as plt  # ❌ 强制导入，环境没有时会报错
```

**修复方案**:
将 matplotlib 改为**可选导入**，并在导入时使用非交互式后端：

```python
# Optional: matplotlib (for plotting)
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
except Exception:
    pass  # ✅ 如果没有 matplotlib，继续运行
```

**修复的文件**:
- `dsat/services/sandbox.py`:
  - 修改 `NOTEBOOK_INIT_CODE` 常量
  - 将 matplotlib 和 seaborn 都改为可选导入
  - 添加非交互式后端配置

---

## ✅ 修复验证

### 测试环境 1: 无 matplotlib 环境

```python
from dotenv import load_dotenv
load_dotenv()

import dslighting

data = dslighting.load_data("bike-sharing-demand")

agent = dslighting.Agent(
    workflow="data_interpreter",
    model="gpt-4o-mini",
    max_iterations=5,
)

result = agent.run(data, description="分析销售趋势")
print(f"Success: {result.success}")
```

**预期结果**:
- ✅ Notebook kernel 正常启动
- ✅ 不会出现 "ModuleNotFoundError: No module named 'matplotlib'"
- ✅ Agent 可以正常运行（只是不能使用 matplotlib 绘图功能）

### 测试环境 2: 有 matplotlib 环境

**预期结果**:
- ✅ Notebook kernel 正常启动
- ✅ matplotlib 正常导入并使用非交互式后端
- ✅ Agent 可以使用 matplotlib 绘图

---

## 📦 安装

```bash
pip install --upgrade dslighting==1.9.5
```

---

## 🔧 技术细节

### 修改前（有问题的代码）

```python
NOTEBOOK_INIT_CODE = """
import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt  # ❌ 强制导入
import os

try:
    import seaborn as sns
    sns.set_theme(style="whitegrid")
except Exception:
    pass

warnings.filterwarnings('ignore')
print("DSAT Notebook environment initialized.")
"""
```

**问题**：
- 如果环境没有 matplotlib，notebook 初始化会失败
- 导致整个 data_interpreter workflow 无法使用

### 修改后（正确的代码）

```python
NOTEBOOK_INIT_CODE = """
import warnings
import pandas as pd
import numpy as np
import os

# Optional: matplotlib (for plotting)
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
except Exception:
    pass  # ✅ 可选导入

# Optional: seaborn (for better plots)
try:
    import seaborn as sns
    sns.set_theme(style="whitegrid")
except Exception:
    pass

warnings.filterwarnings('ignore')
print("DSAT Notebook environment initialized.")
"""
```

**改进**：
- ✅ matplotlib 改为可选导入
- ✅ 添加非交互式后端配置（防止 plt.show() 阻塞）
- ✅ 代码注释清晰说明哪些是可选的
- ✅ 即使没有 matplotlib，agent 也能正常运行

---

## 🎯 影响范围

### 受影响的 Workflow
- ✅ **data_interpreter** - 修复完成（现在可以在没有 matplotlib 的环境中运行）
- ✅ **其他 workflows** - 无影响（不使用 notebook executor）

### 受影响的场景
| 场景 | 修复前 | 修复后 |
|------|--------|--------|
| **无 matplotlib 环境** | ❌ 无法运行 | ✅ 正常运行（不能绘图） |
| **有 matplotlib 环境** | ✅ 正常运行 | ✅ 正常运行（可绘图） |

---

## 📖 完整文档

- **PyPI**: https://pypi.org/project/dslighting/1.9.5/
- **GitHub**: https://github.com/usail-hkust/dslighting
- **在线文档**: https://luckyfan-cs.github.io/dslighting-web/

---

## 🎉 总结

DSLighting v1.9.5 是一个 **Bug 修复版本**，修复了 data_interpreter workflow 在没有 matplotlib 的环境中无法运行的问题。

### 核心修复
- ✅ 将 matplotlib 改为可选导入
- ✅ 添加非交互式后端配置
- ✅ 确保 data_interpreter 可以在最小依赖环境中运行

### 推荐行动
- **data_interpreter workflow 用户**: **强烈建议升级**到 v1.9.5
- **所有用户**: 可选升级（不影响其他 workflows）

### 可选依赖说明

以下包是**可选的**，不是 data_interpreter workflow 的必需依赖：
- `matplotlib` - 用于绘图
- `seaborn` - 用于更好的可视化

如果需要绘图功能，可以手动安装：
```bash
pip install matplotlib seaborn
```

---

**版本**: DSLighting v1.9.5
**发布日期**: 2026-01-17
**向后兼容**: ✅ 是（100% 兼容 v1.9.4）
**类型**: Bug 修复（可选依赖导入）
