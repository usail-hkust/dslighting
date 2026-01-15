# PyPI 发布指南

本指南说明如何将 DSLighting 发布到 PyPI，让用户可以通过 `pip install dslighting` 直接安装。

## 🎯 发布目标

用户可以这样安装：

```bash
pip install dslighting
```

然后直接使用：

```python
import dslighting
result = dslighting.run_agent("data/competitions/bike-sharing-demand")
```

## 📋 前置要求

### 1. PyPI 账号

- 注册 PyPI 账号：https://pypi.org/account/register/
- 启用双重认证（2FA）
- 创建 API token

### 2. 安装发布工具

```bash
pip install build twine
```

## 🔧 配置 pyproject.toml

当前 `pyproject.toml` 需要添加核心依赖，因为用户通过 pip 安装时不会自动安装 `requirements_local.txt`。

### 更新依赖配置

编辑 `pyproject.toml`，添加核心依赖：

```toml
[project]
name = "dslighting"
version = "1.0.0"
description = "Simplified API for Data Science Agent Automation"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "AGPL-3.0"}
authors = [
    {name = "DSLighting Team", email = "your-email@example.com"}
]
maintainers = [
    {name = "DSLighting Team", email = "your-email@example.com"}
]
keywords = ["data-science", "agent", "automation", "machine-learning", "ai"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: GNU Affero General Public License v3",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]

# 核心依赖（必需）
dependencies = [
    "pandas>=1.5.0",
    "pydantic>=2.0",
    "python-dotenv>=1.0.0",
]

# 可选依赖
[project.optional-dependencies]
# 包含 DSAT 框架的所有依赖
full = [
    "openai>=1.0.0",
    "anthropic>=0.34.0",
    "litellm>=1.0.0",
    "rich>=13.0.0",
    "transformers>=4.30.0",
    "torch>=2.0.0",
    "scikit-learn>=1.0.0",
]
# 开发依赖
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "black>=23.0",
    "mypy>=1.0",
    "ruff>=0.1.0",
]

# 项目 URL
[project.urls]
Homepage = "https://github.com/usail-hkust/dslighting"
Documentation = "https://luckyfan-cs.github.io/dslighting-web/"
Repository = "https://github.com/usail-hkust/dslighting"
"Bug Tracker" = "https://github.com/usail-hkust/dslighting/issues"
```

## 📦 构建包

### 1. 清理旧的构建文件

```bash
cd /path/to/dslighting
rm -rf dist/ build/ *.egg-info
```

### 2. 构建源码包和 wheel

```bash
python -m build
```

这会在 `dist/` 目录下生成：
- `dslighting-1.0.0.tar.gz` (源码包)
- `dslighting-1.0.0-py3-none-any.whl` (wheel 包)

## 🧪 测试包

### 1. 本地测试安装

```bash
# 创建虚拟环境测试
python3 -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate

# 安装构建的包
pip install dist/dslighting-1.0.0-py3-none-any.whl

# 测试导入
python -c "import dslighting; print(dslighting.__version__)"

# 测试功能（需要 API_KEY）
python -c "
import dslighting
result = dslighting.run_agent('What is 2+2?')
print(f'Answer: {result.output}')
"

# 退出测试环境
deactivate
```

### 2. 检查包内容

```bash
twine check dist/*
```

修复所有警告和错误。

## 🚀 发布到 PyPI

### 方式 1: 使用 API Token（推荐）

1. **创建 PyPI API Token**:
   - 登录 https://pypi.org/manage/account/token/
   - 创建新的 token
   - 选择 "Entire account" 或特定项目
   - 复制 token（只显示一次！）

2. **配置 ~/.pypirc**:
   ```ini
   [pypi]
   username = __token__
   password = pypi-xxxxxx...  # 你的 API token
   ```

3. **上传到 PyPI**:
   ```bash
   twine upload dist/*
   ```

### 方式 2: 使用用户名密码（不推荐）

```bash
twine upload dist/* --username your-username --password your-password
```

### 发布到 TestPyPI（先测试）

```bash
# 1. 注册 TestPyPI 账号
# https://test.pypi.org/account/register/

# 2. 配置 ~/.pypirc
[pypi]
username = __token__
password = pypi-xxxxxx...  # 生产环境 token

[testpypi]
username = __token__
password = pypi-xxxxxx...  # 测试环境 token

# 3. 上传到 TestPyPI
twine upload --repository testpypi dist/*

# 4. 从 TestPyPI 安装测试
pip install --index-url https://test.pypi.org/simple/ dslighting

# 5. 测试通过后，再发布到正式 PyPI
twine upload dist/*
```

## 📝 发布流程清单

### 首次发布

```bash
# 1. 确认版本号
grep "version = " pyproject.toml

# 2. 更新 CHANGELOG
echo "## v1.0.0 (2025-01-15)" >> CHANGELOG.md
echo "- Initial release of DSLighting simplified API" >> CHANGELOG.md

# 3. 清理旧构建
rm -rf dist/ build/ *.egg-info

# 4. 构建包
python -m build

# 5. 检查包
twine check dist/*

# 6. 测试安装（可选但推荐）
python -m venv test_install
source test_install/bin/activate
pip install dist/dslighting-1.0.0-py3-none-any.whl
python -c "import dslighting; print('OK')"
deactivate

# 7. 发布到 TestPyPI（测试）
twine upload --repository testpypi dist/*

# 8. 从 TestPyPI 测试安装
pip install --index-url https://test.pypi.org/simple/ dslighting

# 9. 发布到正式 PyPI
twine upload dist/*
```

