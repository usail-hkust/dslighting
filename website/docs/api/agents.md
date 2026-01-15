# Agent 工作流 API

DSLIGHTING 支持多种智能体工作流，每种工作流都有其特点和适用场景。

## AIDE

**迭代式代码生成和审查循环**

### 特点
- 持续的代码改进
- 自动代码审查
- 性能优化迭代

### 使用方法

\`\`\`bash
python run_benchmark.py \\
  --workflow aide \\
  --max-iterations 10 \\
  --review-threshold 0.8
\`\`\`

### 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| \`max_iterations\` | 最大迭代次数 | 10 |
| \`temperature\` | LLM 温度参数 | 0.7 |
| \`review_threshold\` | 代码审查通过阈值 | 0.8 |

## Automania

**带记忆和任务分解的规划系统**

### 特点
- 复杂任务分解
- 上下文记忆管理
- 多步骤推理

### 使用方法

\`\`\`bash
python run_benchmark.py \\
  --workflow automind \\
  --planning-iterations 3
\`\`\`

### 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| \`planning_iterations\` | 规划迭代次数 | 3 |
| \`memory_size\` | 记忆窗口大小 | 10 |

## DSAgent

**结构化操作符流程**

### 特点
- 清晰的任务分解
- 结构化执行步骤
- 灵活的操作符组合

### 使用方法

\`\`\`bash
python run_benchmark.py \\
  --workflow dsagent \\
  --max-steps 20
\`\`\`

### 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| \`max_steps\` | 最大执行步骤 | 20 |
| \`execution_timeout\` | 单步超时时间(秒) | 300 |

## Data Interpreter

**快速代码执行和调试**

### 特点
- 快速代码迭代
- 自动错误修复
- 实时调试

### 使用方法

\`\`\`bash
python run_benchmark.py \\
  --workflow data_interpreter \\
  --debug-mode true
\`\`\`

### 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| \`debug_mode\` | 调试模式开关 | false |
| \`max_retries\` | 最大重试次数 | 3 |

## AFlow

**元优化工作流**

### 特点
- 自动工作流选择
- 性能评估
- 策略优化

### 使用方法

\`\`\`bash
python run_benchmark.py \\
  --workflow aflow \\
  --meta-iterations 5
\`\`\`

### 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| \`meta_iterations\` | 元优化迭代次数 | 5 |
| \`candidate_workflows\` | 候选工作流列表 | ["aide", "dsagent"] |

## 选择合适的工作流

根据任务类型选择合适的工作流：

- **简单任务**: Data Interpreter
- **代码优化**: AIDE
- **复杂规划**: Automania / DSAgent
- **性能优化**: AFlow
- **竞赛任务**: AutoKaggle

返回 [API 概览](/api/overview)
