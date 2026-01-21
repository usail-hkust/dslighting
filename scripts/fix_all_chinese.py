#!/usr/bin/env python3
"""Replace Chinese with English in multiple Python files"""

import os
import re

files_to_fix = [
    "dslighting/workflows/base_factory.py",
    "dslighting/tasks/mle_task_loader.py",
    "dslighting/core/agent.py",
    "dslighting/benchmark/mle_lite.py",
    "dslighting/benchmark/kaggle_evaluator.py",
    "dslighting/benchmark/custom.py",
    "dslighting/benchmark/factory.py",
    "dslighting/benchmark/base.py",
    "dslighting/benchmark/base_benchmarks.py",
]

def process_file(file_path):
    """Process a single file"""
    print(f"\nProcessing {file_path}...")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Replace common Chinese phrases
    replacements = [
        ("清理工作空间", "Cleanup workspace"),
        ("工作空间已清理", "Workspace cleaned"),
        ("运行 workflow", "Run workflow"),
        ("统一入口", "unified entry point"),
        ("推荐使用", "recommended"),
        ("同步方法", "synchronous method"),
        ("支持多种", "Supports multiple"),
        ("调用方式", "calling modes"),
        ("最简单", "simplest"),
        ("数据目录", "data directory"),
        ("返回", "Return"),
        ("加载", "Load"),
        ("执行", "Execute"),
        ("结果", "result"),
        ("失败", "failed"),
        ("成功", "success"),
        ("完成", "completed"),
        ("错误", "Error"),
        ("警告", "Warning"),
        ("注意", "Note"),
        ("例如", "e.g."),
        ("等等", "etc."),
        ("模型", "Model"),
        ("超时", "Timeout"),
        ("保留", "Keep"),
        ("初始化", "Initialize"),
        ("创建", "Create"),
        ("提供", "Provide"),
        ("传递", "Pass"),
        ("处理", "Process"),
        ("生成", "Generate"),
        ("评分", "Grading"),
        ("任务", "Task"),
        ("数据", "Data"),
        ("文件", "File"),
        ("路径", "Path"),
        ("配置", "Config"),
        ("服务", "Service"),
        ("沙箱", "Sandbox"),
        ("基础", "Base"),
        ("工厂", "Factory"),
        ("工作流", "Workflow"),
        ("代理", "Agent"),
        ("操作", "Operator"),
        ("提示", "Prompt"),
        ("响应", "Response"),
        ("请求", "Request"),
        ("输出", "Output"),
        ("输入", "Input"),
        ("参数", "Parameter"),
        ("可选", "Optional"),
        ("必需", "Required"),
        ("如果", "If"),
        ("否则", "Otherwise"),
        ("并且", "and"),
        ("或者", "or"),
        ("但是", "but"),
        ("因为", "because"),
        ("所以", "therefore/so"),
        ("然后", "then"),
        ("之后", "after"),
        ("之前", "before"),
        ("首先", "First"),
        ("其次", "Second"),
        ("最后", "Finally"),
        ("自动", "automatic/automatically"),
        ("手动", "manual"),
        ("标准", "standard"),
        ("格式", "format"),
        ("类型", "type"),
        ("值", "value"),
        ("默认", "default"),
        ("所有", "All"),
        ("每个", "Each"),
        ("其他", "other"),
        ("多个", "multiple"),
        ("单个", "single"),
        ("包含", "contains"),
        ("其中", "among/in"),
        ("关于", "About"),
        ("无需", "no need/don't need"),
        ("需要", "need/require"),
        ("应该", "should"),
        ("能够", "can"),
        ("必须", "must"),
        ("验证", "Verify"),
        ("检查", "Check"),
        ("测试", "Test"),
        ("分析", "Analyze"),
        ("评估", "Evaluate"),
        ("优化", "Optimize"),
        ("改进", "Improve"),
        ("修复", "Fix"),
        ("更新", "Update"),
        ("删除", "Delete"),
        ("添加", "Add"),
        ("设置", "Set"),
        ("获取", "Get"),
        ("方法", "method"),
        ("函数", "function"),
        ("类", "class"),
        ("对象", "object"),
        ("实例", "instance"),
        ("属性", "attribute/property"),
        ("字段", "field"),
        ("变量", "variable"),
        ("常量", "constant"),
        ("接口", "interface"),
        ("实现", "implement/implementation"),
        ("定义", "define"),
        ("描述", "description"),
        ("说明", "instruction/explanation"),
        ("示例", "example"),
        ("文档", "documentation"),
        ("注释", "comment"),
        ("代码", "code"),
        ("用户", "user"),
        ("客户端", "client"),
        ("服务端", "server"),
        ("系统", "system"),
        ("环境", "environment"),
        ("版本", "version"),
        ("依赖", "dependency"),
        ("包", "package"),
        ("模块", "module"),
        ("库", "library"),
        ("工具", "tool"),
        ("框架", "framework"),
        ("平台", "platform"),
        ("项目", "project"),
        ("产品", "product"),
        ("功能", "feature/functionality"),
        ("特性", "feature"),
        ("组件", "component"),
        ("元素", "element"),
        ("节点", "node"),
        ("边", "edge"),
        ("图", "graph"),
        ("树", "tree"),
        ("列表", "list"),
        ("字典", "dict/dictionary"),
        ("集合", "set/collection"),
        ("数组", "array"),
        ("字符串", "string"),
        ("数字", "number"),
        ("布尔", "boolean"),
        ("空", "empty/null"),
        ("无效", "invalid"),
        ("有效", "valid"),
        ("正确", "correct"),
        ("错误", "wrong/error"),
        ("异常", "exception"),
        ("问题", "problem/issue"),
        ("解决", "solve/solution"),
        ("答案", "answer"),
        ("结果", "result"),
        ("响应", "response"),
    ]

    # Apply replacements
    for chinese, english in replacements:
        content = content.replace(chinese, english)

    # Convert non-critical log levels
    lines = content.split('\n')
    new_lines = []

    for line in lines:
        # Skip if line starts with import or contains only ASCII
        if re.match(r'^\s*(import|from|#.*coding)', line):
            new_lines.append(line)
            continue

        # Check if it's a log line
        if 'logger.' in line:
            # Non-critical logs -> debug
            if any(keyword in line for keyword in [
                'Workspace cleaned', 'initialized', 'linked',
                'loading completed', 'Using public',
                'Loaded benchmark', 'Configuration',
                'Parameter', 'Setting'
            ]):
                line = re.sub(r'logger\.(info|warning|error)', 'logger.debug', line)
            # Errors and critical warnings remain as is
            elif any(keyword in line for keyword in [
                'Error', 'Exception', 'Failed', 'Cannot'
            ]):
                pass  # Keep as is
            else:
                # Info stays as info, warning can be debug
                if 'logger.warning' in line and 'may cause' in line.lower():
                    line = line.replace('logger.warning', 'logger.debug')

        new_lines.append(line)

    content = '\n'.join(new_lines)

    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Updated {file_path}")
        return True
    else:
        print(f"  No changes needed for {file_path}")
        return False

# Process all files
print("="*80)
print("Replacing Chinese with English in dslighting package")
print("="*80)

updated_count = 0
for file_path in files_to_fix:
    if os.path.exists(file_path):
        if process_file(file_path):
            updated_count += 1
    else:
        print(f"\nWARNING: File not found: {file_path}")

print("\n" + "="*80)
print(f"Completed! Updated {updated_count} files")
print("="*80)
