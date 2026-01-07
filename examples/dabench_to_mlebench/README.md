# DABench 到 MLE-Bench 批量转换工具

## 📋 功能

这个工具可以批量将 DABench 数据分析任务转换为 MLE-Bench 格式的比赛。

## 🚀 快速使用

### 基本命令

```bash
# 列出所有可用任务
python convert_dabench_to_mlebench.py --list

# 转换单个任务
python convert_dabench_to_mlebench.py --task-ids 0

# 转换多个任务
python convert_dabench_to_mlebench.py --task-ids 0 5 6 9 10

# 转换并自动准备数据 ⭐ 推荐
python convert_dabench_to_mlebench.py --task-ids 0 --auto-prepare

# 批量转换所有任务
python convert_dabench_to_mlebench.py --all --auto-prepare
```

## ⚡ 新功能：自动准备数据

**问题**：之前转换后需要手动进入每个目录运行 `prepare.py`

**解决**：使用 `--auto-prepare` 参数，转换后自动准备数据！

```bash
# 不使用 auto-prepare（旧方式）
python convert_dabench_to_mlebench.py --task-ids 0
cd /path/to/mlebench-data/dabench-0-mean-fare
python prepare.py  # 需要手动运行

# 使用 auto-prepare（新方式）✨
python convert_dabench_to_mlebench.py --task-ids 0 --auto-prepare
# 自动完成！数据已准备好，可以直接运行比赛
```

### auto-prepare 功能特点

- ✅ 自动运行 prepare.py
- ✅ 验证数据文件是否成功创建
- ✅ 显示详细的准备进度
- ✅ 60 秒超时保护
- ✅ 完善的错误处理

## 📊 使用场景

### 场景 1: 转换单个任务进行测试

```bash
python convert_dabench_to_mlebench.py --task-ids 0 --auto-prepare
```

**输出**：
```
Converting 1 task(s)...
⚡ Auto-prepare mode enabled - data will be prepared automatically

============================================================
Converting Task 0 -> dabench-0-mean-fare
============================================================
Answer: @mean_fare[34.65]
✓ Created competition directory: ...
✓ Created all competition files
✓ Copied data file: ...
✓ Created dataset prepare script

📦 Auto-preparing data for dabench-0-mean-fare...
✅ Data prepared successfully!
✓ Verified: All data files created
✅ Task 0 converted successfully!
```

### 场景 2: 批量转换 Easy 任务

```bash
python convert_dabench_to_mlebench.py \
  --task-ids 0 9 10 18 19 24 25 26 32 33 \
  --auto-prepare
```

### 场景 3: 转换所有任务（约 200+）

```bash
# 建议先 dry-run 查看
python convert_dabench_to_mlebench.py --all --dry-run

# 确认后执行（会花费约 10-15 分钟）
python convert_dabench_to_mlebench.py --all --auto-prepare
```

## 🎯 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--task-ids` | 指定要转换的任务 ID | `--task-ids 0 5 6` |
| `--all` | 转换所有任务 | `--all` |
| `--auto-prepare` | 自动准备数据 ⭐ | `--auto-prepare` |
| `--dry-run` | 预览转换（不创建文件） | `--dry-run` |
| `--list` | 列出所有可用任务 | `--list` |

## 📁 生成的文件结构

每个任务会生成两个目录：

### 1. 比赛注册目录
```
/path/to/data_science_agent_toolkit/mlebench/competitions/
└── dabench-<id>-<keywords>/
    ├── config.yaml         # 比赛配置
    ├── description.md      # 任务描述
    ├── grade.py            # 评分函数
    ├── prepare.py          # 数据准备函数
    ├── leaderboard.csv     # 排行榜
    └── checksums.yaml      # 数据校验
```

### 2. 数据集目录
```
/path/to/mlebench-data/
└── dabench-<id>-<keywords>/
    ├── prepare.py          # 便捷准备脚本
    ├── raw/
    │   └── <data_file>.csv # 原始数据
    └── prepared/           # 👈 auto-prepare 自动生成
        ├── public/
        │   ├── train.csv
        │   └── sample_submission.csv
        └── private/
            └── answer.csv
```

## 🔍 验证转换结果

