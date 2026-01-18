# DSLighting v1.9.1 发布说明

## 🎉 重大更新：完整的帮助系统

### 核心改进

DSLighting v1.9.1 引入了**完整的帮助系统**，解决用户"不知道如何使用"的问题。现在用户可以通过 CLI 命令或 Python 函数快速获取帮助、查看示例和开始使用。

---

## ✨ 新特性

### 1️⃣ CLI 帮助命令

新增 4 个用户友好的命令行工具：

#### `dslighting help` - 显示主帮助

```bash
$ dslighting help
```

显示：
- 快速开始指南
- 所有可用 workflow
- 有用的 CLI 命令
- Python 帮助函数
- 文档链接

#### `dslighting workflows` - 列出所有 workflow

```bash
$ dslighting workflows
```

显示每个 workflow 的：
- 完整名称
- 描述
- 使用场景
- 默认模型
- 独有参数

#### `dslighting example <workflow>` - 显示示例代码

```bash
$ dslighting example aide
$ dslighting example autokaggle
$ dslighting example data_interpreter
```

直接显示可复制粘贴的完整示例代码！

#### `dslighting quickstart` - 快速开始指南

```bash
$ dslighting quickstart
```

显示详细的快速开始指南，包括：
- 安装步骤
- API Key 设置
- 第一个 Agent
- 使用自己的数据
- 选择正确的 workflow
- 常见问题解答

---

### 2️⃣ Python 帮助函数

在 Python 中添加了 3 个交互式帮助函数：

#### `dslighting.help()` - 显示帮助

```python
import dslighting
dslighting.help()
```

#### `dslighting.list_workflows()` - 列出 workflow

```python
import dslighting
dslighting.list_workflows()
```

显示所有 workflow 的详细信息。

#### `dslighting.show_example()` - 显示示例

```python
import dslighting
dslighting.show_example("aide")
dslighting.show_example("autokaggle")
```

显示完整可运行的示例代码。

---

### 3️⃣ 完整的快速开始文档

创建了 **QUICK_START.md**，包含：

- 📦 安装指南
- 🔑 API Key 设置
- 🚀 3 步开始使用
- 📊 使用自己的数据
- 🎯 Workflow 选择指南
- 💡 常用示例
- 🛠️ 获取帮助的方法
- 📚 进阶用法
- ⚠️ 常见问题解答

---

## 📋 使用示例

### CLI 命令行使用

```bash
# 新手入门
$ dslighting help              # 查看帮助
$ dslighting workflows          # 查看所有 workflow
$ dslighting example aide       # 查看 AIDE 示例

# 直接复制运行
$ dslighting example autokaggle  # 显示 AutoKaggle 代码
# 复制代码到你的文件，运行！
```

### Python 交互式使用

```python
import dslighting

# 方式 1：查看帮助
dslighting.help()

# 方式 2：查看所有 workflow
dslighting.list_workflows()

# 方式 3：查看具体示例
dslighting.show_example("aide")

# 方式 4：开始使用
data = dslighting.load_data("bike-sharing-demand")
agent = dslighting.Agent(workflow="aide")
result = agent.run(data)
```

---

## 🎯 用户收益

### 解决的问题

✅ **不知道有哪些 workflow** - 运行 `dslighting workflows`
✅ **不知道如何开始** - 运行 `dslighting quickstart`
✅ **不知道怎么用** - 运行 `dslighting example <workflow>`
✅ **没有示例代码** - 所有命令都提供完整示例
✅ **没有文档指引** - QUICK_START.md 提供完整指南

### 改进的用户体验

**之前**（v1.9.0）：
```bash
# 用户不知道有哪些命令
$ dslighting
# 只显示 detect-packages, show-packages 等

# 不知道如何开始
# 需要查看 GitHub 文档
```

