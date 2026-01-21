"""
Custom Benchmark

完全轻量的自define Benchmark（不dependency开源framework）。
"""

import logging
from typing import Dict, List

from dslighting.benchmark.base import BaseBenchmark
from dsat.models.task import TaskDefinition

logger = logging.getLogger(__name__)


class CustomBenchmark(BaseBenchmark):
    """
    完全轻量的自define Benchmark

    用途：
    - user自defineTasklist
    - 从 config.yaml Load的Task
    - 不dependency MLE-Bench 等开源framework

    Example:
        >>> tasks = [task1, task2, task3]
        >>> benchmark = CustomBenchmark("my-benchmark", tasks)
        >>> results = await benchmark.run_evaluation(eval_fn)
        >>> stats = benchmark.get_statistics()
    """

    def __init__(
        self,
        name: str,
        tasks: List[TaskDefinition],
        log_path: str = "runs/benchmarks/custom",
    ):
        """
        Initialize自define Benchmark

        Args:
            name: Benchmark 名称
            tasks: Tasklist
            log_path: 日志Path
        """
        super().__init__(name, tasks, log_path)

        logger.debug(f"✓ Custom Benchmark initialized: {name}")
        logger.info(f"  Tasks: {len(tasks)}")

    async def run_evaluation(self, eval_fn, **kwargs) -> List[Dict]:
        """
        批量Evaluate

        完全使用 DSLighting 的Evaluate逻辑，不dependency外部framework
        """
        return await super().run_evaluation(eval_fn, **kwargs)
