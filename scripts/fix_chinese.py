#!/usr/bin/env python3
"""Replace Chinese with English in base_factory.py"""

import re

file_path = "dslighting/workflows/base_factory.py"

# Read file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Chinese text with English
replacements = [
    ("清理工作空间", "Cleanup workspace"),
    ("工作空间已清理", "Workspace cleaned"),
    ("运行 workflow - 统一的入口（推荐使用）", "Run workflow - unified entry point (recommended)"),
    ("这是同步方法，用户无需关心 async/await", "This is a synchronous method, users don't need to care about async/await"),
    ("支持多种调用方式", "Supports multiple calling modes"),
    ("使用 LoadedData 对象**（最简单）", "Use LoadedData object** (simplest)"),
    ("使用 task_id", "Use task_id"),
    ("使用 task_id + data_dir", "Use task_id + data_dir"),
    ("使用 dataset 字典**（从 datasets.load_xxx() 返回的）", "Use dataset dict** (returned from datasets.load_xxx())"),
    ("可选，可以是", "Optional, can be"),
    ("任务 ID（例如", "Task ID (e.g."),
    ("）:", "):"),
    ("数据目录路径", "Data directory path"),
    ("传递给 create_agent() 的参数", "Parameters passed to create_agent()"),
    ("获取 workflow 名称（用于日志和 workspace 命名）", "Get workflow name (for logging and workspace naming)"),
    ("返回类名的小写形式", "Return lowercase form of class name"),
    ("这是推荐的用法 - 自动从 registry 加载标准 MLE 格式配置", "This is recommended - automatically load standard MLE format config from registry"),
    ("可选的数据目录路径。如果不提供，将从 registry 自动查找", "Optional data directory path. If not provided, will automatically search from registry"),
    ("可选的任务加载器。如果不提供，使用 MLETaskLoader", "Optional task loader. If not provided, use MLETaskLoader"),
    ("使用 Task Loader 加载任务（从 tasks 层）", "Use Task Loader to load task (from tasks layer)"),
    ("对于 MLE 格式，只分析 public 数据（避免泄露 private/test_answer.csv）", "For MLE format, only analyze public data (avoid leaking private/test_answer.csv)"),
    ("使用 public 数据目录（避免泄露答案）", "Using public data directory (avoid leaking answers)"),
    ("加载标准 MLE 格式任务配置（传递 public_dir 而不是 data_dir）", "Load standard MLE format task config (pass public_dir instead of data_dir)"),
    ("验证加载结果", "Validate loading result"),
    ("任务加载完成:", "Task loading completed:"),
    ("自动处理数据链接（基础设施层，用户无需关心）", "Automatically handle data linking (infrastructure layer, users don't need to care)"),
    ("自动链接 public 数据到 sandbox...", "Automatically link public data to sandbox..."),
    ("这可能导致模型无法正确理解文件路径要求！", "This may cause the model to not correctly understand file path requirements!"),
    ("尝试重新生成完整的 I/O instructions...", "Attempting to regenerate complete I/O instructions..."),
    ("尝试重新生成完整的 I/O instructions", "Try to regenerate complete I/O instructions"),
    ("重新生成 I/O instructions 成功！长度:", "Successfully regenerated I/O instructions! Length:"),
    ("重新生成失败:", "Regeneration failed:"),
    ("自动评分（基础设施，用户无需关心）", "Auto-grading (infrastructure, users don't need to care)"),
    ("自动评分中...", "Auto-grading..."),
    ("获取提交文件路径", "Get submission file path"),
    ("提交文件:", "Submission file:"),
    ("通用评分逻辑：尝试多种方式加载 benchmark", "Universal grading logic: try multiple ways to load benchmark"),
    ("尝试使用 task_loader.load_benchmark()...", "Trying to use task_loader.load_benchmark()..."),
    ("通过 task_loader 加载 benchmark", "Loaded benchmark through task_loader"),
    ("task_loader.load_benchmark() 失败:", "task_loader.load_benchmark() failed:"),
    ("使用简化评分:", "Using simplified grading:"),
    ("判断成功与否：提交文件存在且有评分", "Determine success: submission file exists and has score"),
    ("Workflow 完成", "Workflow completed"),
    ("Success:", "Success:"),
    ("Score:", "Score:"),
    ("Cost:", "Cost:"),
    ("Duration:", "Duration:"),
    ("✓ ", ""),
    ("不需要 await", "no need to await"),
    ("对象（从", "object (from"),
    ("返回）", ")"),
    ("如果提供，将从中提取 task_id 和 data_dir", "If provided, will extract task_id and data_dir from it"),
    ("如果不提供且 data 也不提供，需要单独指定 data_dir", "If not provided and data is also not provided, need to specify data_dir separately"),
    ("执行结果", "Execution result"),
    ("方式 1: 使用 LoadedData", "Method 1: Use LoadedData"),
    ("方式 2: Use task_id", "Method 2: Use task_id"),
    ("方式 3: 使用 dataset 字典", "Method 3: Use dataset dict"),
    ("关于数据链接的说明", "About data linking"),
    ("模型将能直接访问数据文件", "Model will be able to directly access data files"),
    ("注意", "Note"),
    ("已自动链接到 sandbox", "automatically linked to sandbox"),
    ("关于 IO instructions", "About IO instructions"),
    ("为模型提供", "Provide model with"),
    ("如果 registry 中有", "If in registry"),
    ("将自动使用", "will automatically use"),
    ("否则基于", "Otherwise based on"),
    ("生成（可能不准确）", "generate (may be inaccurate)"),
]

for chinese, english in replacements:
    content = content.replace(chinese, english)

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Chinese text replaced with English successfully!")
