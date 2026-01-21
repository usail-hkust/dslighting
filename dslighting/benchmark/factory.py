"""
Benchmark Factory

Factoryclass，用于从ConfigCreate不同type的 Benchmark instance。
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


class BenchmarkFactory:
    """
    Benchmark Factoryclass

    支持Create：
    1. 内置 Benchmark（mle-lite, dabench）
    2. 自define Benchmark（从 config.yaml）
    3. 继承开源 Benchmark（MLEBenchmark, DABenchmark）

    Example:
        >>> # 方式 1: 从ConfigFileLoad
        >>> factory = BenchmarkFactory.from_config_file("config.yaml")
        >>> benchmark = factory.create("mle-lite")
        >>>
        >>> # 方式 2: 直接Create
        >>> benchmark = BenchmarkFactory.create("mle-lite", config_data)
        >>>
        >>> # 方式 3: 列出可用的 Benchmark
        >>> benchmarks = factory.list_benchmarks()
    """

    # 内置 Benchmark type注册表
    BENCHMARK_TYPES = {
        "custom": "dslighting.benchmark.custom:CustomBenchmark",
        "mle-lite": "dslighting.benchmark.mle_lite:MLELiteBenchmark",
        # 未来扩展：
        # "dabench": "dslighting.benchmark.dabench:DABenchmark",
    }

    def __init__(
        self,
        config_path: Optional[Path] = None,
        registry_dir: Optional[Path] = None,
        data_dir: Optional[Path] = None,
    ):
        """
        InitializeFactory

        Args:
            config_path: ConfigFilePath（config.yaml）
            registry_dir: 注册表目录
            data_dir: data directory
        """
        self.config_path = config_path
        self.registry_dir = registry_dir
        self.data_dir = data_dir
        self.config = None

        if config_path and config_path.exists():
            self.load_config(config_path)

    def load_config(self, config_path: Path):
        """
        LoadConfigFile

        Args:
            config_path: ConfigFilePath
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
            name: Benchmark 名称或type
            config: Configdict/dictionary（If为 None，从 self.config 读取）
            **kwargs: 额外的Parameter

        Returns:
            Benchmark instance

        Raises:
            ValueError: If Benchmark type不存在
        """
        # If没有Provide config，使用已Load的Config
        if config is None and self.config:
            benchmarks_config = self.config.get("benchmarks", {})
            config = benchmarks_config.get(name)

            if not config:
                raise ValueError(f"Benchmark '{name}' not found in config")

        # Get Benchmark type
        if isinstance(config, dict):
            benchmark_type = config.get("type", "custom")
        else:
            benchmark_type = "custom"

        # 根据typeCreate Benchmark
        if benchmark_type == "custom":
            from dslighting.benchmark.base import BaseBenchmark
            return self._create_custom_benchmark(name, config, **kwargs)

        elif benchmark_type == "mle-lite":
            from dslighting.benchmark.mle_lite import MLELiteBenchmark
            return self._create_mle_lite_benchmark(name, config, **kwargs)

        else:
            # 尝试从注册表查找
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
        Create自define Benchmark（纯 DSLighting）

        Args:
            name: Benchmark 名称
            config: Configdict/dictionary
            **kwargs: 额外Parameter

        Returns:
            BaseBenchmark instance
        """
        from dslighting.benchmark.base import BaseBenchmark

        # 使用defaultPath
        registry_dir = self.registry_dir or Path("dslighting/registry")
        data_dir = self.data_dir or Path("data/competitions")

        logger.info(f"Creating custom benchmark: {name}")

        return BaseBenchmark.from_config(
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
        Create MLE-Bench Lite（继承 MLE-Bench 能力）

        Args:
            name: Benchmark 名称
            config: Configdict/dictionary
            **kwargs: 额外Parameter

        Returns:
            MLELiteBenchmark instance
        """
        from dslighting.benchmark.mle_lite import MLELiteBenchmark

        # 提取竞赛list
        competitions = None
        if isinstance(config, dict):
            competitions = config.get("competitions") or config.get("tasks")

        logger.info(f"Creating MLE-Lite benchmark: {name}")

        return MLELiteBenchmark(
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
        从注册表Create Benchmark

        Args:
            benchmark_type: Benchmark type
            name: Benchmark 名称
            config: Configdict/dictionary
            **kwargs: 额外Parameter

        Returns:
            Benchmark instance
        """
        import_str = self.BENCHMARK_TYPES[benchmark_type]

        try:
            # 动态导入
            module_path, class_name = import_str.split(":")
            import importlib
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)

            # Createinstance
            return cls(name, config, **kwargs)

        except Exception as e:
            logger.error(f"Failed to create benchmark from registry: {e}")
            raise

    def list_benchmarks(self) -> List[str]:
        """
        列出ConfigFile中define的All Benchmark

        Returns:
            Benchmark 名称list
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
        从ConfigFileCreateFactoryinstance

        Args:
            config_path: ConfigFilePath
            registry_dir: 注册表目录
            data_dir: data directory

        Returns:
            BenchmarkFactory instance

        Example:
            >>> factory = BenchmarkFactory.from_config_file("config.yaml")
            >>> benchmark = factory.create("mle-lite")
        """
        # SetdefaultPath
        if registry_dir is None:
            registry_dir = Path("dslighting/registry")
        if data_dir is None:
            data_dir = Path("data/competitions")

        return cls(
            config_path=config_path,
            registry_dir=registry_dir,
            data_dir=data_dir,
        )
