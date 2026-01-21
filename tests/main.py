# """
# My Custom Agent - 主程序

# 像 DSLighting 用户一样使用自定义 Agent。

# 这个文件展示了如何：
# 1. 使用 DSLighting 的 load_data() 加载数据
# 2. 创建自定义 Agent
# 3. 运行完整的工作流
# 4. 获取结果和指标
# """

# import sys
# sys.path.insert(0, '/Users/liufan/Applications/Github/test_pip_dslighting/my_custom_agent')

# import dslighting
# from my_custom_agent import MyCustomAgent

# # ============================================================================
# # 方法 1: 经典 DSLighting 风格
# # ============================================================================

# print("="*70)
# print("方法 1: 经典 DSLighting 风格")
# print("="*70 + "\n")

# # 1. 使用 DSLighting 加载数据
# print("步骤 1: 加载数据")
# print("-"*70)
# data = dslighting.load_data("bike-sharing-demand")

# print(f"\n✓ 数据加载成功!")
# print(f"  任务 ID: {data.task_id}")
# print(f"  数据路径: {data.data_dir}")
# print(f"  数据类型: {data.task_detection.task_type if hasattr(data, 'task_detection') else 'kaggle'}")

# # 2. 创建自定义 Agent（类似 DSLighting 的 Agent）
# print("\n步骤 2: 创建自定义 Agent")
# print("-"*70)
# agent = MyCustomAgent(
#     target_column="count",  # 目标列
#     n_estimators=100,        # 随机森林树数量
#     verbose=True             # 打印详细信息
# )

# print(f"\n✓ Agent 创建成功!")
# print(f"  目标列: {agent.target_column}")
# print(f"  树数量: {agent.n_estimators}")
# print(f"  工具数量: {len(agent.tools)}")

# # 3. 运行 Agent
# print("\n步骤 3: 运行 Agent")
# print("-"*70)
# result = agent.run(str(data.data_dir))

# # 4. 查看结果
# print("\n步骤 4: 查看结果")
# print("-"*70)
# print(f"\n📊 性能指标:")
# print(f"  R² 分数: {result['metrics']['r2']:.4f}")
# print(f"  RMSE: {result['metrics']['rmse']:.4f}")
# print(f"  MAE: {result['metrics']['mae']:.4f}")
# print(f"  训练 R²: {result['model_info']['train_score']:.4f}")

# print(f"\n📈 数据信息:")
# print(f"  数据形状: {result['analysis']['shape']}")
# print(f"  列数: {len(result['analysis']['columns'])}")

# # 5. 获取摘要
# print("\n步骤 5: 获取摘要")
# print("-"*70)
# summary = agent.get_summary()
# print(f"\n📋 训练摘要:")
# for key, value in summary.items():
#     if isinstance(value, float):
#         print(f"  {key}: {value:.4f}")
#     else:
#         print(f"  {key}: {value}")


# # ============================================================================
# # 方法 2: 便捷函数风格
# # ============================================================================

# print("\n\n" + "="*70)
# print("方法 2: 便捷函数风格")
# print("="*70 + "\n")

# from my_custom_agent import run_agent

# print("使用便捷函数 run_agent()...")
# print("-"*70)

# result2 = run_agent(
#     data_path=str(data.data_dir),
#     target_column="count",
#     n_estimators=50
# )

# print(f"\n✓ 运行完成!")
# print(f"  R²: {result2['metrics']['r2']:.4f}")


# # ============================================================================
# # 方法 3: 使用 DSLighting 2.0 核心协议
# # ============================================================================

# print("\n\n" + "="*70)
# print("方法 3: DSLighting 2.0 核心协议")
# print("="*70 + "\n")

# from dslighting import Context, Tool

# print("创建自定义工具和 Context...")
# print("-"*70)

# # 创建自定义分析工具
# def custom_analysis(df):
#     """自定义数据分析"""
#     return {
#         "correlation": df.corr(),
#         "skewness": df.skew(),
#         "kurtosis": df.kurtosis()
#     }

# # 封装成 Tool
# custom_tool = Tool(
#     name="advanced_analysis",
#     description="Advanced statistical analysis",
#     fn=custom_analysis
# )

# # 创建 Context
# ctx = Context(
#     task="高级数据分析",
#     data={"data_dir": str(data.data_dir)},
#     tools={"analysis": custom_tool}
# )

# print(f"\n✓ Context 创建成功!")
# print(f"  任务: {ctx.task}")
# print(f"  工具: {list(ctx.tools.keys())}")


# # ============================================================================
# # 总结
# # ============================================================================

# print("\n\n" + "="*70)
# print("✅ 测试完成!")
# print("="*70)
# print("\n💡 关键要点:")
# print("  1. ✓ 使用 DSLighting.load_data() 加载数据")
# print("  2. ✓ 创建自定义 Agent 类似 DSLighting.Agent()")
# print("  3. ✓ 使用 agent.run() 运行工作流")
# print("  4. ✓ 使用 DSLighting 2.0 核心协议 (Context, Tool)")
# print("  5. ✓ 完全兼容 DSLighting 生态系统")

# print("\n🚀 你现在可以像使用 DSLighting 一样使用自定义 Agent!")
# print("   - agent = MyCustomAgent()")
# print("   - result = agent.run(data)")
# print("   - summary = agent.get_summary()")
# print("="*70 + "\n")


import sys
sys.path.insert(0, '/Users/liufan/Applications/Github/test_pip_dslighting/my_custom_agent')

import dslighting
from my_custom_agent import MyCustomAgent

# 加载数据
data = dslighting.load_data("bike-sharing-demand")

# 创建 Agent
agent = MyCustomAgent(target_column="count", n_estimators=100)

# 运行
result = agent.run(str(data.data_dir))

# 查看结果
print(f"R²: {result['metrics']['r2']:.4f}")