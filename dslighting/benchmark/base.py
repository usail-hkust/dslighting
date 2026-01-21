"""
DSLighting Base Benchmark

轻量级 Benchmark 基class，Provide统一的批量Evaluate和统计Analyze能力。
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pandas as pd

from dsat.models.task import TaskDefinition

logger = logging.getLogger(__name__)


class BaseBenchmark:
    """
    DSLighting 轻量级 Benchmark 基class

    核心能力：
    - 统一的批量Evaluateinterface
    - 统计Analyze（平均分、中位数、成本等）
    - Config驱动（从 config.yaml Load）
    - 灵活的Outputformat

    继承此class可以：
    1. Create完全自define的 Benchmark
    2. 作为多重继承的基class（如 MLELiteBenchmark）
    3. Provide统一的 DSLighting API

    Example:
        >>> tasks = [task1, task2, task3]
        >>> benchmark = BaseBenchmark("my-benchmark", tasks)
        >>> results = await benchmark.run_evaluation(eval_fn)
        >>> stats = benchmark.get_statistics()
    """

    def __init__(
        self,
        name: str,
        tasks: List[TaskDefinition],
        log_path: str = "runs/benchmarks",
    ):
        """
        Initialize Benchmark

        Args:
            name: Benchmark 名称
            tasks: Tasklist（TaskDefinition objectlist）
            log_path: 日志OutputPath
        """
        self.name = name
        self.tasks = tasks
        self.log_path = Path(log_path)
        self.results = []

        # Create日志目录
        self.log_path.mkdir(parents=True, exist_ok=True)

        # resultFilePath
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_path = self.log_path / f"{self.name}_results_{timestamp}.csv"
        self.stats_path = self.log_path / f"{self.name}_stats_{timestamp}.json"

        logger.debug(f"✓ Benchmark initialized: {self.name}")
        logger.info(f"  Tasks: {len(self.tasks)}")
        logger.info(f"  Log path: {self.log_path}")

    async def run_evaluation(self, eval_fn: Callable, **kwargs) -> List[Dict[str, Any]]:
        """
        批量EvaluateAllTask

        Args:
            eval_fn: Evaluatefunction，接收 TaskDefinition，ReturnEvaluateresult
            **kwargs: 额外的Parameter（如 model_name）

        Returns:
            Evaluateresultlist

        Example:
            >>> async def my_eval_fn(task):
            ...     result = await run_task(task)
            ...     return {"score": result.score, "cost": result.cost}
            >>> results = await benchmark.run_evaluation(my_eval_fn)
        """
        if not self.tasks:
            logger.warning(f"No tasks to evaluate in benchmark '{self.name}'")
            return []

        logger.info(f"Starting evaluation for benchmark '{self.name}' with {len(self.tasks)} tasks")

        results = []
        completed = 0
        failed = 0

        # 顺序EvaluateEachTask
        for i, task in enumerate(self.tasks, 1):
            try:
                logger.info(f"[{i}/{len(self.tasks)}] Evaluating task: {task.task_id}")

                # 调用Evaluatefunction
                result = await eval_fn(task, **kwargs)

                # 确保Returndict/dictionary
                if isinstance(result, dict):
                    result["task_id"] = task.task_id
                    results.append(result)
                    completed += 1
                else:
                    logger.warning(f"  Invalid result type: {type(result)}")
                    failed += 1

            except Exception as e:
                logger.error(f"  Task '{task.task_id}' failed: {e}")
                failed += 1
                # 记录failed的Task
                results.append({
                    "task_id": task.task_id,
                    "score": None,
                    "error": str(e),
                })

        # 保存result
        self.results = results
        self._save_results(results, **kwargs)

        logger.info(f"Evaluation complete: {completed} succeeded, {failed} failed")

        return results

    def get_statistics(self, results: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        计算统计信息

        Args:
            results: Evaluateresultlist（If为 None，使用 self.results）

        Returns:
            统计信息dict/dictionary，contains：
            - total_tasks: 总Task数
            - avg_score: 平均分数
            - median_score: 中位数分数
            - std_score: standard差
            - avg_cost: 平均成本
            - total_cost: 总成本
            - success_rate: success率
        """
        if results is None:
            results = self.results

        if not results:
            return {}

        stats = {
            "total_tasks": len(results),
            "successful_tasks": 0,
            "failed_tasks": 0,
        }

        # 提取分数和成本
        scores = []
        costs = []
        durations = []

        for result in results:
            if result.get("score") is not None:
                scores.append(float(result["score"]))
                stats["successful_tasks"] += 1
            else:
                stats["failed_tasks"] += 1

            if result.get("cost") is not None:
                costs.append(float(result["cost"]))

            if result.get("duration") is not None:
                durations.append(float(result["duration"]))

        # 计算分数统计
        if scores:
            import numpy as np
            stats["avg_score"] = float(np.mean(scores))
            stats["median_score"] = float(np.median(scores))
            stats["std_score"] = float(np.std(scores))
            stats["min_score"] = float(np.min(scores))
            stats["max_score"] = float(np.max(scores))

        # 计算成本统计
        if costs:
            import numpy as np
            stats["avg_cost"] = float(np.mean(costs))
            stats["total_cost"] = float(np.sum(costs))

        # 计算时长统计
        if durations:
            import numpy as np
            stats["avg_duration"] = float(np.mean(durations))
            stats["total_duration"] = float(np.sum(durations))

        # success率
        stats["success_rate"] = stats["successful_tasks"] / stats["total_tasks"]

        return stats

    def _save_results(self, results: List[Dict], **kwargs):
        """
        保存result到 CSV File

        Args:
            results: Evaluateresultlist
            **kwargs: 额外的元Data（如 model_name）
        """
        try:
            # 转换为 DataFrame
            df = pd.DataFrame(results)

            # 保存 CSV
            df.to_csv(self.results_path, index=False)
            logger.info(f"✓ Results saved to: {self.results_path}")

            # 保存统计信息
            stats = self.get_statistics(results)

            # Add元Data
            stats["benchmark_name"] = self.name
            stats["timestamp"] = datetime.now().isoformat()
            stats["model_name"] = kwargs.get("model_name", "unknown")

            # 保存 JSON
            import json
            with open(self.stats_path, "w") as f:
                json.dump(stats, f, indent=2)
            logger.info(f"✓ Statistics saved to: {self.stats_path}")

        except Exception as e:
            logger.error(f"Failed to save results: {e}")

    @classmethod
    def from_config(
        cls,
        name: str,
        config: Dict[str, Any],
        registry_dir: Path,
        data_dir: Path,
    ) -> "BaseBenchmark":
        """
        从ConfigCreate Benchmark

        Args:
            name: Benchmark 名称
            config: Configdict/dictionary
            registry_dir: 注册表目录
            data_dir: data directory

        Returns:
            BaseBenchmark instance

        Example:
            >>> config = {
            ...     "tasks": [
            ...         {"task_id": "bike-sharing-demand"},
            ...         {"task_id": "titanic"},
            ...     ]
            ... }
            >>> benchmark = BaseBenchmark.from_config("my-bench", config, registry_dir, data_dir)
        """
        from dslighting.core.data_loader import load_data

        tasks = []

        for task_config in config.get("tasks", []):
            task_id = task_config.get("task_id") or task_config.get("id")

            if not task_id:
                logger.warning(f"Skipping task without task_id: {task_config}")
                continue

            try:
                # LoadData
                loaded_data = load_data(
                    task_id=task_id,
                    registry_parent_dir=str(registry_dir),
                    data_parent_dir=str(data_dir),
                )

                # Create TaskDefinition
                task = TaskDefinition(
                    task_id=task_id,
                    task_type=loaded_data.get_task_type(),
                    payload={
                        "description": loaded_data.description or "",
                        "data_dir": str(loaded_data.data_dir) if loaded_data.data_dir else None,
                    }
                )

                tasks.append(task)

            except Exception as e:
                logger.warning(f"Failed to load task '{task_id}': {e}")
                continue

        logger.info(f"Loaded {len(tasks)} tasks from config")

        return cls(name, tasks)
