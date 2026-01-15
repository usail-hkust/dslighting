# 🚀 PyPI 发布快速指南

5 分钟内将 DSLighting 发布到 PyPI！

## ✅ 准备工作

### 1. 注册账号
- PyPI: https://pypi.org/account/register/
- 创建 API Token

### 2. 安装工具
```bash
pip install build twine
```

## 📦 更新配置

在 `pyproject.toml` 中**添加核心依赖**（当前缺失）：

```toml
dependencies = [
    "pandas>=1.5.0",
    "pydantic>=2.0",
    "python-dotenv>=1.0.0",
]
```

**原因**：用户通过 pip 安装时，需要这些基础依赖。

## 🔨 构建和发布

```bash
# 1. 清理旧文件
rm -rf dist/ build/

# 2. 构建
python -m build

# 3. 检查
twine check dist/*

# 4. 测试安装（可选）
python -m venv test_env
source test_env/bin/activate
pip install dist/dslighting-*.whl
python -c "import dslighting; print('OK')"
deactivate

# 5. 发布到 TestPyPI（推荐先测试）
twine upload --repository testpypi dist/*

# 6. 发布到正式 PyPI
twine upload dist/*
```

## 🎯 一键发布脚本

创建 `scripts/publish.sh`：

```bash
#!/bin/bash
set -e

echo "🚀 Publishing DSLighting to PyPI..."

# 清理
echo "🧹 Cleaning old builds..."
rm -rf dist/ build/

# 构建
echo "📦 Building package..."
python -m build

# 检查
echo "✅ Checking package..."
twine check dist/*

# 上传
echo "📤 Uploading to PyPI..."
twine upload dist/*

echo "✅ Done! Package published to PyPI!"
echo "📦 Install with: pip install dslighting"
```

使用：

```bash
chmod +x scripts/publish.sh
./scripts/publish.sh
```

## 📊 用户安装

发布后，用户可以：

```bash
# 基础安装
pip install dslighting

# 完整安装（包含所有依赖）
pip install dslighting[full]

# 使用
python -c "
import dslighting
result = dslighting.run_agent('What is 2+2?')
print(f'Answer: {result.output}')
"
```

## ⚠️ 重要提示

1. **版本号**：每次发布前更新 `pyproject.toml` 中的版本号
2. **TestPyPI**：先在 TestPyPI 测试，确认无误后再发布到正式 PyPI
3. **API Token**：使用 token 而不是密码
4. **检查**：发布前先 `twine check dist/*`

## 🔗 有用的链接

- **PyPI**: https://pypi.org/
- **TestPyPI**: https://test.pypi.org/
- **详细指南**: [PYPI_PUBLISHING_GUIDE.md](PYPI_PUBLISHING_GUIDE.md)

---

**准备好了？运行 `python -m build && twine upload dist/*` 即可发布！** 🚀
