# 快速开始指南 - 5 分钟创建你的自定义 Agent

## 🚀 立即开始

### 步骤 1: 准备环境（已完成 ✅）
```bash
# 环境已经创建好了
cd /Users/liufan/Applications/Github/test_pip_dslighting
source intelligent_tool_selector_env/bin/activate
```

### 步骤 2: 运行示例（已完成 ✅）
```bash
python main.py
```

### 步骤 3: 创建你自己的 Agent

#### 方法 A: 修改现有 Agent

```python
# my_agent.py
import sys
sys.path.insert(0, '/Users/liufan/Applications/Github/test_pip_dslighting/my_custom_agent')

from my_custom_agent import MyCustomAgent
import dslighting

# 1. 加载数据
data = dslighting.load_data("bike-sharing-demand")

# 2. 创建并运行 Agent
agent = MyCustomAgent(
    target_column="count",  # 你的目标列
    n_estimators=100        # 树的数量
)

result = agent.run(str(data.data_dir))

# 3. 查看结果
print(f"R²: {result['metrics']['r2']:.4f}")
```

#### 方法 B: 从零开始

```python
# simple_agent.py
from dslighting import Action, Context, Tool
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor

# 1. 定义工具
def load_csv(path):
    return pd.read_csv(path)

def train_model(X, y):
    model = RandomForestRegressor()
    model.fit(X, y)
    return model

# 2. 封装成 Tool
load_tool = Tool(name="load", description="Load CSV", fn=load_csv)
train_tool = Tool(name="train", description="Train model", fn=train_model)

# 3. 创建 Agent
class SimpleAgent:
    def __init__(self):
        self.tools = {"load": load_tool, "train": train_tool}

    def run(self, data_path):
        # 加载数据
        data = self.tools["load"](data_path)

        # 训练模型
        X = data.drop("target", axis=1)
        y = data["target"]
        model = self.tools["train"](X, y)

        return model

# 4. 使用
agent = SimpleAgent()
model = agent.run("data.csv")
```

## 📝 常用代码片段

### 1. 加载不同类型的数据
```python
# Kaggle 数据集
data = dslighting.load_data("bike-sharing-demand")

# 本地 CSV 文件
data = dslighting.load_data("path/to/data.csv")

# DataFrame
df = pd.read_csv("data.csv")
data = dslighting.load_data(df)
```

### 2. 自定义目标列
```python
agent = MyCustomAgent(
    target_column="price",  # 指定目标列名
    n_estimators=200
)
```

### 3. 添加自定义工具
```python
def my_preprocessing(df):
    # 你的预处理逻辑
    df["new_feature"] = df["col1"] * df["col2"]
    return df

# 在 agent.py 的 _init_tools() 中添加
self.tools["preprocess"] = Tool(
    name="preprocess",
    description="Custom preprocessing",
    fn=my_preprocessing
)
```

### 4. 保存和加载模型
```python
# 训练并保存
agent = MyCustomAgent()
agent.run("data.csv")
agent.save_model("my_model.pkl")

# 加载模型
new_agent = MyCustomAgent()
new_agent.load_model("my_model.pkl")
predictions = new_agent.predict(X_test)
```

## 🔧 调试技巧

### 打印中间结果
```python
# 在 agent.py 的 _update_state() 中添加
def _update_state(self, tool_name, result):
    if tool_name == "clean_data":
        print(f"清洗后数据形状: {result.shape}")
        print(f"缺失值: {result.isnull().sum().sum()}")
```

### 查看可用的工具
```python
agent = MyCustomAgent()
print(f"可用工具: {list(agent.tools.keys())}")
# ['load_data', 'clean_data', 'analyze_data', 'prepare_data', 'train_model', 'evaluate_model', 'predict']
```

### 获取训练摘要
```python
agent = MyCustomAgent()
agent.run("data.csv")

summary = agent.get_summary()
for key, value in summary.items():
    print(f"{key}: {value}")
```

