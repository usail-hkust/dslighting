# DABench Remote Tuning Scripts

这些脚本用于在远端 `user 2` 上跑：

- `experiments/benchmark/run_dabench_benchmark_react.py`
- `experiments/benchmark/run_dacode_benchmark_react.py`
- `experiments/benchmark/run_moscibench_benchmark_react.py`
- `experiments/benchmark/run_scienceagentbench_benchmark_react.py`

它们的作用是：

- 不改 Python 入口脚本
- 只通过环境变量覆盖 scheduler 参数
- 方便对 DABench 做并发与速率限制调参

## 运行方式

远端登录后，在仓库根目录执行：

```bash
cd ~/projects/dslighting
bash experiments/benchmark/scripts/profiles/run_remote_user2_dabench_profile_03_current_baseline.sh
```

单个 profile 脚本默认：

- 后台启动
- 自动创建独立 log 目录
- 输出：
  - `pid=...`
  - `log=...`

如果要按顺序串行扫完全部 profile：

```bash
cd ~/projects/dslighting
bash experiments/benchmark/scripts/run_remote_user2_dabench_profile_sweep_serial.sh
```

这条 sweep 脚本会：

- 严格串行
- 一组跑完再跑下一组
- 不会同时启动多个 profile

## 其他 Benchmark 的 `p03_current_baseline`

如果你要用和 `p03_current_baseline` 一样的 scheduler 参数去跑其他 benchmark，现在已经有这 3 条脚本：

```bash
cd ~/projects/dslighting
bash experiments/benchmark/scripts/profiles/run_remote_user2_dacode_profile_03_current_baseline.sh
bash experiments/benchmark/scripts/profiles/run_remote_user2_moscibench_profile_03_current_baseline.sh
bash experiments/benchmark/scripts/profiles/run_remote_user2_scienceagentbench_profile_03_current_baseline.sh
```

它们统一使用：

- `scheduler_policy = "balanced"`
- `max_concurrency = 8`
- `llm_max_concurrency = 20`
- `enable_task_rate_limiting = true`
- `llm_task_start_rate = 10.0`
- `sandbox_task_start_rate = 20.0`
- `task_rate_burst_factor = 2.0`

也就是和 `p03_current_baseline` 完全一致，只是 benchmark 入口不同。

## 参数表

| Profile | `scheduler_policy` | `max_concurrency` | `llm_max_concurrency` | `enable_task_rate_limiting` | `llm_task_start_rate` | `sandbox_task_start_rate` | `task_rate_burst_factor` | 变化点 |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | --- |
| `p01_safe_low` | `balanced` | `4` | `8` | `True` | `4.0` | `8.0` | `1.5` | 最保守，整体并发与启动速率都压低 |
| `p02_safe_mid` | `balanced` | `6` | `12` | `True` | `6.0` | `12.0` | `1.5` | 中低并发，观察稳定性/吞吐折中 |
| `p03_current_baseline` | `balanced` | `8` | `20` | `True` | `10.0` | `20.0` | `2.0` | 当前主配置基线 |
| `p04_llm_tight` | `balanced` | `8` | `12` | `True` | `8.0` | `16.0` | `1.5` | Task 并发不变，收紧 LLM 压力 |
| `p05_rate_tight` | `balanced` | `8` | `20` | `True` | `6.0` | `12.0` | `1.2` | 并发上限不变，收紧启动节奏 |
| `p06_aggressive` | `balanced` | `10` | `24` | `True` | `12.0` | `24.0` | `2.0` | 比基线更激进的并发 |
| `p07_task20_llm20` | `balanced` | `20` | `20` | `True` | `10.0` | `20.0` | `2.0` | 只把 task 并发拉高，LLM 上限保持 20 |
| `p08_task20_llm40` | `balanced` | `20` | `40` | `True` | `20.0` | `40.0` | `2.0` | `20` 个 task，同时放开 LLM 并发 |
| `p09_task40_llm40` | `balanced` | `40` | `40` | `True` | `20.0` | `40.0` | `2.0` | 高压并发组，观察上限和失稳点 |

## 结果怎么读

建议统一看这些指标：

- `actual_accuracy`
- `failed_submission_count`
- `avg_total_tokens`
- `wall_clock_elapsed`

可以重点看：

- `p01/p02` 是否比 `p03` 更稳
- `p04` 是否优于 `p03`
- `p05` 是否优于 `p03`
- `p07/p08/p09` 在更高并发下是否出现明显掉分或 missing submission 增长

## 已有结果

说明：

