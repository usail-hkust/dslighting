"""Built-in benchmark presets."""

from dslighting.benchmark.benchmarks.custom_benchmark import CustomBenchmark
from dslighting.benchmark.benchmarks.da_benchmark import DABenchmark
from dslighting.benchmark.benchmarks.mle_lite_benchmark import MLELiteBenchmark

try:
    from dslighting.benchmark.benchmarks.mle_benchmark import MLEBenchmark
except ImportError:
    MLEBenchmark = None

try:
    from dslighting.benchmark.benchmarks.sciencebench_benchmark import ScienceBenchBenchmark
except ImportError:
    ScienceBenchBenchmark = None

try:
    from dslighting.benchmark.benchmarks.datasci_benchmark import DataSciBenchmark
except ImportError:
    DataSciBenchmark = None

__all__ = [
    "CustomBenchmark",
    "DABenchmark",
    "MLELiteBenchmark",
    "MLEBenchmark",
    "ScienceBenchBenchmark",
    "DataSciBenchmark",
]
