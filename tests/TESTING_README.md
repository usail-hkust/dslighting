# DSLighting 测试脚本使用指南

## 文件说明

### 1. `test_single_workflow.py` - 单个 Workflow 测试

测试单个 workflow 的完整流程，包括数据加载、agent 创建和运行。

**使用方法：**
```bash
# 1. 配置 API key
cp .env.example .env
# 编辑 .env 文件，填入你的 API keys

# 2. 激活虚拟环境（如果需要）
source dslighting-env-v2/bin/activate

# 3. 运行测试
python test_single_workflow.py

# 或者修改脚本中的 WORKFLOW_NAME 变量测试其他 workflow
# WORKFLOW_NAME = "autokaggle"  # 或 data_interpreter, automind, dsagent, deepanalyze
```

**配置项（在脚本中修改）：**
```python
WORKFLOW_NAME = "aide"  # 要测试的 workflow
MODEL = "openai/deepseek-ai/DeepSeek-V3.1-Terminus"  # 使用的模型
TEMPERATURE = 0.7  # 温度参数
MAX_ITERATIONS = 1  # 最大迭代次数
```

**输出文件：**
- `test_result_{workflow}_{timestamp}.txt` - 测试结果
- `test_error_{workflow}_{timestamp}.md` - 错误报告（如果失败）

---

### 2. `test_all_workflows_batch.py` - 批量测试

一次性测试所有 6 个 workflows。

**使用方法：**
```bash
# 1. 配置 API key
cp .env.example .env
# 编辑 .env 文件

# 2. 激活虚拟环境
source dslighting-env-v2/bin/activate

# 3. 运行批量测试
python test_all_workflows_batch.py
```

**输出文件：**
- `test_report_batch_{timestamp}.md` - 测试报告

---

## 环境要求

### Python 版本
- Python >= 3.10（DSLighting 1.8.3 要求）

### 虚拟环境
推荐使用 `dslighting-env-v2`（已安装 DSLighting 1.8.3）

```bash
# 创建虚拟环境（如果还没有）
python3.10 -m venv dslighting-env-v2

# 激活虚拟环境
source dslighting-env-v2/bin/activate

# 安装 DSLighting
pip install dslighting
```

---

## API Key 配置

### 方式 1：使用 .env 文件（推荐）

```bash
# 复制模板
cp .env.example .env

# 编辑 .env 文件
nano .env  # 或使用其他编辑器
```

在 `.env` 文件中配置：
```bash
# OpenAI API Key
OPENAI_API_KEY=sk-your-openai-api-key-here

# DeepSeek API Key（如果使用）
DEEPSEEK_API_KEY=your-deepseek-api-key-here
```

### 方式 2：环境变量

```bash
export OPENAI_API_KEY="your-api-key-here"
python test_single_workflow.py
```

---

## 测试流程说明

### 单个 Workflow 测试流程

1. **加载数据集信息**
   - 使用 `dslighting.datasets.load_bike_sharing_demand()` 加载数据集信息
   - 获取数据目录和任务 ID

2. **加载数据**
   - 使用 `dslighting.load_data()` 加载数据
   - 创建 `LoadedData` 对象

3. **创建 Agent**
   - 使用 `dslighting.Agent()` 创建 agent
   - 配置 workflow、model、temperature 等参数

4. **运行 Agent**
   - 调用 `agent.run(data)` 执行任务
   - 等待执行完成

5. **查看结果**
   - 检查 `result.score` 是否有值
   - **有 Score = 成功**
   - **无 Score = 需要检查配置**

---

## 结果判断标准

### ✅ 成功（有 Score）
```
✓ Success: True
✓ Score: 0.8567  ← 必须有这个值！
✓ Cost: $0.2345
✓ Duration: 125.3s

✅✅✅ 测试成功！✅✅✅
   Agent 成功完成任务并获得分数: 0.8567
```

### ⚠️ 部分成功（无 Score）
```
✓ Success: True
✓ Score: None  ← 没有分数！
✓ Cost: $0.0000
✓ Duration: 0.2s

⚠️  部分成功
   Agent 运行完成但没有获得分数
   可能原因: API key 未配置或 LLM 调用失败
```

