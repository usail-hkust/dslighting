"""
DSLighting 2.4.0 - 新 API 使用示例

展示如何使用新的统一 Dataset API，包括 Agent 视角的获取。
"""

import dslighting

print("\n" + "=" * 80)
print("DSLighting 2.4.0 - 新 API 使用示例")
print("=" * 80 + "\n")

# ============================================================================
# 1. 基本加载
# ============================================================================
print("【1. 基本加载】")
print("-" * 80)

dataset = dslighting.load_dataset("bike-sharing-demand")
print(f"✓ 数据集加载成功: {dataset}")
print(f"✓ 任务 ID: {dataset.info.task_id}")
print(f"✓ 任务类型: {dataset.info.task_type}")
print()

# ============================================================================
# 2. 快速预览（用户视角）
# ============================================================================
print("【2. 快速预览（用户视角）】")
print("-" * 80)

print(dataset.show())
print()

# ============================================================================
# 3. Agent 视角（完整数据报告）
# ============================================================================
print("【3. Agent 视角（完整数据报告）】")
print("-" * 80)

agent_report = dataset.get_agent_report()
print(agent_report)
print()

# ============================================================================
# 4. 与 Agent 一起使用
# ============================================================================
print("【4. 与 Agent 一起使用】")
print("-" * 80)

agent = dslighting.Agent(
    workflow="aide",
    model="openai/deepseek-ai/DeepSeek-V3.1-Terminus"
)

# Agent 会自动使用 DataAnalyzer 生成报告
# result = agent.run(data=dataset, max_iterations=1)
print("✓ Agent 会自动获取数据报告")
print("✓ Agent 会自己加载数据")
print()

# ============================================================================
# 5. 用户调试（可选）
# ============================================================================
print("【5. 用户调试（可选）】")
print("-" * 80)

print("如果用户想查看数据：")
dataset.load()
print(f"✓ Train shape: {dataset.train.shape}")
print(f"✓ Test shape: {dataset.test.shape}")
print(f"✓ Sample submission shape: {dataset.sample_submission.shape}")
print()

print("✓ 注意：这只是给用户调试用的，Agent 会自己加载数据")
print()

# ============================================================================
# 总结
# ============================================================================
print("=" * 80)
print("✅ 新 API 优势总结：")
print("=" * 80)
print("1. ✓ 统一：一个类 Dataset，符合 HuggingFace 风格")
print("2. ✓ 简单：load_dataset() 一行搞定")
print("3. ✓ Agent 视角：get_agent_report() 返回完整数据报告")
print("4. ✓ 复用：使用现有的 DataAnalyzer 服务")
print("5. ✓ 不预加载：Agent 会自己处理数据加载")
print("=" * 80)
