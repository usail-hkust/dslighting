# 统一 JSON 响应格式文档

## 概述

从现在开始，所有 web_ui 中的 agent 调用都将使用统一的 JSON Schema 格式响应。这样可以：

- ✅ **节省 Token**：不需要额外的 markdown 标记
- ✅ **规范化输出**：所有响应都有统一的结构
- ✅ **易于解析**：直接使用 Pydantic 模型解析
- ✅ **更好的错误处理**：可以验证响应格式

## 统一的 JSON Schema

### 1. CodeResponse（代码生成任务）

所有需要生成 Python 代码的任务使用此格式。

```json
{
  "thought": "Step-by-step reasoning for the proposed solution.",
  "code": "The complete, single-file Python script."
}
```

**使用场景**：
- 数据分析代码生成
- 数据准备代码生成
- EDA 代码生成
- 调试修复代码

### 2. ReportResponse（报告生成任务）

所有需要生成报告的任务使用此格式。

```json
{
  "thought": "Reasoning for the report structure and content.",
  "report_content": "The full markdown content of the report."
}
```

**使用场景**：
- EDA 报告生成
- 技术报告生成
- 分析总结生成

### 3. ChatResponse（通用对话任务）

所有一般性对话使用此格式。

```json
{
  "thought": "Step-by-step reasoning for the response.",
  "response": "The text response to the user.",
  "code": "Optional Python code if the response includes code."
}
```

**使用场景**：
- 一般性问答
- 任务建议
- 流程说明

## 实现细节

### 1. Pydantic 模型定义

位置：`backend/app/models/llm_formats.py`

```python
class CodeResponse(BaseModel):
    thought: str = Field(description="Step-by-step reasoning for the proposed solution.")
    code: str = Field(description="The complete, single-file Python script.")

class ReportResponse(BaseModel):
    thought: str = Field(description="Reasoning for the report structure and content.")
    report_content: str = Field(description="The full markdown content of the report.")

class ChatResponse(BaseModel):
    thought: str = Field(description="Step-by-step reasoning for the response.")
    response: str = Field(description="The text response to the user.")
    code: Optional[str] = Field(default=None, description="Optional Python code if the response includes code.")
```

### 2. 统一的 Prompt 模板

位置：`backend/app/prompts/agent_prompts.py`

所有 prompt 都会自动添加统一的 JSON Schema 要求：

```python
JSON_SCHEMA_REQUIREMENT = """
# RESPONSE FORMAT (MANDATORY)

You MUST respond with valid JSON ONLY. No markdown, no code blocks, no extra text.

**CRITICAL**: Output ONLY the raw JSON object. Do NOT wrap in ```json or ``` markdown blocks.
"""
```

### 3. LLM 调用方式

所有调用都使用 `call_with_json` 方法：

```python
# 代码任务
res_model = await llm.call_with_json(prompt, output_model=CodeResponse, system_message=system_prompt)
thought = res_model.thought
code = res_model.code

# 报告任务
res_model = await llm.call_with_json(prompt, output_model=ReportResponse, system_message=system_prompt)
thought = res_model.thought
content = res_model.report_content

# 对话任务
res_model = await llm.call_with_json(prompt, output_model=ChatResponse, system_message=system_prompt)
thought = res_model.thought
response = res_model.response
code = res_model.code
```

## 修改文件列表

### 已修改的文件

1. **backend/app/models/llm_formats.py**
   - 添加了 `ChatResponse` 模型

2. **backend/app/services/chat_service.py**
   - 导入 `ChatResponse`
   - 将所有 `llm.call()` 改为 `llm.call_with_json()`
   - 添加通用的 JSON 格式提醒

3. **backend/app/prompts/agent_prompts.py**
   - 添加统一的 JSON Schema 要求
   - 更新 `_log_format` 函数自动添加 Schema

### 已经使用 JSON 格式的调用（chat_logic.py）

以下调用已经正确使用 JSON 格式，无需修改：

- `_update_chat_summary` → `ChatSummary`
- `_generate_task_blueprint` → `TaskBlueprint`
- `_refine_task_blueprint` → `TaskBlueprint`
- `_judge_blueprint_approval` → `BlueprintApproval`
- `_summarize_debug_history` → `DebugSummary`
- `_run_active_exploration` → `ExplorationAction`
- `_detect_intent` → `IntentResponse`
- Data Loading Guide → `DataLoadingGuide`

## Token 节省估算

### 之前（带 markdown）

```markdown
Here's my analysis:

```python
import pandas as pd
# ... 100 lines of code ...
```

This code does the following:
- Step 1: Load data
- Step 2: Process data
- Step 3: Save results
```

**Token 估算**: ~500 tokens (包含大量 markdown 和解释性文字)

### 现在（纯 JSON）

```json
{"thought":"Load data, process, save results","code":"import pandas as pd\n#..."}
```

**Token 估算**: ~150 tokens (纯 JSON，去除冗余)

**节省**: ~70% tokens

## 验证和测试

### 测试步骤

1. 启动后端服务：
   ```bash
   cd web_ui/backend
   python main.py
   ```

2. 在前端测试不同功能：
   - 数据探索（对话）
   - 代码生成
   - 报告生成

3. 检查后端日志，确认使用 `call_with_json`

### 预期行为

- 所有 LLM 调用都应该是 JSON 格式
- 日志中应显示 "Calling LLM with JSON format"
- 没有解析错误
- 响应时间应该更快（token 更少）

## 常见问题

### Q: 如果 LLM 返回 markdown 包裹的 JSON 怎么办？

A: `call_with_json` 方法会自动处理，提取纯 JSON。

### Q: 如何调试 JSON 格式问题？

A: 查看后端日志中的 "LLM call failed" 错误，会显示具体的验证错误。

### Q: 能否添加新的响应格式？

A: 可以。在 `llm_formats.py` 中定义新的 Pydantic 模型，然后在相应的 prompt 中说明即可。

## 总结

所有 web_ui 的 agent 调用现在都使用统一的 JSON Schema 格式，实现了：

- ✅ 规范化
- ✅ Token 优化
- ✅ 类型安全
- ✅ 易于维护
