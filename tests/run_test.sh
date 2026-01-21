#!/bin/bash
# DSLighting 快速测试脚本

set -e

echo "================================================================================"
echo "DSLighting 快速测试"
echo "================================================================================"
echo ""

# 检查虚拟环境
if [ ! -d "dslighting-env-v2" ]; then
    echo "❌ 未找到虚拟环境 dslighting-env-v2"
    echo ""
    echo "请先创建虚拟环境："
    echo "  python3.10 -m venv dslighting-env-v2"
    echo "  source dslighting-env-v2/bin/activate"
    echo "  pip install dslighting"
    echo ""
    exit 1
fi

# 激活虚拟环境
echo "✓ 激活虚拟环境: dslighting-env-v2"
source dslighting-env-v2/bin/activate

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  未找到 .env 文件"
    echo ""
    echo "是否创建 .env 文件？(y/N)"
    read -r response
    if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
        cp .env.example .env
        echo "✓ 已创建 .env 文件"
        echo ""
        echo "请编辑 .env 文件，填入你的 API keys："
        echo "  nano .env  # 或使用其他编辑器"
        echo ""
        echo "配置完成后重新运行此脚本"
        exit 0
    else
        echo "跳过创建 .env 文件"
    fi
fi

echo ""
echo "================================================================================"
echo "选择测试模式"
echo "================================================================================"
echo ""
echo "1) 测试单个 workflow (AIDE)"
echo "2) 测试单个 workflow (自定义)"
echo "3) 批量测试所有 workflows"
echo "4) 退出"
echo ""
read -p "请选择 (1-4): " choice

case $choice in
    1)
        echo ""
        echo "运行单个 workflow 测试 (AIDE)..."
        echo "================================================================================"
        echo ""
        python test_single_workflow.py
        ;;
    2)
        echo ""
        echo "自定义 workflow 测试"
        echo "================================================================================"
        echo ""
        echo "可用的 workflows:"
        echo "  - aide"
        echo "  - autokaggle"
        echo "  - data_interpreter"
        echo "  - automind"
        echo "  - dsagent"
        echo "  - deepanalyze"
        echo ""
        read -p "请输入 workflow 名称: " workflow_name

        # 创建临时测试脚本
        cat > test_custom_workflow.py << EOF
import os
import sys
from dotenv import load_dotenv
load_dotenv()

import dslighting
from pathlib import Path
from datetime import datetime
import time

WORKFLOW_NAME = "$workflow_name"
MODEL = "openai/deepseek-ai/DeepSeek-V3.1-Terminus"
TEMPERATURE = 0.7
MAX_ITERATIONS = 1

print(f"测试 {WORKFLOW_NAME}...")

try:
    info = dslighting.datasets.load_bike_sharing_demand()
    data = dslighting.load_data(info['data_dir'])

    agent = dslighting.Agent(
        workflow=WORKFLOW_NAME,
        model=MODEL,
        temperature=TEMPERATURE,
        max_iterations=MAX_ITERATIONS,
        keep_workspace=True
    )

    start_time = time.time()
    result = agent.run(data)
    duration = time.time() - start_time

    print()
    print("=" * 80)
    print("执行结果")
    print("=" * 80)
    print(f"Success: {result.success}")
    print(f"Score: {result.score}")
    print(f"Cost: \${result.cost:.4f}")
    print(f"Duration: {duration:.1f}s")

    if result.score is not None:
        print(f"\\n✅ 成功！获得分数: {result.score}")
        sys.exit(0)
    else:
        print(f"\\n⚠️  警告: 未获得分数")
        sys.exit(1)

except Exception as e:
    print(f"\\n✗ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(2)
EOF

        echo "运行测试: $workflow_name"
        echo "================================================================================"
        echo ""
        python test_custom_workflow.py
        rm -f test_custom_workflow.py
        ;;
    3)
        echo ""
        echo "运行批量测试..."
        echo "================================================================================"
        echo ""
        python test_all_workflows_batch.py
        ;;
    4)
        echo "退出"
        exit 0
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac

echo ""
echo "================================================================================"
echo "测试完成"
echo "================================================================================"