### 后续版本更新

```bash
# 1. 更新版本号
# 修改 pyproject.toml: version = "1.0.1" -> version = "1.0.2"

# 2. 清理
rm -rf dist/ build/ *.egg-info

# 3. 构建
python -m build

# 4. 发布
twine upload dist/*
```

## 🔐 安全最佳实践

### 1. 使用 Trusted Publishing（推荐）

GitHub Actions 自动发布，无需存储 token：

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  release:
    types: [published]

permissions:
  id-token: write  # REQUIRED for trusted publishing
  contents: read

jobs:
  pypi-publish:
    name: Upload release to PyPI
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: "3.10"
    - name: Install build dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build
    - name: Build package
      run: python -m build
    - name: Publish package distributions to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
```

**配置 Trusted Publishing**:
1. 访问 https://pypi.org/manage/account/publishing/
2. 添加新的 publisher
3. 选择 GitHub Actions workflow
4. 关联你的 GitHub 仓库

### 2. 保护 API Token

- ✅ 使用 API token，不用密码
- ✅ Token 存储在 `~/.pypirc`，不要写在代码里
- ✅ 使用环境变量：`export TWINE_PASSWORD=pypi-xxxxxx`
- ✅ 不要把 token 提交到 Git

## 📊 版本管理

### 语义化版本（Semantic Versioning）

```
MAJOR.MINOR.PATCH

1.0.0 - 初始发布
1.0.1 - Bug 修复
1.1.0 - 新功能（向后兼容）
2.0.0 - 破坏性变更
```

### 更新版本号

```bash
# 1. 修改 pyproject.toml
version = "1.0.1"  # 修改这里

# 2. 更新 __init__.py
__version__ = "1.0.1"  # 保持一致

# 3. 提交
git add pyproject.toml dslighting/__init__.py
git commit -m "bump: version 1.0.0 -> 1.0.1"
git tag v1.0.1
git push --tags
```

## 🐛 常见问题

### Q1: 上传失败 - "File already exists"

```bash
# 原因：版本号已存在
# 解决：更新版本号
# 修改 pyproject.toml 中的 version
# 然后重新构建和上传
```

### Q2: 导入错误

```bash
# 检查包结构
python -m build
tar -tzf dist/dslighting-1.0.0.tar.gz  # 查看内容
# 确保所有必要文件都在包中
```

### Q3: 依赖冲突

```bash
# 如果用户安装时遇到依赖冲突：
# 1. 在 pyproject.toml 中指定最小依赖
# 2. 不在 PyPI 中包含所有依赖
# 3. 用户可选安装完整依赖：pip install dslighting[full]
```

### Q4: 包名被占用

```bash
# 如果 dslighting 名字被占用：
# 1. 使用其他名字，如 dslighting-ai
# 2. 或者联系现有包的维护者
# 3. 检查：https://pypi.org/search/?q=dslighting
```

## 📦 用户安装方式

发布成功后，用户可以这样安装：

### 方式 1: 基础安装（最小依赖）

```bash
pip install dslighting
```

只安装核心依赖（pandas, pydantic, python-dotenv）。

### 方式 2: 完整安装（包含所有依赖）

```bash
pip install dslighting[full]
```

安装所有依赖，包括 DSAT 框架。

### 方式 3: 开发安装

```bash
pip install dslighting[dev]
```

包含开发工具（pytest, black, mypy 等）。

### 方式 4: 从 GitHub 安装（开发版）

```bash
pip install git+https://github.com/usail-hkust/dslighting.git
```

## ✅ 发布后验证

```bash
# 1. 从 PyPI 搜索
# 访问 https://pypi.org/project/dslighting/

# 2. 安装测试
pip install dslighting

# 3. 导入测试
python -c "import dslighting; print(dslighting.__version__)"

# 4. 功能测试
python -c "
import dslighting
result = dslighting.run_agent('What is 2+2?')
print(f'✓ Works! Answer: {result.output}')
"
```

## 📚 相关资源

- **PyPI 用户指南**: https://packaging.python.org/tutorials/packaging-projects/
- **Twine 文档**: https://twine.readthedocs.io/
- ** Trusted Publishing**: https://docs.pypi.org/trusted-publishers/
- **语义化版本**: https://semver.org/

## 🎯 快速参考

### 常用命令

```bash
# 构建
python -m build

# 检查
twine check dist/*

# 上传到 TestPyPI
twine upload --repository testpypi dist/*

# 上传到 PyPI
twine upload dist/*

# 测试安装
pip install --index-url https://test.pypi.org/simple/ dslighting
pip install dslighting
```

### 文件清单

确保以下文件在 git 仓库中：
- ✅ `pyproject.toml` - 包配置
- ✅ `README.md` - 主文档
- ✅ `LICENSE` - 许可证文件
- ✅ `MANIFEST.in` - 包含额外文件（如果需要）
- ✅ `dslighting/` - 包代码

### 不要发布

- ❌ `.env` 或 `.env.example`
- ❌ `tests/` (测试文件)
- ❌ `__pycache__/`
- ❌ `*.pyc`
- ❌ `.git/`
- ❌ 数据文件

## 🚀 下一步

1. **更新 pyproject.toml** - 添加核心依赖
2. **测试构建** - `python -m build`
3. **TestPyPI 测试** - 先在测试环境发布
4. **正式发布** - `twine upload dist/*`
5. **验证安装** - `pip install dslighting`
6. **更新文档** - 告诉用户如何安装

---

**准备好发布了吗？按照上面的步骤，DSLighting 就可以发布到 PyPI 了！** 🎉
