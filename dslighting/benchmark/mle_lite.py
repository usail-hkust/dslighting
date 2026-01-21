"""
MLE-Bench Lite Benchmark

继承 MLE-Bench 的能力 + DSLighting 的Base能力。
"""

import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yaml

from dslighting.benchmark.base import BaseBenchmark
from dsat.models.task import TaskDefinition

logger = logging.getLogger(__name__)


class MLELiteBenchmark(BaseBenchmark):
    """
    MLE-Bench Lite - 精选核心竞赛

    继承能力：
    1. BaseBenchmark (DSLighting):
       - 统一的批量Evaluateinterface
       - 统计Analyze
       - Config驱动

    2. MLEBenchmark (开源):
       - TaskLoad（Registry）
       - Grading逻辑（grade_csv）
       - Competition 管理

    Example:
        >>> # 使用default精选Task
        >>> benchmark = MLELiteBenchmark()
        >>> results = await benchmark.run_evaluation(eval_fn)
        >>>
        >>> # 自defineTasklist
        >>> benchmark = MLELiteBenchmark(
        ...     competitions=["bike-sharing-demand", "titanic"]
        ... )
        >>> results = await benchmark.run_evaluation(eval_fn)
    """

    # 内置精选Tasklist（10个核心竞赛）
    DEFAULT_COMPETITIONS = [
        "bike-sharing-demand",
        "titanic",
        "house-prices",
        "new-york-city-taxi-fare-prediction",
        "tabular-playground-series-dec-2021",
        "histopathologic-cancer-detection",
        "aptos2019-blindness-detection",
        "spooky-author-identification",
        "us-patent-phrase-to-phrase-matching",
        "google-quest-challenge",
    ]

    def __init__(
        self,
        competitions: Optional[List[str]] = None,
        name: str = "mle-lite",
        log_path: str = "runs/benchmarks/mle-lite",
        data_dir: Optional[Path] = None,
    ):
        """
        Initialize MLE-Bench Lite

        Args:
            competitions: 竞赛list（If为 None，使用default精选Task）
            name: Benchmark 名称
            log_path: 日志Path
            data_dir: data directory
        """
        # 使用default精选Task或自defineTask
        self.competitions = competitions or self.DEFAULT_COMPETITIONS

        # data directory
        if data_dir is None:
            data_dir = Path("data/competitions")

        self.data_dir = Path(data_dir)

        # Initialize MLE-Bench 能力
        self._init_mlebench()

        # 转换为 TaskDefinition
        tasks = self._convert_to_task_definitions()

        # Initialize BaseBenchmark（DSLighting Base能力）
        super().__init__(name, tasks, log_path)

        logger.debug(f"✓ MLE-Lite Benchmark initialized")
        logger.info(f"  Competitions: {len(self.competitions)}")
        logger.info(f"  Data dir: {self.data_dir}")

    def _init_mlebench(self):
        """
        Initialize MLE-Bench 能力

        这里只Initializeneed/require的部分，不Create完整的 MLEBenchmark instance
        """
        try:
            # Add mlebench 到 sys.path（Ifneed/require）
            import sys
            benchmarks_path = Path(__file__).parent.parent.parent / "benchmarks"
            if benchmarks_path.exists():
                if str(benchmarks_path) not in sys.path:
                    sys.path.insert(0, str(benchmarks_path))

            # Createmodule别名（向后兼容）
            if "mlebench" not in sys.modules:
                try:
                    mod = __import__("benchmarks.mlebench", fromlist=["*"])
                    sys.modules["mlebench"] = mod
                    sys.modules["mlebench.competitions"] = mod.competitions
                except ImportError:
                    pass

            # 导入 MLE-Bench component
            from mlebench.registry import Registry
            from mlebench.data import is_dataset_prepared

            self.mle_registry = Registry()
            self.mle_registry = self.mle_registry.set_data_dir(self.data_dir)

            self.is_dataset_prepared = is_dataset_prepared

            logger.info(f"✓ MLE-Bench capabilities loaded")

        except ImportError as e:
            logger.warning(f"⚠️  MLE-Bench import failed: {e}")
            logger.warning(f"   Will run without MLE-Bench integration")
            self.mle_registry = None
            self.is_dataset_prepared = None

    def _convert_to_task_definitions(self) -> List[TaskDefinition]:
        """
        使用 MLE-Bench 能力转换为 TaskDefinition

        Returns:
            TaskDefinition list
        """
        tasks = []

        for comp_id in self.competitions:
            try:
                # 使用 MLE-Bench Registry 查找竞赛
                if self.mle_registry:
                    try:
                        competition = self.mle_registry.get_competition(comp_id)
                        description = competition.description if hasattr(competition, 'description') else f"Competition: {comp_id}"

                        # GetDataPath
                        public_dir = competition.public_dir if hasattr(competition, 'public_dir') else None
                        private_dir = competition.private_dir if hasattr(competition, 'private_dir') else None

                    except Exception as e:
                        logger.warning(f"  Competition '{comp_id}' not found in MLE registry: {e}")
                        # 降级到manual构造
                        description = f"Competition: {comp_id}"
                        public_dir = None
                        private_dir = None
                else:
                    # 没有 MLE-Bench，manual构造
                    description = f"Competition: {comp_id}"
                    public_dir = None
                    private_dir = None

                # Create TaskDefinition
                task = TaskDefinition(
                    task_id=comp_id,
                    task_type="kaggle",
                    payload={
                        "description": description,
                        "data_dir": str(self.data_dir / comp_id),
                        "public_data_dir": str(public_dir) if public_dir else str(self.data_dir / comp_id / "prepared" / "public"),
                        "output_submission_path": str(self.data_dir / comp_id / "submission.csv"),
                    }
                )

                tasks.append(task)

            except Exception as e:
                logger.warning(f"Failed to convert competition '{comp_id}': {e}")
                continue

        logger.info(f"✓ Converted {len(tasks)} competitions to TaskDefinition")

        return tasks

    async def run_evaluation(self, eval_fn: Callable, **kwargs) -> List[Dict[str, Any]]:
        """
        批量Evaluate - 使用 MLE-Bench 的Grading能力

        Args:
            eval_fn: Evaluatefunction
            **kwargs: 额外Parameter

        Returns:
            Evaluateresultlist
        """
        logger.info(f"Running MLE-Lite evaluation with {len(self.tasks)} tasks")

        # 调用 BaseBenchmark 的批量Evaluate
        results = await super().run_evaluation(eval_fn, **kwargs)

        # 可以在这里Add MLE-Bench 特有的后Process
        # e.g.：使用 MLE-Bench 的排行榜比较

        return results

    def grade_submission(
        self,
        task_id: str,
        submission_path: Path,
    ) -> Optional[float]:
        """
        使用 MLE-Bench 的Grading逻辑Gradingsingle提交

        Args:
            task_id: Task ID
            submission_path: 提交FilePath

        Returns:
            分数（IfGradingfailedReturn None）
        """
        if not self.mle_registry:
            logger.warning("MLE-Bench not available, cannot grade submission")
            return None

        try:
            from mlebench.grade import grade_csv

            # Get竞赛
            competition = self.mle_registry.get_competition(task_id)

            # Grading
            report = grade_csv(submission_path, competition)

            return report.score if report.score is not None else None

        except Exception as e:
            logger.error(f"Grading failed for '{task_id}': {e}")
            return None

    @classmethod
    def get_default_competitions(cls) -> List[str]:
        """
        Getdefault精选Tasklist

        Returns:
            竞赛 ID list
        """
        return cls.DEFAULT_COMPETITIONS.copy()

    @classmethod
    def list_available_competitions(
        cls,
        data_dir: Optional[Path] = None,
    ) -> List[str]:
        """
        列出可用的竞赛

        Args:
            data_dir: data directory

        Returns:
            可用竞赛list
        """
        if data_dir is None:
            data_dir = Path("data/competitions")

        competitions = []

        # 扫描data directory
        for comp_dir in data_dir.iterdir():
            if comp_dir.is_dir() and (comp_dir / "prepared").exists():
                competitions.append(comp_dir.name)

        return sorted(competitions)
