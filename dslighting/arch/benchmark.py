"""Architecture-layer benchmark exports."""

from dslighting.benchmark import (
    BaseBenchmark,
    BaseBenchmarkEvaluator,
    BenchmarkFactory,
    CustomBenchmark,
    KaggleEvaluator,
    MLELiteBenchmark,
    RuntimeSchedulerOptions,
)

try:
    from dslighting.benchmark import (
        DABenchmark,
        DataSciBenchmark,
        MLEStyleBenchmark,
        MLEBenchmark,
        ScienceBenchBenchmark,
    )

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
        "ScienceBenchBenchmark",
        "DataSciBenchmark",
    ]
except ImportError:
    __all__ = [
        "BaseBenchmark",
        "BenchmarkFactory",
        "RuntimeSchedulerOptions",
        "MLELiteBenchmark",
        "CustomBenchmark",
        "BaseBenchmarkEvaluator",
        "KaggleEvaluator",
    ]