## 💡 实用示例

### 示例 1: 房价预测
```python
# house_prices.py
import dslighting
from my_custom_agent import MyCustomAgent

data = dslighting.load_data("house-prices")
agent = MyCustomAgent(target_column="SalePrice", n_estimators=150)
result = agent.run(str(data.data_dir))

print(f"房价预测 R²: {result['metrics']['r2']:.4f}")
```

### 示例 2: 信用评分
```python
# credit_scoring.py
data = dslighting.load_data("credit-default")
agent = MyCustomAgent(target_column="default", n_estimators=200)
result = agent.run(str(data.data_dir))

print(f"信用评分准确率: {result['metrics']['accuracy']:.4f}")
```

### 示例 3: 批量处理多个数据集
```python
# batch_process.py
datasets = ["bike-sharing-demand", "house-prices", "titanic"]

for dataset in datasets:
    print(f"\n处理: {dataset}")
    data = dslighting.load_data(dataset)
    agent = MyCustomAgent(n_estimators=50)
    result = agent.run(str(data.data_dir))
    print(f"R²: {result['metrics']['r2']:.4f}")
```

## 🎯 不同场景的配置

### 快速原型（开发阶段）
```python
agent = MyCustomAgent(
    n_estimators=10,      # 少量树，快速迭代
    verbose=True          # 详细输出
)
```

### 生产部署
```python
agent = MyCustomAgent(
    n_estimators=200,     # 更多树，更好性能
    verbose=False         # 减少输出
)
```

### 调试模式
```python
agent = MyCustomAgent(
    n_estimators=5,       # 最小配置
    verbose=True          # 最大信息
)
```

## 📚 进阶：自定义工作流

### 修改工作流步骤
```python
# 在 agent.py 中修改
class MyCustomAgent:
    def __init__(self):
        # 自定义工作流
        self.workflow_steps = [
            "load_data",
            "custom_clean",      # 新步骤
            "feature_engineering", # 新步骤
            "train_model"
        ]
```

### 添加新的决策逻辑
```python
def _plan(self, step_name):
    # 自定义决策逻辑
    if "high_cardinality" in ctx.state["analysis"]:
        return Action(tool="target_encoding", args={...})
    else:
        return Action(tool="one_hot_encoding", args={...})
```

## 🐛 常见问题

### Q1: 找不到目标列
```python
# 如果目标列不存在，会自动使用最后一列
# 或者手动指定
agent = MyCustomAgent(target_column="your_column_name")
```

### Q2: 内存不足
```python
# 减少树的数量
agent = MyCustomAgent(n_estimators=50)

# 或使用数据采样
def sample_data(df, frac=0.5):
    return df.sample(frac=frac)
```

### Q3: 运行时间太长
```python
# 减少数据量或树的数量
agent = MyCustomAgent(n_estimators=50)

# 或使用更简单的模型
# 在 tools.py 中修改 train_model 使用更快的算法
```

## 📖 学习路径

### 初学者（1-2 天）
1. 运行 `main.py` 和 `examples/run_example.py`
2. 修改 `target_column` 和 `n_estimators`
3. 尝试不同的数据集

### 中级（1 周）
1. 添加自定义工具
2. 修改工作流步骤
3. 实现模型保存/加载
4. 编写单元测试

### 高级（2-4 周）
1. 实现 `DSATWorkflow` 接口
2. 集成到 DSLighting
3. 添加超参数调优
4. 实现模型解释
5. 发布到 PYPI

## 🎉 你已经准备好了！

现在就开始吧：
```bash
cd /Users/liufan/Applications/Github/test_pip_dslighting
python main.py
```

查看完整文档：
- README.md: `/Users/liufan/Applications/Github/test_pip_dslighting/my_custom_agent/README.md`
- 成功总结: `/Users/liufan/Applications/Github/test_pip_dslighting/SUCCESS_SUMMARY.md`

祝你使用愉快！🚀
