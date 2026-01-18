# DSLighting v1.9.4 发布说明

## ✨ 功能改进

### 1. 包检测优化 - 只保存 Data Science 相关包

**改进内容**:
`detect-packages` 命令现在默认只保存 Data Science & ML 相关的包，而不是所有依赖包。

**改进前**:
```bash
$ dslighting detect-packages
📦 Found 97 packages
✓ Saved 97 packages to config
```

**改进后**:
```bash
$ dslighting detect-packages
📦 Detecting Data Science & ML packages...
   Mode: Save only Data Science packages (recommended)

✓ Found 97 total packages in environment

📊 Data Science & ML Packages (7):
   - numpy (2.2.6)
   - pandas (2.3.3)
   - requests (2.32.5)
   - scikit-learn (1.7.2)
   - scipy (1.15.3)
   - torch (2.9.1)
   - transformers (4.57.6)

✓ Saved 7 Data Science packages to config: config.yaml
```

**优势**:
- ✅ Agent context 更简洁清晰
- ✅ 减少 token 使用（只传递核心包信息）
- ✅ 避免向 agent 暴露不相关的依赖包
- ✅ 更快、更精准的代码生成

**新参数**:
- `--all`: 保存所有包（包括依赖）
- `--data-science-only`: 只保存 Data Science 包（默认行为）

**使用示例**:
```bash
# 默认：只保存 Data Science 包（推荐）
dslighting detect-packages

# 保存所有包
dslighting detect-packages --all
```

**修改的文件**:
- `dslighting/utils/package_detector.py`:
  - `save_to_config()` 方法添加 `data_science_only` 参数
  - 默认值为 `True`，只保存 Data Science 包
- `dslighting_cli.py`:
  - `cmd_detect_packages()` 函数优化输出信息
  - 添加 `--all` 和 `--data-science-only` 参数

---

### 2. 添加 ipykernel 核心依赖

**问题描述**:
在 v1.9.3 中，`data_interpreter` workflow 会报错：
```
jupyter_client.kernelspec.NoSuchKernel: No such kernel named python3
```

这是因为 `ipykernel` 没有作为核心依赖包含在 DSLighting 中。

**修复方案**:
将 `ipykernel>=7.0.0` 添加到核心依赖列表中。

**修改的文件**:
- `pyproject.toml`:
  ```toml
  # Notebook support (required for data_interpreter workflow)
  "nbformat",
  "nbclient",
  "ipykernel>=7.0.0",  # Required for Jupyter kernel in data_interpreter
  ```

**影响范围**:
- ✅ **data_interpreter workflow**: 现在可以正常使用 notebook executor
- ✅ **其他 workflows**: 无影响（不使用 notebook executor）

---

## ✅ 改进验证

### 环境信息
- **Python**: 3.10+
- **Workflow**: data_interpreter
- **测试环境**: macOS + Linux + Windows

### 测试 1: 包检测优化
```bash
# 安装新版本
pip install --upgrade dslighting==1.9.4

# 检测包（默认只保存 Data Science 包）
dslighting detect-packages

# 预期结果：只保存 7-15 个 Data Science 包，而不是 70-100 个所有包
```

### 测试 2: data_interpreter workflow
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
- ✅ Jupyter kernel 正常启动
- ✅ Notebook executor 正常工作
- ✅ 不会出现 "No such kernel named python3" 错误

---

## 📦 安装

```bash
pip install --upgrade dslighting==1.9.4
```

---

## 🎯 影响范围

### 改进 1: 包检测优化
| 用户类型 | 影响 | 建议 |
|---------|------|------|
| **新用户** | ✅ 更简洁的 agent context | 直接使用 v1.9.4 |
| **旧用户** | ⚠️ 需要重新运行 `detect-packages` | 运行 `dslighting detect-packages` 更新配置 |
| **高级用户** | ✅ 可选择保存所有包 | 使用 `--all` 参数 |

### 改进 2: ipykernel 依赖
| Workflow | 影响 | 状态 |
|----------|------|------|
| **data_interpreter** | ✅ 修复 kernel 缺失问题 | **必须升级** |
| **其他 workflows** | ✅ 无影响 | 可选升级 |

---

## 📖 完整文档

- **PyPI**: https://pypi.org/project/dslighting/1.9.4/
- **GitHub**: https://github.com/usail-hkust/dslighting
- **在线文档**: https://luckyfan-cs.github.io/dslighting-web/

---

## 🎉 总结

DSLighting v1.9.4 是一个 **功能改进版本**，包含两个重要的用户体验优化。

### 核心改进
1. ✅ **包检测优化**: 默认只保存 Data Science 包，减少 80-90% 的冗余信息
2. ✅ **添加 ipykernel 依赖**: 修复 data_interpreter workflow 的 kernel 缺失问题

### 推荐行动
- **data_interpreter workflow 用户**: **必须升级**到 v1.9.4
- **所有用户**: 强烈建议重新运行 `dslighting detect-packages` 以优化配置
- **新用户**: 直接安装 v1.9.4

### 升级后的操作
```bash
# 1. 升级到 v1.9.4
pip install --upgrade dslighting==1.9.4

# 2. 重新检测包（使用新的优化逻辑）
dslighting detect-packages

# 3. 验证配置
dslighting show-packages
```

---

**版本**: DSLighting v1.9.4
**发布日期**: 2026-01-17
**向后兼容**: ✅ 是（100% 兼容 v1.9.3）
**类型**: 功能改进（包检测优化 + 依赖修复）
