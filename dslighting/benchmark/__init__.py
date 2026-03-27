"""
DSLighting Benchmark System

Provides lightweight batch evaluation capabilities, supporting:
1. BaseBenchmark (pure DSLighting)
2. MLELiteBenchmark (inherits MLE-Bench + DSLighting)
3. CustomBenchmark (fully customizable)
4. BenchmarkFactory (create from config)

Example:
    >>> from dslighting.benchmark import MLELiteBenchmark, BenchmarkFactory
    >>>
    >>> # Method 1: Create directly
    >>> benchmark = MLELiteBenchmark()
    >>> results = await benchmark.run_evaluation(eval_fn)
    >>>
    >>> # Method 2: Create from config
    >>> factory = BenchmarkFactory.from_config_file("config.yaml")
    >>> benchmark = factory.create("mle-lite")
    >>> results = await benchmark.run_evaluation(eval_fn)
"""

# Export DSLighting Benchmark classes
from dslighting.benchmark.core.base import BaseBenchmark
from dslighting.benchmark.core.factory import BenchmarkFactory
from dslighting.benchmark.core.scheduler_core import RuntimeSchedulerOptions
from dslighting.benchmark.benchmarks.custom_benchmark import CustomBenchmark
from dslighting.benchmark.evaluators import BaseBenchmarkEvaluator, KaggleEvaluator

try:
    from dslighting.benchmark.benchmarks.mle_lite_benchmark import MLELiteBenchmark
    from dslighting.benchmark.benchmarks.da_benchmark import DABenchmark
    from dslighting.benchmark.benchmarks.mle_style_benchmark import MLEStyleBenchmark
    from dslighting.benchmark.benchmarks.mle_benchmark import MLEBenchmark
    from dslighting.benchmark.benchmarks.datasci_benchmark import DataSciBenchmark

    __all__ = [
        "BaseBenchmark",
        "BenchmarkFactory",
        "RuntimeSchedulerOptions",
        "MLELiteBenchmark",
        "CustomBenchmark",
        "BaseBenchmarkEvaluator",
        "KaggleEvaluator",
        "DABenchmark",
        "MLEStyleBenchmark",
        "MLEBenchmark",
        "DataSciBenchmark",
    ]

except ImportError:
    MLELiteBenchmark = None
    __all__ = [
        "BaseBenchmark",
        "BenchmarkFactory",
        "RuntimeSchedulerOptions",
        "MLELiteBenchmark",
        "CustomBenchmark",
        "BaseBenchmarkEvaluator",
        "KaggleEvaluator",
    ]
