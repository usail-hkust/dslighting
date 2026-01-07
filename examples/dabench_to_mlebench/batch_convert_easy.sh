#!/bin/bash
# 批量转换 DABench Easy 任务
# 使用 --auto-prepare 自动准备数据

echo "========================================"
echo "批量转换 DABench Easy 任务"
echo "========================================"
echo ""

# Easy 任务 ID 列表（部分）
EASY_TASKS="0 9 10 18 19 24 25 26 32 33 55 56 57 58 59"

echo "将转换以下任务："
echo "$EASY_TASKS"
echo ""

read -p "是否继续？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "已取消"
    exit 1
fi

echo ""
echo "开始转换..."
echo ""

python convert_dabench_to_mlebench.py \
  --task-ids $EASY_TASKS \
  --auto-prepare

echo ""
echo "========================================"
echo "转换完成！"
echo "========================================"
echo ""
echo "查看转换结果："
echo "ls /path/to/data_science_agent_toolkit/mlebench/competitions/ | grep dabench"
echo ""
echo "查看数据："
echo "ls /path/to/mlebench-data/ | grep dabench"
