"""Built-in benchmark presets."""

from dslighting.benchmark.benchmarks.custom_benchmark import CustomBenchmark
try:
    from dslighting.benchmark.benchmarks.da_benchmark import DABenchmark
except ImportError:
    DABenchmark = None

try:
    from dslighting.benchmark.benchmarks.mle_lite_benchmark import MLELiteBenchmark
except ImportError:
    MLELiteBenchmark = None

try:
    from dslighting.benchmark.benchmarks.mle_style_benchmark import MLEStyleBenchmark
except ImportError:
    MLEStyleBenchmark = None

try:
    from dslighting.benchmark.benchmarks.mle_benchmark import MLEBenchmark
except ImportError:
    MLEBenchmark = None

try:
    from dslighting.benchmark.benchmarks.datasci_benchmark import DataSciBenchmark
except ImportError:
    DataSciBenchmark = None

__all__ = [
    "CustomBenchmark",
    "DABenchmark",
    "MLELiteBenchmark",
    "MLEStyleBenchmark",
    "MLEBenchmark",
    "DataSciBenchmark",
]
