# 数据准备

DSLighting 支持多种数据来源和格式。

## MLE-Bench 数据集

### 安装 MLE-Bench

\`\`\`bash
git clone https://github.com/openai/mle-bench.git
cd mle-bench
pip install -e .
\`\`\`

### 下载数据集

\`\`\`bash
# 下载所有数据集
python scripts/prepare.py --competition all

# 下载特定竞赛
python scripts/prepare.py --competition bike-sharing-demand
\`\`\`

### 数据组织结构

\`\`\`
data/competitions/
  <竞赛ID>/
    config.yaml           # 竞赛配置文件
    prepared/
      public/            # 公开数据（训练集、样本提交）
      private/           # 私有数据（测试标签，用于评分）
\`\`\`

## 自定义数据集

### 创建自定义任务

1. 在 \`data/competitions/\` 下创建任务目录
2. 添加 \`config.yaml\` 配置文件
3. 组织训练数据和测试数据

### 配置文件示例

\`\`\`yaml
competition_id: my-custom-task
competition_name: My Custom Task
description: A custom machine learning task

dataset:
  train_file: train.csv
  test_file: test.csv
  target_column: target

evaluation:
  metric: accuracy
  higher_is_better: true
\`\`\`

## 数据格式要求

### 训练数据
- CSV 格式
- 包含特征列和目标列
- 建议提供数据描述文档

### 测试数据
- CSV 格式
- 与训练数据相同的特征列
- 不包含目标列

### 样本提交
- 包含 ID 列和预测列
- 符合提交格式要求

## 数据预处理

DSLighting 会自动进行：
- 缺失值处理
- 特征编码
- 数据清洗
- 特征工程

你也可以在 Agent 工作流中自定义预处理步骤。

查看[配置说明](/guide/configuration)了解更多细节。
