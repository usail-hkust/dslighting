"""
Benchmark Factory

Factory class for creating different types of Benchmark instances from Config.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

DEFAULT_REGISTRY_DIR = Path("dslighting/benchmark/vendor/mlebench/competitions")


class BenchmarkFactory:
    """
    Benchmark Factory class

    Supports creating:
    1. Built-in Benchmarks (mle-lite, dabench)
    2. Custom Benchmarks (from config.yaml)
    3. Extended Open-source Benchmarks (MLEBenchmark, DABenchmark)

    Example:
        >>> # Method 1: Load from config file
        >>> factory = BenchmarkFactory.from_config_file("config.yaml")
        >>> benchmark = factory.create("mle-lite")
        >>>
        >>> # Method 2: Create directly
        >>> benchmark = BenchmarkFactory.create("mle-lite", config_data)
        >>>
        >>> # Method 3: List available benchmarks
        >>> benchmarks = factory.list_benchmarks()
    """

    # Built-in Benchmark type registry
    BENCHMARK_TYPES = {
        "custom": "dslighting.benchmark.benchmarks.custom_benchmark:CustomBenchmark",
        "mle-lite": "dslighting.benchmark.benchmarks.mle_lite_benchmark:MLELiteBenchmark",
        "dabench": "dslighting.benchmark.benchmarks.da_benchmark:DABenchmark",
        # Future extensions:
        # "dabench": "dslighting.benchmark.vendor.dabench:DABenchmark",
    }

    def __init__(
        self,
        config_path: Optional[Path] = None,
        registry_dir: Optional[Path] = None,
        data_dir: Optional[Path] = None,
    ):
        """
        Initialize Factory

        Args:
            config_path: Config file path (config.yaml)
            registry_dir: Registry directory
            data_dir: Data directory
        """
        self.config_path = config_path
        self.registry_dir = registry_dir
        self.data_dir = data_dir
        self.config = None

        if config_path and config_path.exists():
            self.load_config(config_path)

    def load_config(self, config_path: Path):
        """
        Load config file

        Args:
            config_path: Config file path
        """
        try:
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f)
            logger.info(f"✓ Config loaded from: {config_path}")

        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    def create(
        self,
        name: str,
        config: Optional[Dict] = None,
        **kwargs
    ):
        """
        Create Benchmark instance

        Args:
            name: Benchmark name or type
            config: Config dict/dictionary (if None, read from self.config)
            **kwargs: Extra parameters

        Returns:
            Benchmark instance

        Raises:
            ValueError: If benchmark type doesn't exist
        """
        # If no config provided, use loaded config
        if config is None and self.config:
            benchmarks_config = self.config.get("benchmarks", {})
            config = benchmarks_config.get(name)

            if not config:
                raise ValueError(f"Benchmark '{name}' not found in config")

        # Get benchmark type
        if isinstance(config, dict):
            benchmark_type = config.get("type", "custom")
        else:
            benchmark_type = "custom"

        # Create benchmark based on type
        if benchmark_type == "custom":
            return self._create_custom_benchmark(name, config, **kwargs)

        elif benchmark_type == "mle-lite":
            from dslighting.benchmark.benchmarks.mle_lite_benchmark import MLELiteBenchmark
            return self._create_mle_lite_benchmark(name, config, **kwargs)

        elif benchmark_type == "dabench":
            return self._create_dabench_benchmark(name, config, **kwargs)

        else:
            # Try to find in registry
            if benchmark_type in self.BENCHMARK_TYPES:
                return self._create_from_registry(benchmark_type, name, config, **kwargs)
            else:
                raise ValueError(f"Unknown benchmark type: {benchmark_type}")

    def _create_custom_benchmark(
        self,
        name: str,
        config: Dict,
        **kwargs
    ):
        """
        Create custom benchmark (pure DSLighting)

        Args:
            name: Benchmark name
            config: Config dict/dictionary
            **kwargs: Extra parameters

        Returns:
            BaseBenchmark instance
        """
        from dslighting.benchmark.benchmarks.custom_benchmark import CustomBenchmark

        # Use default path
        registry_dir = self.registry_dir or DEFAULT_REGISTRY_DIR
        data_dir = self.data_dir or Path("data/competitions")

        logger.info(f"Creating custom benchmark: {name}")

        return CustomBenchmark.from_config(
            name=name,
            config=config,
            registry_dir=registry_dir,
            data_dir=data_dir,
        )

    def _create_mle_lite_benchmark(
        self,
        name: str,
        config: Dict,
        **kwargs
    ):
        """
        Create MLE-Bench Lite (inherits MLE-Bench capabilities)

        Args:
            name: Benchmark name
            config: Config dict/dictionary
            **kwargs: Extra parameters

        Returns:
            MLELiteBenchmark instance
        """
        from dslighting.benchmark.benchmarks.mle_lite_benchmark import MLELiteBenchmark

        # Extract competition list
        competitions = None
        if isinstance(config, dict):
            competitions = config.get("competitions") or config.get("tasks")

        logger.info(f"Creating MLE-Lite benchmark: {name}")

        return MLELiteBenchmark(
            competitions=competitions,
            **kwargs
        )

    def _create_dabench_benchmark(
        self,
        name: str,
        config: Dict,
        **kwargs
    ):
        """
        Create DABenchmark (dedicated DABench tasks)
        """
        from dslighting.benchmark.benchmarks.da_benchmark import DABenchmark

        competitions = None
        if isinstance(config, dict):
            competitions = config.get("competitions") or config.get("tasks")

        logger.info(f"Creating DABenchmark: {name}")

        return DABenchmark(
            name=name,
            competitions=competitions,
            **kwargs
        )

    def _create_from_registry(
        self,
        benchmark_type: str,
        name: str,
        config: Dict,
        **kwargs
    ):
        """
        Create Benchmark from registry

        Args:
            benchmark_type: Benchmark type
            name: Benchmark name
            config: Config dict/dictionary
            **kwargs: Extra parameters

        Returns:
            Benchmark instance
        """
        import_str = self.BENCHMARK_TYPES[benchmark_type]

        try:
            # Dynamic import
            module_path, class_name = import_str.split(":")
            import importlib
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)

            # Create instance
            return cls(name, config, **kwargs)

        except Exception as e:
            logger.error(f"Failed to create benchmark from registry: {e}")
            raise

    def list_benchmarks(self) -> List[str]:
        """
        List all benchmarks defined in config file

        Returns:
            List of benchmark names
        """
        if not self.config:
            return []

        return list(self.config.get("benchmarks", {}).keys())

    @classmethod
    def from_config_file(
        cls,
        config_path: Path,
        registry_dir: Optional[Path] = None,
        data_dir: Optional[Path] = None,
    ) -> "BenchmarkFactory":
        """
        Create factory instance from config file

        Args:
            config_path: Config file path
            registry_dir: Registry directory
            data_dir: Data directory

        Returns:
            BenchmarkFactory instance

        Example:
            >>> factory = BenchmarkFactory.from_config_file("config.yaml")
            >>> benchmark = factory.create("mle-lite")
        """
        # Set default paths
        if registry_dir is None:
            registry_dir = DEFAULT_REGISTRY_DIR
        if data_dir is None:
            data_dir = Path("data/competitions")

        return cls(
            config_path=config_path,
            registry_dir=registry_dir,
            data_dir=data_dir,
        )
