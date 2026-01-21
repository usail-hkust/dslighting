"""
DSLighting Benchmark System

提供轻量级的批量评估能力，支持：
1. 基础 BaseBenchmark（纯 DSLighting）
2. MLELiteBenchmark（继承 MLE-Bench + DSLighting）
3. CustomBenchmark（完全自定义）
4. BenchmarkFactory（从配置创建）

Example:
    >>> from dslighting.benchmark import MLELiteBenchmark, BenchmarkFactory
    >>>
    >>> # 方式 1: 直接创建
    >>> benchmark = MLELiteBenchmark()
    >>> results = await benchmark.run_evaluation(eval_fn)
    >>>
    >>> # 方式 2: 从配置创建
    >>> factory = BenchmarkFactory.from_config_file("config.yaml")
    >>> benchmark = factory.create("mle-lite")
    >>> results = await benchmark.run_evaluation(eval_fn)
"""

# 导出 DSLighting Benchmark 类
from dslighting.benchmark.base import BaseBenchmark
from dslighting.benchmark.factory import BenchmarkFactory
from dslighting.benchmark.mle_lite import MLELiteBenchmark
from dslighting.benchmark.custom import CustomBenchmark

# 也重新导出 DSAT Benchmark（向后兼容）
try:
    from dsat.benchmark.benchmark import BaseBenchmark as DSATBaseBenchmark
    from dsat.benchmark.mle import MLEBenchmark
    from dsat.benchmark.sciencebench import ScienceBenchBenchmark

    # 为了避免冲突，使用不同的名字
    DSATBaseBenchmark = DSATBaseBenchmark
    DSATMLEBenchmark = MLEBenchmark
    DSATScienceBenchBenchmark = ScienceBenchBenchmark

    __all__ = [
        # DSLighting Benchmark（新）
        "BaseBenchmark",
        "BenchmarkFactory",
        "MLELiteBenchmark",
        "CustomBenchmark",
        # DSAT Benchmark（向后兼容）
        "DSATBaseBenchmark",
        "DSATMLEBenchmark",
        "DSATScienceBenchBenchmark",
    ]

except ImportError:
    # DSAT 不可用
    __all__ = [
        "BaseBenchmark",
        "BenchmarkFactory",
        "MLELiteBenchmark",
        "CustomBenchmark",
    ]
