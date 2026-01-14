# 数据准备指南

本文档详细说明如何为DSLighting准备数据。

---

## 📊 数据来源

DSLighting支持多种数据来源，您可以根据需求选择最适合的方式。

### 1. MLE-Bench数据集（推荐）

**[MLE-Bench](https://github.com/openai/mle-bench)** 是OpenAI提供的机器学习评估基准，包含多个真实的Kaggle竞赛任务。

#### 支持的任务类型

- **回归任务**: 房价预测、自行车租赁需求预测
- **分类任务**: 泰坦尼克号生存预测、客户流失预测
- **时序预测**: 销量预测、股票价格预测
- **多标签分类**: 图像标签分类、文本分类

#### 安装步骤

```bash
# 1. 激活DSLighting虚拟环境
source /path/to/dslighting/dslighting/bin/activate

# 2. 克隆MLE-Bench仓库（与dslighting同级目录）
cd /path/to
git clone https://github.com/openai/mle-bench.git
cd mle-bench

# 3. 安装MLE-Bench依赖
pip install -e .

# 4. 下载所有竞赛数据
python scripts/prepare.py --competition all

# 数据将下载到 ~/mle-bench/data/competitions/
```

#### 链接到DSLighting

```bash
# 创建符号链接（推荐，节省磁盘空间）
cd /path/to/dslighting/data
ln -s ~/mle-bench/data/competitions competitions

# 或者复制数据（占用更多空间但更独立）
# cp -r ~/mle-bench/data/competitions /path/to/dslighting/data/
```

#### 验证数据

```bash
# 查看可用的竞赛
ls /path/to/dslighting/data/competitions/
# 输出: bike-sharing-demand/ titanic/ house-prices/ ...

# 检查单个竞赛结构
ls /path/to/dslighting/data/competitions/bike-sharing-demand/
# 输出: config.yaml description.md prepare.py grade.py prepared/

# 检查prepared目录
ls /path/to/dslighting/data/competitions/bike-sharing-demand/prepared/
# 输出: public/ private/
```

---

### 2. 自定义数据集

如果您有自己的数据集，可以按照DSLighting的格式进行组织。

#### 数据目录结构

```
data/competitions/
  <your-competition-id>/
    ├── config.yaml           # 竞赛配置（必需）
    ├── description.md        # 任务描述（可选）
    ├── prepare.py            # 数据准备脚本（可选）
    ├── grade.py              # 评分脚本（可选）
    └── prepared/
        ├── public/           # 公开数据
        │   ├── train.csv     # 训练数据
        │   ├── test.csv      # 测试数据
        │   └── sample_submission.csv  # 样本提交
        └── private/          # 私有数据
            └── answer.csv    # 测试集答案
```

#### config.yaml示例

```yaml
id: my-custom-task
name: My Custom Competition
competition_type: kaggle

grader:
  name: rmse  # 或 accuracy, f1, mae 等
  grade_fn: competitions.my_custom_task.grade:grade

preparer: competitions.my_custom_task.prepare:prepare
```

#### prepare.py示例

```python
from pathlib import Path

def prepare(raw: Path, public: Path, private: Path):
    """
    将原始数据分割为训练集和测试集

    Args:
        raw: 原始数据目录
        public: 公开数据输出目录
        private: 私有数据输出目录
    """
    import pandas as pd
    from sklearn.model_selection import train_test_split

    # 读取原始数据
    df = pd.read_csv(raw / "data.csv")

    # 分割训练集和测试集
    train, test = train_test_split(df, test_size=0.2, random_state=42)

    # 保存训练数据
    train.to_csv(public / "train.csv", index=False)

    # 保存测试数据（不含标签）
    test_features = test.drop('target', axis=1)
    test_features.to_csv(public / "test.csv", index=False)

    # 保存测试集答案
    test_labels = test[['id', 'target']]
    test_labels.to_csv(private / "answer.csv", index=False)

    # 生成样本提交文件
    sample_submission = test_features.copy()
    sample_submission['target'] = 0  # 默认值
    sample_submission.to_csv(public / "sample_submission.csv", index=False)
```

#### grade.py示例

```python
import pandas as pd
import numpy as np

def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    """
    计算提交结果的评分

    Args:
        submission: 用户提交的预测结果
        answers: 正确答案

    Returns:
        评分（RMSE）
    """
    # 合并提交和答案
    merged = submission.merge(answers, on='id')

    # 计算RMSE
    rmse = np.sqrt(np.mean((merged['target_x'] - merged['target_y'])**2))

    return rmse
```

---

### 3. Web UI上传（快速测试）

使用Web UI界面上传小型数据集进行快速测试。

#### 步骤

1. **启动服务**
   ```bash
   # 终端1：启动后端
   cd /path/to/dslighting
   source dslighting/bin/activate
   cd web_ui/backend
   python main.py

   # 终端2：启动前端
   cd /path/to/dslighting/web_ui/frontend
   npm run dev
   ```

2. **访问界面**
   - 打开浏览器访问：http://localhost:3000

3. **上传数据**
   - 点击"上传数据集"按钮
   - 选择训练数据文件（CSV格式）
   - 选择测试数据文件（CSV格式）
   - 填写任务描述
   - 点击"开始处理"

4. **自动处理**
   - 系统自动创建数据目录
   - 生成config.yaml配置文件
   - 组织数据结构

---

## 📦 数据格式要求

### CSV文件格式

#### 训练数据 (train.csv)

```csv
id,feature1,feature2,feature3,target
1,0.5,1.2,3.4,100
2,0.3,1.5,2.1,200
3,0.8,0.9,4.5,150
```

**要求**：
- 第一列为ID列（可选）
- 最后一列为目标列（标签）
- 中间列为特征列
- 使用逗号分隔
- 包含表头

#### 测试数据 (test.csv)

```csv
id,feature1,feature2,feature3
4,0.6,1.1,3.2
5,0.4,1.3,2.5
```

**要求**：
- 与训练数据特征列相同
- 不包含目标列
- 包含ID列用于匹配答案

#### 提交格式 (sample_submission.csv)

```csv
id,target
4,0
5,0
```

**要求**：
- 包含ID列
- 包含预测目标列
- 初始值可以是0、均值或中位数

#### 答案文件 (answer.csv)

```csv
id,target
4,120
5,180
```

**要求**：
- 包含ID列
- 包含真实目标值
- 仅用于评分，对Agent不可见

---

## 🎯 支持的任务类型

### 当前支持

| 任务类型 | 评分指标 | 示例数据集 |
|---------|---------|-----------|
| **回归** | RMSE, MAE, R² | 房价预测、销量预测 |
| **二分类** | Accuracy, F1, AUC-ROC | 泰坦尼克生存预测 |
| **多分类** | Accuracy, Log Loss | 手写数字识别 |
| **多标签分类** | F1-macro, F1-micro | 图像标签分类 |

### 即将支持

- 🔜 **时序预测**: ARIMA、LSTM、Transformer
- 🔜 **推荐系统**: NDCG、Hit Rate
- 🔜 **强化学习**: Reward、Episode Length
- 🔜 **多模态**: 图像+文本联合任务

---

## 🔧 数据预处理建议

### 特征工程

```python
# 处理缺失值
df.fillna(df.mean(), inplace=True)

# 特征标准化
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
df[features] = scaler.fit_transform(df[features])

# 类别编码
from sklearn.preprocessing import LabelEncoder
le = LabelEncoder()
df['category'] = le.fit_transform(df['category'])
```

### 数据验证

```python
# 检查数据完整性
assert train_df.isnull().sum().sum() == 0, "训练集有缺失值"
assert test_df.isnull().sum().sum() == 0, "测试集有缺失值"

# 检查特征一致性
assert set(train_df.columns) - {'target'} == set(test_df.columns), "特征不一致"

# 检查ID唯一性
assert train_df['id'].is_unique, "训练集ID有重复"
assert test_df['id'].is_unique, "测试集ID有重复"
```

---

## ❓ 常见问题

### Q1: MLE-Bench下载失败怎么办？

**解决方案**：

```bash
# 单独下载某个竞赛
python scripts/prepare.py --competition bike-sharing-demand

# 使用镜像站点（如果可用）
export MLE_BENCH_MIRROR=https://mirror.example.com
python scripts/prepare.py --competition all
```

### Q2: 数据集太大怎么办？

**解决方案**：

```bash
# 下载部分竞赛
python scripts/prepare.py --competition bike-sharing-demand,titanic

# 或者创建子采样
python scripts/subsample_data.py --competition bike-sharing-demand --ratio 0.1
```

### Q3: 如何使用自己的数据？

**解决方案**：

1. 按照上述"自定义数据集"章节组织数据
2. 编写对应的config.yaml、prepare.py、grade.py
3. 将数据放置在`data/competitions/<your-task-id>/`
4. 通过Web UI或命令行运行任务

### Q4: 数据格式不兼容？

**解决方案**：

```python
# 转换数据格式
import pandas as pd

# 读取Excel
df = pd.read_excel('data.xlsx')
df.to_csv('data.csv', index=False)

# 读取JSON
df = pd.read_json('data.json')
df.to_csv('data.csv', index=False)
```

---

## 📚 相关文档

- [主README](../README.md) - 项目概述
- [配置指南](../SETUP_GUIDE.md) - 环境配置
- [MLE-Bench文档](https://github.com/openai/mle-bench) - MLE-Bench官方文档
- [数据格式规范](./DATA_FORMAT.md) - 详细格式说明（待补充）

---

## 🚀 下一步

数据准备完成后：

1. **测试数据加载**
   ```bash
   python -c "from dsat.benchmark.mle import MLEBenchmark; print('✅ 数据加载成功')"
   ```

2. **运行示例任务**
   ```bash
   python run_benchmark.py --workflow aide --benchmark mle --task-id bike-sharing-demand
   ```

3. **使用Web UI**
   - 访问 http://localhost:3000
   - 在界面中选择任务并运行

---

**祝您使用愉快！** 🎉
