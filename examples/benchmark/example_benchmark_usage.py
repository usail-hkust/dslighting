"""
DSLighting Benchmark 使用示例

演示如何使用新的 Benchmark 系统
"""

import asyncio
from pathlib import Path

from dslighting.benchmark import (
    MLELiteBenchmark,
    CustomBenchmark,
    BenchmarkFactory,
)
from dslighting import Agent


# ============================================================================
# 示例 1: 使用 MLELiteBenchmark（继承 MLE-Bench + DSLighting）
# ============================================================================

async def example_mle_lite():
    """
    使用 MLE-Bench Lite - 精选核心竞赛

    继承能力：
    - MLE-Bench 的任务加载和评分
    - DSLighting 的统计分析和接口
    """
    print("\n" + "=" * 80)
    print("示例 1: MLE-Bench Lite")
    print("=" * 80 + "\n")

    # 创建 MLE-Lite Benchmark（使用默认精选任务）
    benchmark = MLELiteBenchmark()

    # 或者自定义任务列表
    # benchmark = MLELiteBenchmark(
    #     competitions=["bike-sharing-demand", "titanic"]
    # )

    print(f"Benchmark: {benchmark.name}")
    print(f"Tasks: {len(benchmark.tasks)}")
    print(f"Log path: {benchmark.log_path}")
    print()

    # 创建评估函数
    async def eval_fn(task):
        """评估单个任务"""
        print(f"  Evaluating: {task.task_id}")

        # 使用 DSLighting Agent 运行任务
        agent = Agent()
        result = agent.run(
            task_id=task.task_id,
            max_iterations=3,
        )

        return {
            "score": result.score,
            "cost": result.cost if hasattr(result, 'cost') else 0.0,
            "duration": result.duration,
        }

    # 运行批量评估
    results = await benchmark.run_evaluation(eval_fn, model_name="test-model")

    # 获取统计信息
    stats = benchmark.get_statistics()

    print("\n" + "-" * 80)
    print("统计信息:")
    print(f"  总任务数: {stats.get('total_tasks', 0)}")
    print(f"  成功任务: {stats.get('successful_tasks', 0)}")
    print(f"  失败任务: {stats.get('failed_tasks', 0)}")
    print(f"  平均分数: {stats.get('avg_score', 0):.4f}")
    print(f"  成功率: {stats.get('success_rate', 0):.2%}")
    print("-" * 80 + "\n")


# ============================================================================
# 示例 2: 使用 CustomBenchmark（完全自定义）
# ============================================================================

async def example_custom():
    """
    使用 CustomBenchmark - 完全轻量

    不依赖 MLE-Bench，完全使用 DSLighting 能力
    """
    print("\n" + "=" * 80)
    print("示例 2: Custom Benchmark")
    print("=" * 80 + "\n")

    # 加载任务
    from dslighting.core.data_loader import load_data

    task_ids = ["bike-sharing-demand", "titanic"]

    tasks = []
    for task_id in task_ids:
        loaded_data = load_data(task_id=task_id)
        from dsat.models.task import TaskDefinition

        task = TaskDefinition(
            task_id=task_id,
            task_type=loaded_data.get_task_type(),
            payload={
                "description": loaded_data.description,
            }
        )
        tasks.append(task)

    # 创建 Custom Benchmark
    benchmark = CustomBenchmark("my-custom", tasks)

    print(f"Benchmark: {benchmark.name}")
    print(f"Tasks: {len(benchmark.tasks)}")
    print()

    # 评估函数
    async def eval_fn(task):
        print(f"  Evaluating: {task.task_id}")
        agent = Agent()
        result = agent.run(task_id=task.task_id, max_iterations=3)
        return {
            "score": result.score,
            "duration": result.duration,
        }

    # 运行评估
    results = await benchmark.run_evaluation(eval_fn)

    print("\n✓ 评估完成\n")


# ============================================================================
# 示例 3: 使用 BenchmarkFactory（从配置文件加载）
# ============================================================================

async def example_factory():
    """
    使用 BenchmarkFactory - 从 config.yaml 加载

    支持配置驱动的批量任务管理
    """
    print("\n" + "=" * 80)
    print("示例 3: BenchmarkFactory")
    print("=" * 80 + "\n")

    # 从配置文件创建工厂
    factory = BenchmarkFactory.from_config_file(
        config_path=Path("config.yaml"),
        registry_dir=Path("dslighting/registry"),
        data_dir=Path("data/competitions"),
    )

    # 列出可用的 Benchmark
    benchmarks = factory.list_benchmarks()
    print(f"可用的 Benchmark: {benchmarks}")
    print()

    # 创建 MLE-Lite Benchmark
    benchmark = factory.create("mle-lite")

    print(f"Benchmark: {benchmark.name}")
    print(f"Tasks: {len(benchmark.tasks)}")
    print()

    # 评估函数
    async def eval_fn(task):
        print(f"  Evaluating: {task.task_id}")
        # 简化版评估
        return {
            "score": 0.85,
            "cost": 0.1,
            "duration": 60.0,
        }

    # 运行评估
    results = await benchmark.run_evaluation(eval_fn, model_name="test-model")

    print("\n✓ 评估完成\n")

    # 查看统计
    stats = benchmark.get_statistics()
    print(f"统计: {stats}\n")


# ============================================================================
# 示例 4: 列出可用的竞赛
# ============================================================================

def example_list_competitions():
    """
    列出所有可用的竞赛
    """
    print("\n" + "=" * 80)
    print("示例 4: 列出可用竞赛")
    print("=" * 80 + "\n")

    # 获取默认精选竞赛
    default_comps = MLELiteBenchmark.get_default_competitions()
    print(f"默认精选竞赛 ({len(default_comps)}):")
    for comp in default_comps:
        print(f"  - {comp}")
    print()

    # 列出所有可用竞赛
    available_comps = MLELiteBenchmark.list_available_competitions(
        data_dir=Path("data/competitions")
    )
    print(f"所有可用竞赛 ({len(available_comps)}):")
    for comp in available_comps[:10]:  # 只显示前 10 个
        print(f"  - {comp}")
    if len(available_comps) > 10:
        print(f"  ... 还有 {len(available_comps) - 10} 个")
    print()


# ============================================================================
# 主函数
# ============================================================================

async def main():
    """运行所有示例"""
    print("\n" + "=" * 80)
    print("DSLighting Benchmark 使用示例")
    print("=" * 80)

    # 示例 1: MLE-Lite Benchmark
    # await example_mle_lite()

    # 示例 2: Custom Benchmark
    # await example_custom()

    # 示例 3: BenchmarkFactory
    # await example_factory()

    # 示例 4: 列出竞赛
    example_list_competitions()

    print("=" * 80)
    print("✓ 所有示例运行完成")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
