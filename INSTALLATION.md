# DSLighting 安装指南

## 推荐安装方式

### 1. 完整安装（用于开发和使用）

```bash
# 克隆仓库
git clone https://github.com/usail-hkust/dslighting.git
cd dslighting

# 安装所有依赖（使用无版本限制的依赖列表）
pip install -r requirements_local.txt

# 安装 DSLighting 包（包含简化的 API）
pip install -e .
```

### 2. 开发环境安装

```bash
# 安装依赖 + 开发工具
pip install -r requirements_local.txt
pip install -e ".[dev]"
```

## 依赖说明

DSLighting 项目使用两个依赖文件：

### requirements_local.txt（推荐）
- **无版本固定** - 使用 `pip install package_name` 格式
- **兼容性好** - pip 会自动解决版本冲突
- **适合用户** - 不会有版本冲突问题

### requirements.txt
- **固定版本** - 使用 `package_name==x.y.z` 格式
- **可重现** - 确保完全相同的依赖版本
- **适合生产** - 用于 CI/CD 和生产环境

## 简化的 API 包

新的 `dslighting` Python 包位于项目根目录，提供简化的 API：

```python
import dslighting

# 一行代码运行
result = dslighting.run_agent("data/competitions/titanic")
```

**安装说明：**
- 该包**不重复安装依赖**
- 依赖已通过 `requirements_local.txt` 安装
- `pip install -e .` 只注册包的导入路径
- 避免版本冲突问题

## 验证安装

```bash
# 检查包是否安装成功
python3 -c "import dslighting; print(dslighting.__version__)"

# 运行基本测试
python3 tests/test_dslighting_api.py
```

## 常见问题

### Q: 为什么不直接在 pyproject.toml 中列出所有依赖？

A: 因为：
1. **避免重复** - 依赖已经在 requirements_local.txt 中
2. **版本冲突** - 两次安装可能产生不同的版本
3. **灵活性** - requirements_local.txt 更容易更新
4. **兼容性** - 让 pip 自动解决依赖关系

### Q: pip install -e . 会不会重新安装依赖？

A: **不会**。我们已经在 `pyproject.toml` 中清空了依赖列表，所以：
- `pip install -e .` 只注册包的导入路径
- 不会重新安装 pandas, python-dotenv 等包
- 避免版本冲突

### Q: 如果我想发布到 PyPI 怎么办？

A: 如果需要发布到 PyPI，可以在 `pyproject.toml` 中添加核心依赖：

```toml
dependencies = [
    "pandas>=1.5.0",
    "python-dotenv>=1.0.0",
    "rich>=13.0.0",
]
```

但这会增加版本冲突的风险。

### Q: 如何升级依赖？

A: 使用 requirements_local.txt：

```bash
# 升级所有依赖到最新版本
pip install --upgrade -r requirements_local.txt

# 或者升级单个包
pip install --upgrade pandas
```

## 环境配置

安装完成后，需要配置环境变量：

```bash
# 必需：LLM API 密钥
export API_KEY="sk-..."

# 可选：LLM 模型
export LLM_MODEL="gpt-4o-mini"

# 可选：API 基础 URL（用于非 OpenAI 的服务）
export API_BASE="https://api.openai.com/v1"

# 可选：LLM 提供商（用于 LiteLLM）
export LLM_PROVIDER="openai"
```

或者创建 `.env` 文件：

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥
```

## 下一步

安装完成后，查看示例代码：

- **基础用法**: `examples/dslighting_api/example_1_basic.py`
- **高级用法**: `examples/dslighting_api/example_2_advanced.py`
- **迁移指南**: `examples/dslighting_api/example_3_migration.py`

或阅读完整的 API 文档：`dslighting/README.md`
