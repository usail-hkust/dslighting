# DSLighting v1.9.3 发布说明

## 🐛 Bug 修复

### DataInterpreter Workflow 在 macOS 上无法运行的问题

**问题描述**:
在 macOS 上使用 `data_interpreter` workflow 时，会出现 `RuntimeError: Worker process is not running.` 错误。

**原因**:
在 macOS 上，Python 的多进程默认使用 `spawn` 模式，要求所有传递给子进程的对象都必须是可序列化的（picklable）。之前的代码直接将 `WorkspaceService` 对象传递给 notebook worker 进程，但该对象包含不可序列化的内容（如文件句柄、锁等），导致 worker 进程无法正确启动。

**修复方案**:
修改了 `dsat/services/sandbox.py` 中的进程间通信方式：
1. `notebook_worker` 函数现在接收 `run_dir` 路径字符串而不是 `WorkspaceService` 对象
2. Worker 进程在启动时根据路径重建 `WorkspaceService` 实例
3. `ProcessIsolatedNotebookExecutor` 传递可序列化的字符串路径而不是对象

**修复的文件**:
- `dsat/services/sandbox.py`:
  - 修改 `notebook_worker` 函数签名，接收 `run_dir` 字符串
  - 在 worker 进程内重建 `WorkspaceService` 实例
  - 更新 `ProcessIsolatedNotebookExecutor.__init__`，传递路径字符串

---

## ✅ 修复验证

### 环境信息
- **操作系统**: macOS (使用 'spawn' 多进程模式)
- **Python**: 3.10+
- **Workflow**: data_interpreter

### 测试代码
```python
from dotenv import load_dotenv
load_dotenv()

import dslighting

data = dslighting.load_data("bike-sharing-demand")

agent = dslighting.Agent(
    workflow="data_interpreter",
    model="gpt-4o-mini",
    max_iterations=5,
)

result = agent.run(data, description="分析销售趋势")
print(f"Success: {result.success}")
print(f"Output: {result.output}")
```

### 预期结果
- ✅ Worker 进程正常启动
- ✅ Notebook kernel 正常初始化
- ✅ 代码执行成功
- ✅ 不会出现 "Worker process is not running" 错误

---

## 📦 安装

```bash
pip install --upgrade dslighting==1.9.3
```

---

## 🔧 技术细节

### macOS 多进程问题详解

在 macOS 上，Python 的多进程模块使用 `spawn` 模式而不是 `fork` 模式：
- **fork 模式**（Linux默认）：子进程继承父进程的内存空间
- **spawn 模式**（macOS/Windows默认）：子进程是全新的 Python 解释器，所有数据必须序列化传递

### 修复前（有问题的代码）
```python
# 错误：直接传递 WorkspaceService 对象
def notebook_worker(task_queue, result_queue, workspace, timeout):
    executor = NotebookExecutor(workspace, timeout)
    ...

class ProcessIsolatedNotebookExecutor:
    def __init__(self, workspace: WorkspaceService, timeout: int):
        self.worker_process = Process(
            target=notebook_worker,
            args=(self.task_queue, self.result_queue, workspace, timeout),  # ❌ workspace 不可序列化
        )
```

### 修复后（正确的代码）
```python
# 正确：只传递路径字符串
def notebook_worker(task_queue, result_queue, run_dir: str, timeout: int):
    # 在 worker 进程内重建 WorkspaceService
    from pathlib import Path
    run_dir_path = Path(run_dir)
    base_dir = str(run_dir_path.parent)
    run_name = run_dir_path.name
    workspace = WorkspaceService(run_name, base_dir)  # ✅ 在子进程中重建

    executor = NotebookExecutor(workspace, timeout)
    ...

class ProcessIsolatedNotebookExecutor:
    def __init__(self, workspace: WorkspaceService, timeout: int):
        workspace_path = str(workspace.run_dir)  # ✅ 只传递可序列化的路径字符串
        self.worker_process = Process(
            target=notebook_worker,
            args=(self.task_queue, self.result_queue, workspace_path, timeout),
        )
```

---

## 🎯 影响范围

### 受影响的 Workflow
- ✅ **data_interpreter** - 修复完成
- ✅ **其他 workflows** - 无影响（不使用 notebook executor）

### 受影响的平台
- ✅ **macOS** - 修复完成
- ✅ **Linux** - 无影响（已正常工作）
- ✅ **Windows** - 无影响（已正常工作）

---

## 📖 完整文档

- **PyPI**: https://pypi.org/project/dslighting/1.9.3/
- **GitHub**: https://github.com/usail-hkust/dslighting
- **在线文档**: https://luckyfan-cs.github.io/dslighting-web/

---

## 🎉 总结

DSLighting v1.9.3 是一个 **Bug 修复版本**，修复了 DataInterpreter workflow 在 macOS 上无法运行的关键问题。

### 核心修复
- ✅ 修复 macOS 上 notebook worker 进程启动失败问题
- ✅ 确保进程间通信的对象都是可序列化的
- ✅ 在 worker 进程内重建必要的对象

### 推荐行动
- **macOS 用户**: 强烈建议升级到 v1.9.3
- **data_interpreter workflow 用户**: 必须升级到此版本
- **其他用户**: 可选升级（不影响其他 workflows）

---

**版本**: DSLighting v1.9.3
**发布日期**: 2026-01-17
**向后兼容**: ✅ 是（100% 兼容 v1.9.2）
**类型**: Bug 修复（macOS 多进程兼容性）
