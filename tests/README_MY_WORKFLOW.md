# 🎯 快速开始：创建自己的 Workflow

## ✅ 正确架构

```python
# 只依赖 dsat！
from dsat.workflows.base import DSATWorkflow
from dsat.services.llm import LLMService
from dsat.services.sandbox import SandboxService

class MyWorkflow(DSATWorkflow):
    async def solve(self, description, io_instructions, data_dir, output_path):
        # LLM + Sandbox
        pass
```

## 🚀 立即运行

```bash
python run_my_workflow_bike.py
```

会在 bike-sharing-demand 上运行您的自定义 workflow！

## 📁 核心文件

- `my_llm_workflow/workflow.py` - 只依赖 dsat
- `run_my_workflow_bike.py` - 运行脚本

## 💡 关键点

✓ 只依赖 dsat（不是 dslighting）
✓ 实现 DSATWorkflow 接口
✓ 使用 LLM + Sandbox
✓ 像 aide 一样使用
✓ 不需要修改源代码

**终于对了！**