### ❌ 失败
```
✗ Error: AuthenticationError: API key not found
```

---

## 常见问题

### Q1: 没有获得分数（Score = None）

**可能原因：**
1. API key 未配置或无效
2. Model 名称错误
3. 网络连接问题
4. LLM API 调用失败

**解决方法：**
1. 检查 `.env` 文件是否正确配置
2. 验证 API key 是否有效
3. 确认 model 参数是否正确
4. 检查网络连接

---

### Q2: Agent 创建失败

**可能原因：**
1. Workflow 名称拼写错误
2. DSLighting 版本不支持该 workflow

**解决方法：**
1. 检查 workflow 名称：
   - `aide`
   - `autokaggle`
   - `data_interpreter`
   - `automind`
   - `dsagent`
   - `deepanalyze`

2. 更新 DSLighting：
   ```bash
   pip install --upgrade dslighting
   ```

---

### Q3: 数据加载失败

**可能原因：**
1. DSLighting 未正确安装
2. 内置数据集损坏

**解决方法：**
1. 重新安装 DSLighting：
   ```bash
   pip uninstall dslighting
   pip install dslighting
   ```

2. 使用自定义数据路径（高级用法）

---

## 支持的 Workflows

| Workflow | 说明 | 配置参数 |
|----------|------|----------|
| `aide` | AIDE 工作流 | num_drafts |
| `autokaggle` | AutoKaggle 工作流 | autokaggle_max_attempts_per_phase, autokaggle_success_threshold |
| `data_interpreter` | Data Interpreter 工作流 | 无特殊参数 |
| `automind` | AutoMind 工作流 | case_dir |
| `dsagent` | DS-Agent 工作流 | case_dir |
| `deepanalyze` | DeepAnalyze 工作流 | 无特殊参数 |

---

## 示例输出

### 成功的测试输出

```
================================================================================
DSLighting 单 Workflow 测试
================================================================================
Workflow: aide
Model: openai/deepseek-ai/DeepSeek-V3.1-Terminus
Max Iterations: 1
开始时间: 2026-01-17T18:00:00.000000
================================================================================

步骤 1: 加载数据集信息...
--------------------------------------------------------------------------------
✓ 数据目录: /path/to/dslighting/datasets/bike-sharing-demand
✓ 任务 ID: bike-sharing-demand

步骤 2: 加载数据...
--------------------------------------------------------------------------------
✓ 数据已加载
  - 任务类型: kaggle
  - 任务 ID: bike-sharing-demand

步骤 3: 创建 aide Agent...
--------------------------------------------------------------------------------
✓ Agent 创建成功

步骤 4: 运行 Agent...
--------------------------------------------------------------------------------
⏳ 开始执行任务（这可能需要几分钟）...

[Agent 运行日志...]

================================================================================
执行结果
================================================================================
✓ Success: True
✓ Score: 0.8567
✓ Cost: $0.2345
✓ Duration: 125.3s
✓ Workspace: /path/to/workspace

✅✅✅ 测试成功！✅✅✅
   Agent 成功完成任务并获得分数: 0.8567

================================================================================

✓ 结果已保存: test_result_aide_20260117_180000.txt
```

---

## 高级用法

### 自定义数据路径

```python
# 加载自定义数据
info = dslighting.datasets.load_bike_sharing_demand()
data = dslighting.load_data(info['data_dir'])  # 使用 data_dir 而不是 parent

# 或者直接指定路径
data = dslighting.load_data("/path/to/your/data")
```

### 修改参数

```python
agent = dslighting.Agent(
    workflow="aide",
    model="openai/gpt-4o-mini",
    temperature=0.7,
    max_iterations=3,  # 增加迭代次数
    num_drafts=5,  # 增加草稿数量
    keep_workspace=True
)
```

---

## 联系与支持

如有问题，请查看：
- DSLighting 文档
- GitHub Issues
- 错误日志文件