```bash
# 检查比赛定义
ls /path/to/data_science_agent_toolkit/mlebench/competitions/dabench-0-mean-fare/

# 检查数据（如果使用了 --auto-prepare）
ls /path/to/mlebench-data/dabench-0-mean-fare/prepared/public/
ls /path/to/mlebench-data/dabench-0-mean-fare/prepared/private/

# 应该看到：
# public/: train.csv, sample_submission.csv
# private/: answer.csv
```

## 🏃 运行转换后的比赛

```bash
cd /path/to/data_science_agent_toolkit

# 如果使用了 --auto-prepare，可以直接运行
python run_benchmark.py \
  --workflow aide \
  --benchmark mle \
  --mle-data-dir "/path/to/mlebench-data" \
  --llm-model openai/deepseek-ai/DeepSeek-V3.1-Terminus \
  --mle-competitions dabench-0-mean-fare
```

## 🐛 故障排除

### 问题 1: 运行比赛时提示 "Public directory does not exist"

**原因**：没有使用 `--auto-prepare` 或数据准备失败

**解决方案 1**：重新转换并使用 auto-prepare
```bash
python convert_dabench_to_mlebench.py --task-ids 0 --auto-prepare
```

**解决方案 2**：手动准备数据
```bash
cd /path/to/mlebench-data/dabench-0-mean-fare
python prepare.py
```

### 问题 2: auto-prepare 失败

**检查错误信息**：
- 脚本会显示详细的错误信息
- 检查原始数据文件是否存在
- 确保有写入权限

**手动调试**：
```bash
cd /path/to/mlebench-data/dabench-<id>-*
python prepare.py  # 手动运行查看详细错误
```

### 问题 3: 数据文件找不到

**错误**：`⚠ Warning: Data file not found: .../da-dev-tables/xxx.csv`

**解决**：确保 DABench 数据已下载
```bash
cd /path/to/DABench
ls da-dev-tables/  # 应该看到很多 .csv 文件
```

## 📈 批量转换建议

### 小批量测试（推荐先做）

```bash
# 转换 10 个 Easy 任务测试
python convert_dabench_to_mlebench.py \
  --task-ids 0 9 10 18 19 24 25 26 32 33 \
  --auto-prepare
```

### 按难度批量转换

```bash
# Easy 任务（约 100 个）
# 建议分批转换，每批 20 个左右

# Medium 任务（约 70 个）
# 可以一次性转换

# Hard 任务（约 30 个）
# 可以一次性转换
```

### 完整批量转换

```bash
# 转换所有任务（建议在后台运行）
nohup python convert_dabench_to_mlebench.py --all --auto-prepare > conversion.log 2>&1 &

# 查看进度
tail -f conversion.log
```

## 💡 最佳实践

1. **首次使用**：先转换 1-2 个任务测试
2. **使用 auto-prepare**：避免手动准备数据
3. **批量转换**：分批进行，每批 10-20 个任务
4. **验证结果**：转换后检查数据文件是否存在
5. **测试运行**：转换后测试运行比赛

## 📚 相关文档

- **主文档**: `/path/to/data_science_agent_toolkit/mlebench/competitions/README.md`
- **快速开始**: `/path/to/data_science_agent_toolkit/examples/dabench_to_mlebench/DABENCH_QUICK_START.md`
- **总结**: `/path/to/data_science_agent_toolkit/examples/dabench_to_mlebench/DABENCH_CONVERSION_SUMMARY.md`

## 🎉 示例：完整工作流

```bash
# 1. 列出任务
python convert_dabench_to_mlebench.py --list | grep easy | head -10

# 2. 转换任务（自动准备数据）
python convert_dabench_to_mlebench.py --task-ids 0 9 10 --auto-prepare

# 3. 验证结果
ls /path/to/mlebench-data/dabench-0-mean-fare/prepared/public/

# 4. 运行比赛
cd /path/to/data_science_agent_toolkit
python run_benchmark.py \
  --workflow aide \
  --benchmark mle \
  --mle-data-dir "/path/to/mlebench-data" \
  --mle-competitions dabench-0-mean-fare

# 5. 查看结果
cat runs/benchmark_results/aide_on_mle/results.json
```

完成！🚀
