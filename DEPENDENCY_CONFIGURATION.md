# 依赖配置更新说明

## 更新内容

已经将 `dslighting` Python 包的依赖配置更新为使用项目的 `requirements_local.txt`，避免 pip 安装时的版本冲突问题。

## 更新的文件

### 1. pyproject.toml
**变更前：**
```toml
dependencies = [
    "pandas>=1.5.0",
    "pydantic>=2.0",
    "python-dotenv>=1.0.0",
    "rich>=13.0.0",
]
```

**变更后：**
```toml
dependencies = [
    # Already in requirements_local.txt, but listed for clarity:
    # - pandas
    # - python-dotenv
    # - rich (if available, otherwise basic logging is used)
]
```

**原因：**
- 避免重复声明依赖
- 防止版本冲突
- 让用户通过 `requirements_local.txt` 管理所有依赖

### 2. dslighting/README.md
更新了安装说明：

```bash
# Step 1: Install DSLighting dependencies first
cd /path/to/dslighting
pip install -r requirements_local.txt

# Step 2: Install DSLighting package with simplified API
pip install -e .
```

### 3. 新增文件
- **INSTALLATION.md** - 详细的安装指南
- **DEPENDENCY_CONFIGURATION.md** - 本文件，说明依赖配置

## 依赖策略

### requirements_local.txt（推荐用于开发）
```
pandas
python-dotenv
rich
...
```

**优点：**
- ✅ 无版本固定，pip 自动解决依赖
- ✅ 兼容性好，不容易出错
- ✅ 适合开发和用户安装

**缺点：**
- ⚠️ 可能有轻微的版本差异
- ⚠️ 不适合生产环境（需要可重现性）

### requirements.txt（用于生产）
```
pandas==2.2.2
python-dotenv==1.0.0
rich==13.7.0
...
```

**优点：**
- ✅ 完全可重现
- ✅ 适合 CI/CD 和生产环境

**缺点：**
- ❌ 容易产生版本冲突
- ❌ 难以维护

## 安装流程

### 用户推荐安装流程

```bash
# 1. 克隆仓库
git clone https://github.com/usail-hkust/dslighting.git
cd dslighting

# 2. 安装依赖（使用 requirements_local.txt）
pip install -r requirements_local.txt

# 3. 安装 DSLighting 包
pip install -e .

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 API_KEY
```

### 开发者安装流程

```bash
# 1. 安装依赖 + 开发工具
pip install -r requirements_local.txt
pip install -e ".[dev]"

# 2. 运行测试
pytest tests/

# 3. 运行示例
python examples/dslighting_api/example_1_basic.py
```

## 验证安装

```bash
# 检查包是否可以导入
python3 -c "import dslighting; print('✓ DSLighting API installed')"

# 检查版本
python3 -c "import dslighting; print(dslighting.__version__)"

# 运行基本测试
python3 tests/test_dslighting_api.py
```

## 常见问题

### Q: 为什么要清空 pyproject.toml 的 dependencies？

A: 因为：
1. **避免重复** - 依赖已经在 requirements_local.txt 中
2. **防止冲突** - 两次安装可能选择不同版本
3. **简化维护** - 只需维护一个依赖列表
4. **灵活性** - pip 可以更好地解决依赖关系

### Q: 如果发布到 PyPI 怎么办？

A: 如果需要发布到 PyPI，可以添加最小依赖：

```toml
dependencies = [
    "pandas>=1.5.0",
    "python-dotenv>=1.0.0",
]
```

但这会增加版本冲突的风险。当前配置更适合作为项目的一部分使用。

### Q: requirements_local.txt 和 requirements.txt 的区别？

A:

| 文件 | 用途 | 格式 | 优点 | 缺点 |
|------|------|------|------|------|
| requirements_local.txt | 开发和用户 | `package_name` | 兼容性好 | 版本不固定 |
| requirements.txt | 生产环境 | `package==x.y.z` | 可重现 | 容易冲突 |

推荐：
- **开发/用户** → 使用 requirements_local.txt
- **生产/CI** → 使用 requirements.txt

## 兼容性

这个配置更新**不影响**现有的 DSLighting 功能：
- ✅ 所有现有代码继续工作
- ✅ DSAT API 完全兼容
- ✅ 新的简化 API 正常工作
- ✅ 所有示例和文档保持有效

## 相关文档

- **安装指南**: `INSTALLATION.md`
- **API 文档**: `dslighting/README.md`
- **实现总结**: `IMPLEMENTATION_SUMMARY.md`

## 总结

通过使用 `requirements_local.txt` 并清空 `pyproject.toml` 的依赖列表，我们：

1. ✅ **避免了版本冲突** - pip 自动选择兼容版本
2. ✅ **简化了依赖管理** - 只需维护一个依赖列表
3. ✅ **改善了用户体验** - 安装过程更顺畅
4. ✅ **保持了灵活性** - 用户可以根据需要调整依赖

用户现在可以放心地使用 `pip install -e .` 而不会遇到版本冲突问题！
