#!/bin/bash
#
# 一键运行自定义 Benchmark 示例
#
# 此脚本自动完成：
# 1. 生成原始数据
# 2. 准备训练/测试数据集
# 3. 运行 Benchmark 测试
#

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   自定义 Benchmark 示例 - 房价预测                      ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 错误: 未找到 python3${NC}"
    exit 1
fi

# 获取脚本目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}步骤 1/3: 生成原始数据${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 prepare_example_data.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 数据生成失败${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}步骤 2/3: 准备数据集（训练/测试分离）${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd competitions/custom-house-price-prediction
python3 prepare.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 数据准备失败${NC}"
    exit 1
fi
cd "$SCRIPT_DIR"
echo ""

echo -e "${YELLOW}步骤 3/3: 运行 Benchmark 测试${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 custom_benchmark.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Benchmark 运行失败${NC}"
    exit 1
fi
echo ""

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   ✅ 完成！                                              ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}结果已保存到:${NC} test_results/"
echo ""
echo "下一步:"
echo "  • 查看提交文件: ls -lh test_results/"
echo "  • 阅读文档: cat README.md"
echo "  • 集成到框架: 参考 README.md 的'集成到框架'部分"
echo ""
