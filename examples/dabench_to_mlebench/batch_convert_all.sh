#!/bin/bash
# 批量转换所有 DABench 任务
# 使用 --auto-prepare 自动准备数据

# 定义颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "========================================"
echo "批量转换所有 DABench 任务"
echo "========================================"
echo ""

# 从 da-dev-questions.jsonl 读取所有任务 ID
DABENCH_DIR="/path/to/DABench"
QUESTIONS_FILE="$DABENCH_DIR/da-dev-questions.jsonl"

if [ ! -f "$QUESTIONS_FILE" ]; then
    echo -e "${RED}错误: 找不到文件 $QUESTIONS_FILE${NC}"
    exit 1
fi

echo "正在读取任务列表..."
ALL_TASK_IDS=$(python3 -c "
import json
with open('$QUESTIONS_FILE', 'r') as f:
    ids = [json.loads(line)['id'] for line in f]
print(' '.join(map(str, ids)))
")

TOTAL_TASKS=$(echo $ALL_TASK_IDS | wc -w)

echo -e "${GREEN}找到 $TOTAL_TASKS 个任务${NC}"
echo ""
echo "任务 ID 范围: $(echo $ALL_TASK_IDS | awk '{print $1}') - $(echo $ALL_TASK_IDS | awk '{print $NF}')"
echo ""

# 显示统计信息
echo "任务难度分布:"
python3 << 'STATS_EOF'
import json
from collections import Counter

with open('/path/to/DABench/da-dev-questions.jsonl', 'r') as f:
    tasks = [json.loads(line) for line in f]

levels = Counter(t['level'] for t in tasks)
print(f"  Easy:   {levels['easy']} 个任务")
print(f"  Medium: {levels['medium']} 个任务")
print(f"  Hard:   {levels['hard']} 个任务")
STATS_EOF

echo ""
echo -e "${YELLOW}注意事项:${NC}"
echo "  1. 将转换所有 $TOTAL_TASKS 个任务"
echo "  2. 使用 --auto-prepare 自动准备数据"
echo "  3. Task 743 可能包含文件路径，转换后需手动验证"
echo "  4. 整个过程可能需要 10-30 分钟"
echo ""

read -p "是否继续？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "已取消"
    exit 1
fi

echo ""
echo "========================================"
echo "开始转换..."
echo "========================================"
echo ""

# 记录开始时间
START_TIME=$(date +%s)

# 执行转换
python convert_dabench_to_mlebench.py \
  --task-ids $ALL_TASK_IDS \
  --auto-prepare

CONVERSION_EXIT_CODE=$?

# 记录结束时间
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo ""
echo "========================================"
if [ $CONVERSION_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}转换完成！${NC}"
else
    echo -e "${RED}转换过程中出现错误 (退出码: $CONVERSION_EXIT_CODE)${NC}"
fi
echo "========================================"
echo ""
echo "耗时: ${MINUTES} 分 ${SECONDS} 秒"
echo ""

# 统计转换结果
echo "统计转换结果..."
echo ""

COMP_DIR="/path/to/data_science_agent_toolkit/mlebench/competitions"
DATA_DIR="/path/to/mlebench-data"

CONVERTED_COMPS=$(ls "$COMP_DIR" 2>/dev/null | grep -c "^dabench-")
PREPARED_DATA=$(find "$DATA_DIR" -type d -name "dabench-*" -exec test -f "{}/prepared/public/train.csv" \; -print 2>/dev/null | wc -l)

echo -e "${GREEN}转换结果:${NC}"
echo "  注册的比赛: $CONVERTED_COMPS 个"
echo "  准备好的数据: $PREPARED_DATA 个"
echo ""

if [ $CONVERTED_COMPS -eq $TOTAL_TASKS ]; then
    echo -e "${GREEN}✓ 所有任务都已转换${NC}"
else
    echo -e "${YELLOW}⚠ 部分任务未转换 ($CONVERTED_COMPS/$TOTAL_TASKS)${NC}"
fi

if [ $PREPARED_DATA -eq $TOTAL_TASKS ]; then
    echo -e "${GREEN}✓ 所有数据都已准备${NC}"
else
    echo -e "${YELLOW}⚠ 部分数据未准备 ($PREPARED_DATA/$TOTAL_TASKS)${NC}"
fi

echo ""
echo "查看转换结果："
echo "  ls $COMP_DIR | grep dabench | head -10"
echo ""
echo "查看数据："
echo "  ls $DATA_DIR | grep dabench | head -10"
echo ""
echo "运行所有任务："
echo "  cd /path/to/data_science_agent_toolkit/examples/dabench_to_mlebench"
echo "  ./run_easy_dabench_aide.sh"
echo ""