- `actual_accuracy` 统一按 `sum(score) / 257` 计算
- 时间统一使用 **wall clock elapsed**
- `avg_total_tokens` 使用结果表里的 per-task `total_tokens` 平均值

| Run | 参数组 | `actual_accuracy` | `failed_submission_count` | `avg_total_tokens` | `wall_clock_elapsed_seconds` | 备注 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `manual_baseline_20260407_172934` | `p03_current_baseline` | `0.8366` | `7` | `16849.13` | `3097.23` | 已完成，user 2 手动并行 baseline |
| `profile_03_current_baseline` | `p03_current_baseline` | `0.8366` | `4` | `16108.16` | `2592.28` | 已完成，sweep 中的 baseline |
| `profile_04_llm_tight` | `p04_llm_tight` | `0.8521` | `3` | `17461.25` | `3048.41` | 已完成 |
| `profile_05_rate_tight` | `p05_rate_tight` | `0.8093` | `8` | `17166.06` | `3343.87` | 已完成 |
| `profile_06_aggressive` | `p06_aggressive` | `0.8327` | `6` | `17948.06` | `2583.19` | 已完成 |
| `profile_09_task40_llm40` | `p09_task40_llm40` | `0.8288` | `14` | `16249.25` | `660.58` | 已完成 |
| `profile_08_task20_llm40` | `p08_task20_llm40` | `0.8482` | `6` | `16763.80` | `1321.16` | 已完成 |
| `profile_07_task20_llm20` | `p07_task20_llm20` | `0.8405` | `3` | `16873.58` | `1399.26` | 已完成 |
| `profile_02_safe_mid` | `p02_safe_mid` | `0.8249` | `6` | `16149.50` | `3501.82` | 已完成 |
| `profile_01_safe_low` | `p01_safe_low` | `0.8288` | `4` | `17715.43` | `5419.67` | 已完成 |

## Selected Repeats

为了给 `p03 / p04 / p07 / p08` 做重复实验，远端又额外跑了一轮：

- run root:
  - `experiments/benchmark/runs/dabench_selected_repeats_20260408_102242`
- 当前状态：
  - **已全部完成**
- 覆盖的 4 组：
  - `p03_current_baseline`
  - `p04_llm_tight`
  - `p07_task20_llm20`
  - `p08_task20_llm40`

当前已确认的远端产物：

- `dabench_react_p03_current_baseline_20260408_102242/dabench_metadata_20260408_102258.json`
- `dabench_react_p04_llm_tight_20260408_111711/dabench_metadata_20260408_111725.json`
- `dabench_react_p07_task20_llm20_20260408_120346/dabench_metadata_20260408_120356.json`
- `dabench_react_p08_task20_llm40_20260408_122343/dabench_metadata_20260408_122352.json`

第二轮结果：

| Repeat Run | 参数组 | `actual_accuracy` | `failed_submission_count` | `avg_total_tokens` | `wall_clock_elapsed_seconds` |
| --- | --- | ---: | ---: | ---: | ---: |
| `repeat_20260408_102242` | `p03_current_baseline` | `0.8521` | `4` | `16449.06` | `3251.71` |
| `repeat_20260408_111711` | `p04_llm_tight` | `0.8327` | `7` | `15949.30` | `2779.45` |
| `repeat_20260408_120346` | `p07_task20_llm20` | `0.8132` | `5` | `17093.06` | `1185.08` |
| `repeat_20260408_122343` | `p08_task20_llm40` | `0.8210` | `11` | `17277.16` | `1278.25` |

两轮平均值：

| 参数组 | `actual_accuracy_avg` | `failed_submission_count_avg` | `avg_total_tokens_avg` | `wall_clock_elapsed_seconds_avg` | 备注 |
| --- | ---: | ---: | ---: | ---: | --- |
| `p03_current_baseline` | `0.8444` | `4.0` | `16278.61` | `2922.00` | 两轮都比较稳定 |
| `p04_llm_tight` | `0.8424` | `5.0` | `16705.27` | `2913.93` | 首轮最好，但重复波动明显 |
| `p07_task20_llm20` | `0.8269` | `4.0` | `16983.32` | `1292.17` | 速度快，稳定性中等 |
| `p08_task20_llm40` | `0.8346` | `8.5` | `17020.48` | `1299.71` | 速度快，但 failed submission 偏高 |

## 文件说明

- `profiles/_run_remote_user2_dabench_benchmark_profile.sh`
  - 公共启动器
- `profiles/_run_remote_user2_benchmark_profile.sh`
  - 通用 benchmark profile 启动器
