# DSLighting v1.9.2 发布说明

## 🐛 Bug 修复

### CLI 命令模块缺失问题

**问题描述**:
在 v1.9.1 中，安装后运行 `dslighting help` 等命令会出现 `ModuleNotFoundError: No module named 'dslighting_cli'` 错误。

**原因**:
`dslighting_cli.py` 是项目根目录下的独立模块，但 `pyproject.toml` 中的包配置只包含了 `dslighting*`、`dsat*`、`mlebench*` 包（目录），没有包含根目录下的顶级 Python 模块文件，导致 `dslighting_cli.py` 没有被打包进分发包中。

**修复方案**:
在 `pyproject.toml` 中添加了 `[tool.setuptools.py-modules]` 配置，明确包含 `dslighting_cli` 模块：

```toml
# Include top-level Python modules
[tool.setuptools.py-modules]
dslighting_cli = "dslighting_cli"
```

---

## ✅ 修复验证

### 安装测试
```bash
pip install dslighting==1.9.2
```

### CLI 命令测试
```bash
# 所有命令应该正常工作
dslighting help              # ✅ 正常
dslighting workflows          # ✅ 正常
dslighting example aide       # ✅ 正常
dslighting quickstart         # ✅ 正常
dslighting detect-packages    # ✅ 正常
```

### Python 帮助函数测试
```python
import dslighting

dslighting.help()              # ✅ 正常
dslighting.list_workflows()    # ✅ 正常
dslighting.show_example("aide") # ✅ 正常
```

---

## 📦 安装

```bash
pip install --upgrade dslighting==1.9.2
```

---

## 🔧 技术细节

### 修改的文件

1. **pyproject.toml**
   - 添加 `[tool.setuptools.py-modules]` 配置
   - 包含 `dslighting_cli` 模块
   - 版本号更新到 1.9.2

2. **dslighting/__init__.py**
   - 版本号更新到 1.9.2

### 向后兼容性

✅ **100% 向后兼容** v1.9.0 和 v1.9.1
- 仅修复打包配置问题
- 所有功能保持不变

---

## 📖 完整文档

- **PyPI**: https://pypi.org/project/dslighting/1.9.2/
- **GitHub**: https://github.com/usail-hkust/dslighting
- **在线文档**: https://luckyfan-cs.github.io/dslighting-web/
- **快速开始**: PIP_DOC/QUICK_START.md

---

## 🎉 总结

DSLighting v1.9.2 是一个 **Bug 修复版本**，修复了 v1.9.1 中 CLI 命令无法使用的关键问题。

### 核心修复
- ✅ 修复 `dslighting_cli` 模块打包问题
- ✅ 所有 CLI 命令现在可以正常使用
- ✅ 100% 向前兼容

### 推荐行动
- **v1.9.1 用户**：强烈建议升级到 v1.9.2 以修复 CLI 命令问题
- **新用户**：直接安装 v1.9.2

---

**版本**: DSLighting v1.9.2
**发布日期**: 2026-01-17
**向后兼容**: ✅ 是（100% 兼容 v1.9.0 和 v1.9.1）
**类型**: Bug 修复（CLI 命令模块缺失）