**现在**（v1.9.1）：
```bash
# 清晰的命令列表
$ dslighting help
# 显示所有命令和用法

# 快速开始
$ dslighting quickstart
# 5 分钟快速上手指南

# 查看示例
$ dslighting example aide
# 直接复制代码运行
```

---

## 📊 功能对比

| 功能 | v1.9.0 | v1.9.1 |
|------|--------|--------|
| CLI 命令 | 3 个 | 7 个 |
| Python 帮助函数 | 0 个 | 3 个 |
| 快速开始文档 | ❌ | ✅ |
| Workflow 示例 | ❌ | ✅ |
| 交互式帮助 | ❌ | ✅ |
| 用户友好度 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 📦 安装

```bash
pip install --upgrade dslighting==1.9.1
```

或从源码安装：

```bash
git clone https://github.com/usail-hkust/dslighting.git
cd dslighting
pip install -e .
```

---

## 🚀 快速体验

安装后立即运行：

```bash
# 查看帮助
$ dslighting help

# 查看所有 workflow
$ dslighting workflows

# 查看示例
$ dslighting example aide
```

或在 Python 中：

```python
import dslighting

# 显示帮助
dslighting.help()

# 查看示例
dslighting.show_example("autokaggle")
```

---

## 📚 文档更新

- ✅ **QUICK_START.md** - 新增完整快速开始指南
- ✅ **CLI 帮助** - 4 个新命令
- ✅ **Python 帮助** - 3 个新函数
- ✅ **所有示例代码** - 可直接复制运行

---

## 🔧 技术细节

### 修改的文件

1. **dslighting_cli.py**
   - 新增 `cmd_help()` - 显示帮助
   - 新增 `cmd_workflows()` - 列出 workflow
   - 新增 `cmd_example()` - 显示示例
   - 新增 `cmd_quickstart()` - 快速开始
   - 更新 `main()` - 注册新命令

2. **dslighting/__init__.py**
   - 新增 `help()` - 显示帮助
   - 新增 `list_workflows()` - 列出 workflow
   - 新增 `show_example()` - 显示示例
   - 更新 `__all__` - 导出新函数

3. **QUICK_START.md**（新建）
   - 5 分钟快速上手
   - 完整示例代码
   - 常见问题解答
   - 进阶用法

### 向后兼容性

✅ **100% 向后兼容** v1.9.0
- 所有原有功能保持不变
- 仅添加新的帮助功能
- 不影响现有代码

---

## 🧪 测试验证

### CLI 命令测试

```bash
# 测试所有命令
$ dslighting help           # ✅ 正常
$ dslighting workflows       # ✅ 正常
$ dslighting example aide    # ✅ 正常
$ dslighting quickstart      # ✅ 正常
```

### Python 函数测试

```python
import dslighting

dslighting.help()              # ✅ 正常
dslighting.list_workflows()    # ✅ 正常
dslighting.show_example("aide") # ✅ 正常
```

---

## 📖 完整文档

- **PyPI**: https://pypi.org/project/dslighting/1.9.1/
- **GitHub**: https://github.com/usail-hkust/dslighting
- **在线文档**: https://luckyfan-cs.github.io/dslighting-web/
- **快速开始**: PIP_DOC/QUICK_START.md

---

## 🎉 总结

DSLighting v1.9.1 是一个**用户体验重大改进版本**，通过添加完整的帮助系统，彻底解决了"不知道如何使用"的问题。

### 核心特性
- ✅ CLI 帮助命令
- ✅ Python 交互式帮助
- ✅ 完整快速开始指南
- ✅ 所有 workflow 示例代码
- ✅ 100% 向后兼容

### 推荐行动
- **新用户**：运行 `dslighting help` 开始使用
- **现有用户**：升级体验新的帮助系统
- **所有用户**：享受更友好的开发体验！

---

**版本**: DSLighting v1.9.1
**发布日期**: 2026-01-17
**向后兼容**: ✅ 是（100% 兼容 v1.9.0）
**类型**: 功能更新（用户体验改进）