- `profiles/run_remote_user2_dabench_profile_*.sh`
  - 单 profile 远端启动脚本
- `profiles/run_remote_user2_{dacode,moscibench,scienceagentbench}_profile_03_current_baseline.sh`
  - 其他 benchmark 的 `p03_current_baseline` 启动脚本
- `run_remote_user2_dabench_profile_sweep_serial.sh`
  - 串行 sweep 脚本

## MosciBench DSLighting Account 2 参数组

用途：在远端 `account 2` 上重跑 `moscibench + dslighting`，对比不同 scheduler 参数。当前只准备脚本，未启动。

串行总控脚本：

```bash
cd ~/projects/dslighting
bash experiments/benchmark/scripts/run_remote_account2_moscibench_dslighting_profile_sweep_serial.sh
```

建议放入 tmux：

```bash
cd ~/projects/dslighting
tmux new-session -d -s moscibench_dslighting_account2_sweep 'bash experiments/benchmark/scripts/run_remote_account2_moscibench_dslighting_profile_sweep_serial.sh'
```

执行顺序固定为：`m03 -> m04 -> m02 -> m05 -> m06 -> m01 -> m07`。每个 profile 完成后才会进入下一个，不会同时启动多个 profile。

| Profile | 脚本 | `scheduler_policy` | `max_concurrency` | `llm_max_concurrency` | `enable_task_rate_limiting` | `llm_task_start_rate` | `sandbox_task_start_rate` | `task_rate_burst_factor` | 目的 |
| --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | --- |
| `m01_mosci_safe_low` | `profiles/run_remote_account2_moscibench_dslighting_profile_01_safe_low.sh` | `balanced` | `2` | `6` | `true` | `2.0` | `4.0` | `1.0` | 最稳组，验证失败提交是否主要来自并发压力 |
| `m02_mosci_safe_mid` | `profiles/run_remote_account2_moscibench_dslighting_profile_02_safe_mid.sh` | `balanced` | `4` | `8` | `true` | `4.0` | `8.0` | `1.2` | 稳定性优先，但比 `m01` 快 |
| `m03_mosci_p03_repeat` | `profiles/run_remote_account2_moscibench_dslighting_profile_03_p03_repeat.sh` | `balanced` | `8` | `20` | `true` | `10.0` | `20.0` | `2.0` | 复跑原 `p03_current_baseline` 作为对照 |
| `m04_mosci_llm_tight` | `profiles/run_remote_account2_moscibench_dslighting_profile_04_llm_tight.sh` | `balanced` | `8` | `12` | `true` | `6.0` | `12.0` | `1.2` | task 并发不变，压低 LLM 并发和启动速率 |
| `m05_mosci_mid_fast` | `profiles/run_remote_account2_moscibench_dslighting_profile_05_mid_fast.sh` | `balanced` | `12` | `16` | `true` | `8.0` | `16.0` | `1.5` | 中等加速，观察 accuracy 与 wall clock 折中 |
| `m06_mosci_high_task` | `profiles/run_remote_account2_moscibench_dslighting_profile_06_high_task.sh` | `balanced` | `20` | `20` | `true` | `10.0` | `20.0` | `1.5` | 高 task 并发但不放大 LLM 并发 |
| `m07_mosci_high_llm` | `profiles/run_remote_account2_moscibench_dslighting_profile_07_high_llm.sh` | `balanced` | `20` | `40` | `true` | `16.0` | `32.0` | `1.5` | 高压组，最后跑，观察失稳点 |

## 本地 MosciBench DSLighting Workspace Debug

用途：本地复现 `dslighting + moscibench` 的 missing submission / workspace 问题，不改 Python benchmark 入口，只创建一个临时 symlink 数据集。

如果要验证 ReAct observation/output-contract 修复，优先跑这条一键脚本：

```bash
cd /Users/liufan/projects/share/dslighting-migration-clean
bash experiments/benchmark/scripts/run_local_moscibench_react_output_contract_debug.sh
```

这条脚本默认使用：

- 数据：`/Users/liufan/projects/data/moscibench`
- profile：`serial`
- task preset：`extended`
- 任务：`mosci-pop_genetics-3 mosci-nurse_stress-15 mosci-cyclone-14 mosci-pop_genetics-4 mosci-nurse_stress-6 mosci-nurse_stress-12 mosci-pop_genetics-12 mosci-cyclone-10 mosci-terra-2 mosci-terra-9 mosci-health_spa-15 mosci-massspecgym-15`
- 输出目录：`experiments/benchmark/runs/local_moscibench_react_output_contract_debug_<timestamp>/`

