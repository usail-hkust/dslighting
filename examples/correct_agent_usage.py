"""
DSLighting - 正确的 Agent 使用示例

解决 Score: N/A 的问题
"""

import dslighting

print("\n" + "=" * 80)
print("DSLighting - 正确的 Agent 使用示例")
print("=" * 80 + "\n")

# ============================================================================
# ❌ 错误示例 1：迭代次数太少
# ============================================================================
print("【❌ 错误示例 1】max_iterations=1（太少了）")
print("-" * 80)

agent_wrong = dslighting.Agent(
    workflow="aide",
    model="openai/deepseek-ai/DeepSeek-V3.1-Terminus",
    max_iterations=1  # ❌ 只有 1 次机会
)

print("问题：")
print("  - 第 1 次迭代：生成代码")
print("  - 检测结果：Buggy: True")
print("  - 达到最大迭代次数，结束")
print("  - 没有机会修复 bug")
print("  - 结果：Score: N/A")
print()

# ============================================================================
# ❌ 错误示例 2：MLE-Bench 未安装
# ============================================================================
print("【❌ 错误示例 2】MLE-Bench 未安装")
print("-" * 80)

print("问题：")
print("  - 日志：MLE-Bench import failed: No module named 'mlebench'")
print("  - 结果：评分被跳过")
print("  - 即使代码正确，也无法评分")
print()

# ============================================================================
# ✅ 正确示例 1：增加迭代次数（推荐）
# ============================================================================
print("【✅ 正确示例 1】增加迭代次数")
print("-" * 80)

agent_correct_1 = dslighting.Agent(
    workflow="aide",
    model="openai/deepseek-ai/DeepSeek-V3.1-Terminus",
    max_iterations=5,  # ✅ 给 Agent 5 次机会
)

print("优势：")
print("  - Agent 有多次机会生成和修复代码")
print("  - 第 1 次失败 → 第 2 次修复 → 第 3 次优化...")
print("  - 提高成功率")
print()

# 实际运行（如果需要）
# result = agent_correct_1.run(task_id="bike-sharing-demand")
# print(f"Success: {result.success}")
# print(f"Score: {result.score or 'N/A (可能需要 MLE-Bench)'}")

# ============================================================================
# ✅ 正确示例 2：禁用评分（快速测试）
# ============================================================================
print("【✅ 正确示例 2】禁用评分（快速测试）")
print("-" * 80)

agent_correct_2 = dslighting.Agent(
    workflow="aide",
    model="openai/deepseek-ai/DeepSeek-V3.1-Terminus",
    max_iterations=5,
)

print("方法：")
print("  result = agent.run(task_id='bike-sharing-demand')")
print("  ")
print("  # 查看结果")
print("  print(f'Success: {result.success}')")
print("  print(f'Cost: ${result.cost:.4f}')")
print("  print(f'Workspace: {result.workspace_path}')")
print("  ")
print("  # 查看提交文件")
print("  import os")
print("  workspace = result.workspace_path")
print("  if workspace:")
print("      submissions = list(workspace.glob('submission_*.csv'))")
print("      print(f'提交文件: {submissions}')")
print()

print("优势：")
print("  - 不依赖 MLE-Bench")
print("  - 快速测试 Agent 能力")
print("  - 生成提交文件供后续使用")
print()

# ============================================================================
# ✅ 正确示例 3：安装 MLE-Bench（正式评估）
# ============================================================================
print("【✅ 正确示例 3】安装 MLE-Bench（正式评估）")
print("-" * 80)

print("步骤：")
print("  1. 安装 MLE-Bench")
print("     cd /Users/liufan/projects/share/dslighting")
print("     pip install -e benchmarks/mlebench")
print()
print("  2. 运行评估")
print("     agent = dslighting.Agent(")
print("         workflow='aide',")
print("         max_iterations=5")
print("     )")
print("     result = agent.run(task_id='bike-sharing-demand')")
print()
print("  3. 获得分数")
print("     print(f'Score: {result.score}')")
print()

# ============================================================================
# 概念澄清
# ============================================================================
print("=" * 80)
print("📊 概念澄清")
print("=" * 80)
print()
print("【Benchmark（基准测试平台）】")
print("  - 定义：提供标准化数据和评分的平台")
print("  - 示例：MLE-Bench, Kaggle, OpenML")
print("  - 作用：提供评分函数、排行榜")
print("  - 必要性：可选安装")
print()
print("【Task（任务类型）】")
print("  - 定义：数据科学任务的类型")
print("  - 示例：kaggle, openqa, vision, nlp")
print("  - 作用：决定 Agent 的处理方式")
print("  - 必要性：内置支持")
print()
print("【关系】")
print("  bike-sharing-demand:")
print("    - Benchmark: Kaggle 竞赛")
print("    - Task Type: kaggle")
print("    - 需要 MLE-Bench: 是（用于评分）")
print()

# ============================================================================
# 推荐配置
# ============================================================================
print("=" * 80)
print("✅ 推荐配置")
print("=" * 80)
print()
print("# 快速测试（不需要评分）")
print("agent = dslighting.Agent(")
print("    workflow='aide',")
print("    max_iterations=5,  # ✅ 关键：给足够的机会")
print(")")
print("result = agent.run(task_id='bike-sharing-demand')")
print()
print("# 正式评估（需要评分）")
print("# 1. 安装 MLE-Bench")
print("# pip install -e benchmarks/mlebench")
print()
print("# 2. 运行评估")
print("result = agent.run(task_id='bike-sharing-demand')")
print("print(f'Score: {result.score}')")
print()
print("=" * 80)
