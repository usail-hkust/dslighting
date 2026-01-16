# Package Context Feature

## 概述

DSLighting v1.3.15+ 引入了**包上下文功能**，自动检测当前环境中可用的 Python 包，并将这些信息提供给 agent。这样 agent 就能知道哪些包可用，避免生成使用不存在包的代码导致编译错误。

## 功能特性

✅ **自动检测**: 扫描当前环境中所有已安装的包
✅ **智能分类**: 特别标注数据科学和机器学习相关的包
✅ **自动配置**: 首次安装时自动运行检测
✅ **灵活控制**: 可以全局或单独关闭此功能
✅ **配置持久化**: 包信息保存到 config.yaml

## 使用方法

### 1. 默认使用（推荐）

创建 Agent 时，包上下文**默认启用**：

```python
import dslighting

# 包上下文默认启用
agent = dslighting.Agent()

# Agent 现在知道环境中有哪些包
result = agent.run(task_id="bike-sharing-demand", data_dir="data/competitions")
```

Agent 会在任务描述中看到类似这样的信息：

```
Available Python packages in the current environment:

Data Science & ML Packages:
  - numpy (1.24.3)
  - pandas (2.0.2)
  - scikit-learn (1.3.0)
  - xgboost (2.0.2)
  - lightgbm (4.1.0)
  ...

Other Available Packages (showing top 20):
  - requests (2.31.0)
  - pyyaml (6.0.1)
  ...
```

这样 Agent 就知道可以使用 `xgboost` 和 `lightgbm`，而不会尝试使用未安装的 `catboost`。

### 2. 禁用包上下文

如果不需要这个功能，可以在创建 Agent 时关闭：

```python
import dslighting

# 禁用包上下文
agent = dslighting.Agent(include_package_context=False)

result = agent.run(task_id="bike-sharing-demand", data_dir="data/competitions")
```

### 3. 手动检测包

使用 CLI 命令手动检测和更新包信息：

```bash
# 检测并保存包信息
dslighting detect-packages

# 查看已检测的包
dslighting show-packages

# 验证配置
dslighting validate-config
```

## 配置文件

包信息保存在 `config.yaml` 中：

```yaml
available_packages:
  enabled: true  # 全局开关
  packages:
    numpy: "1.24.3"
    pandas: "2.0.2"
    scikit-learn: "1.3.0"
    xgboost: "2.0.2"
    lightgbm: "4.1.0"
    # ... 更多包
  last_updated: 1705392000.0
```

### 全局禁用

要全局禁用包上下文，修改 `config.yaml`：

```yaml
available_packages:
  enabled: false
```

## 工作原理

1. **首次安装**: 运行 `scripts/setup_package_context.py` 自动检测
2. **初始化**: Agent 启动时读取包信息
3. **任务执行**: 将包列表添加到任务描述的开头
4. **Agent感知**: LLM 看到可用包列表，生成兼容代码

## 示例对比

### ❌ 没有包上下文（之前）

Agent 可能生成这样的代码：

```python
import catboost  # ❌ 未安装！
from catboost import CatBoostRegressor

model = CatBoostRegressor()
model.fit(X_train, y_train)
```

运行时会报错：`ModuleNotFoundError: No module named 'catboost'`

### ✅ 有包上下文（现在）

Agent 知道只有 `xgboost` 和 `lightgbm`，生成：

```python
import xgboost as xgb  # ✅ 已安装
from xgboost import XGBRegressor

model = XGBRegressor()
model.fit(X_train, y_train)
```

代码可以正常运行！

## 高级用法

### 检测特定包

```python
from dslighting.utils.package_detector import PackageDetector

detector = PackageDetector()

# 获取所有包
all_packages = detector.detect_packages()

# 只获取数据科学包
ds_packages = detector.get_data_science_packages()

# 格式化为上下文字符串
context = detector.format_as_context()
print(context)
```

### 保存到自定义配置

```python
from pathlib import Path
from dslighting.utils.package_detector import PackageDetector

detector = PackageDetector()
packages = detector.detect_packages()

# 保存到自定义路径
config_path = Path("/custom/path/config.yaml")
detector.save_to_config(config_path, packages)
```

### 从配置加载

```python
from pathlib import Path
from dslighting.utils.package_detector import PackageDetector

detector = PackageDetector()

# 从配置加载
config_path = Path("config.yaml")
packages = detector.load_from_config(config_path)

if packages:
    print(f"Loaded {len(packages)} packages")
```

## 数据科学包列表

默认检测的数据科学包包括：

- **基础**: pandas, numpy, scipy
- **可视化**: matplotlib, seaborn, plotly, bokeh
- **机器学习**: scikit-learn, xgboost, lightgbm, catboost
- **深度学习**: torch, tensorflow, keras
- **NLP**: transformers, datasets, nltk, spacy
- **统计**: statsmodels
- **数据处理**: polars, pyarrow, dask

## 故障排查

### 包信息未检测到

```bash
# 手动重新检测
dslighting detect-packages

# 检查配置文件
dslighting validate-config

# 查看检测到的包
dslighting show-packages
```

### Agent 没有使用包信息

1. 检查 `include_package_context` 是否为 `True`（默认）
2. 查看 agent 日志，确认有 "Package context added to task description"
3. 验证 config.yaml 中的 `available_packages.enabled` 为 `true`

### 包版本不准确

包信息是在安装/检测时的快照。如果环境有变化：

```bash
# 重新检测
dslighting detect-packages
```

## 性能影响

- **初始化**: 增加约 0.1-0.5 秒（首次检测包）
- **内存影响**: 可忽略（只存储包名和版本）
- **Token 使用**: 每个任务增加约 200-500 tokens（取决于包数量）

## 最佳实践

1. **首次设置**: 安装后运行 `dslighting detect-packages`
2. **定期更新**: 当安装新包后重新检测
3. **生产环境**: 可以禁用以减少 token 使用
4. **开发环境**: 保持启用以获得最佳体验

## 版本要求

- DSLighting >= 1.3.15
- Python >= 3.10

## 相关文档

- [Package Detector API](dslighting/utils/package_detector.py)
- [Agent Configuration](dslighting/core/agent.py)
- [CLI Reference](dslighting_cli.py)

## 反馈

如果有问题或建议，请提交 issue:
https://github.com/usail-hkust/dslighting/issues