可用 preset：

| Preset | 任务数 | 用途 |
| --- | ---: | --- |
| `quick` | `4` | 旧默认小集合，先快速验证链路 |
| `extended` | `12` | 新默认，覆盖 nurse stress、pop genetics、cyclone、terra、health spa、massspecgym |
| `long_io` | `6` | 重点压测长 I/O/data report 的任务 |
| `full` | `88` | 全量本地 MosciBench |

例如只跑旧的 4 个任务：

```bash
cd /Users/liufan/projects/share/dslighting-migration-clean
MOSCI_TASK_PRESET=quick bash experiments/benchmark/scripts/run_local_moscibench_react_output_contract_debug.sh
```

例如重点跑长 I/O 任务：

```bash
cd /Users/liufan/projects/share/dslighting-migration-clean
MOSCI_TASK_PRESET=long_io bash experiments/benchmark/scripts/run_local_moscibench_react_output_contract_debug.sh
```

如果要跑全量本地 MosciBench：

```bash
cd /Users/liufan/projects/share/dslighting-migration-clean
MOSCI_TASK_PRESET=full LOCAL_DEBUG_PROFILE=p03 bash experiments/benchmark/scripts/run_local_moscibench_react_output_contract_debug.sh
```

一键运行：

```bash
cd /Users/liufan/projects/share/dslighting-migration-clean
bash experiments/benchmark/scripts/run_local_moscibench_dslighting_workspace_debug.sh
```

默认配置：

- Python：`experiments/.venv312_framework/bin/python`
- env file：仓库根目录 `.env`
- 数据优先使用：`/Users/liufan/projects/data/moscibench/competitions`
- profile：`serial`
- `MAX_CONCURRENCY=1`
- `LLM_MAX_CONCURRENCY=1`
- `KEEP_WORKSPACE=true`
- `MAX_STEPS=10`
- 默认任务：同一键脚本的 `extended` 集合

默认任务集合包含之前 DSLighting MosciBench 里出现过 missing submission / 长 I/O 风险的任务，也包含多个 family 的对照任务，方便一次性观察是否还存在 workspace 或 submission 输出问题。

如果要复现远端 `p03_current_baseline` 并发参数：

```bash
cd /Users/liufan/projects/share/dslighting-migration-clean
LOCAL_DEBUG_PROFILE=p03 bash experiments/benchmark/scripts/run_local_moscibench_dslighting_workspace_debug.sh
```

如果只跑单个任务：

```bash
cd /Users/liufan/projects/share/dslighting-migration-clean
MOSCI_TASKS="mosci-pop_genetics-3" bash experiments/benchmark/scripts/run_local_moscibench_dslighting_workspace_debug.sh
```

如果要跑全量 88 个任务：

```bash
cd /Users/liufan/projects/share/dslighting-migration-clean
MOSCI_TASKS=all LOCAL_DEBUG_PROFILE=p03 bash experiments/benchmark/scripts/run_local_moscibench_dslighting_workspace_debug.sh
```

输出位置：

- `experiments/benchmark/runs/local_moscibench_dslighting_workspace_debug_<timestamp>/stdout.log`
- `experiments/benchmark/runs/local_moscibench_dslighting_workspace_debug_<timestamp>/moscibench_react/moscibench_results_*.csv`
- `experiments/benchmark/runs/local_moscibench_dslighting_workspace_debug_<timestamp>/moscibench_react/moscibench_metadata_*.json`
- `experiments/benchmark/runs/local_moscibench_dslighting_workspace_debug_<timestamp>/moscibench_react/debug_logs/`

脚本结束后会打印：

- `actual_accuracy`
- `scored_task_count`
- `missing_submission_count`
- 每个 missing submission 的 `competition_id` 和 `submission_path`
- 已存在 submission 的 `competition_id`、`submission_path` 和 `score`

当前目录结构：

- `scripts/`
  - `README.md`
  - `run_local_moscibench_dslighting_workspace_debug.sh`
  - `run_remote_user2_dabench_benchmark_react.sh`
  - `run_remote_user2_dabench_profile_sweep_serial.sh`
  - `run_remote_account2_moscibench_dslighting_profile_sweep_serial.sh`
  - `profiles/`
    - `_run_remote_user2_dabench_benchmark_profile.sh`
    - `run_remote_user2_dabench_profile_*.sh`
    - `run_remote_account2_moscibench_dslighting_profile_*.sh`
