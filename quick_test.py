#!/usr/bin/env python3
"""
DSLighting 快速测试脚本 - dsagent workflow
"""
import sys
sys.path.insert(0, '/Users/liufan/Applications/Github/dslighting')

print("=" * 60)
print("DSLighting 快速测试 - dsagent workflow")
print("=" * 60)
print()

try:
    import dslighting
    print(f"✓ DSLighting v{dslighting.__version__} 导入成功")
except Exception as e:
    print(f"✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("测试参数:")
print("  Workflow: dsagent")
print("  Dataset: bike-sharing-demand")
print("  Model: gpt-4o-mini")
print()

try:
    # 创建 dsagent
    print("1. 创建 Agent...")
    agent = dslighting.Agent(
        workflow="dsagent",
        model="gpt-4o-mini",
        temperature=0.7,
        max_iterations=3  # 测试用，减少迭代次数
    )
    print("   ✓ Agent 创建成功")

    # 加载数据
    print()
    print("2. 加载数据...")
    data = dslighting.load_data("data/competitions/bike-sharing-demand")
    print(f"   ✓ 数据加载成功")
    print(f"   Task Type: {data.task_detection.task_type}")

    # 运行任务
    print()
    print("3. 运行任务（这可能需要几分钟）...")
    result = agent.run(data)

    # 查看结果
    print()
    print("=" * 60)
    print("测试结果")
    print("=" * 60)
    print(f"✓ 成功: {result.success}")
    print(f"✓ 得分: {result.score}")
    print(f"✓ 成本: ${result.cost:.4f}")
    print(f"✓ 耗时: {result.duration:.1f}秒")
    print(f"✓ 工作空间: {result.workspace_path}")

    if result.error:
        print(f"✗ 错误: {result.error}")

    print()
    print("=" * 60)
    print("测试完成！")
    print("=" * 60)

except Exception as e:
    print()
    print(f"✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
