"""
自定义 Benchmark 实现 - 房价预测示例

这是一个完整的 DABench 风格 benchmark 实现，展示如何：
1. 组织比赛注册目录和数据集目录
2. 实现数据准备和评分的分离
3. 集成到 DSAT 框架中
"""

import sys
import uuid
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple, Optional

import pandas as pd

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dsat.benchmark.benchmark import BaseBenchmark
from dsat.models.task import TaskDefinition

logger = logging.getLogger(__name__)


class HousePriceBenchmark(BaseBenchmark):
    """
    房价预测 Benchmark - DABench 风格实现

    目录结构:
    examples/custom_benchmark/
    ├── competitions/custom-house-price-prediction/
    │   ├── config.yaml
    │   ├── description.md
    │   ├── grade.py
    │   └── prepare.py
    └── data/custom-house-price-prediction/
        ├── raw/houses.csv
        └── prepared/
            ├── public/
            │   ├── train.csv
            │   └── sample_submission.csv
            └── private/
                └── answer.csv
    """

    def __init__(
        self,
        name: str,
        file_path: Optional[str],
        log_path: str,
        data_dir: Optional[str] = None,
        **kwargs
    ):
        """
        初始化房价预测 Benchmark

        Args:
            name: Benchmark 名称
            file_path: 任务文件路径（兼容参数，实际不使用）
            log_path: 日志和结果输出目录
            data_dir: 数据集根目录（默认为 ./data）
        """
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).parent / "data"
        self.competitions_dir = Path(__file__).parent / "competitions"

        super().__init__(name, file_path, log_path)

        # 创建日志目录
        Path(self.log_path).mkdir(parents=True, exist_ok=True)

        # 加载任务
        self.problems = self._load_problems()
        logger.info(f"HousePriceBenchmark 初始化完成，共 {len(self.problems)} 个任务")

    def _load_problems(self) -> List[Dict[str, Any]]:
        """
        加载任务列表

        Returns:
            List[Dict]: 任务列表，每个任务包含 task_id 和相关路径
        """
        competition_id = "custom-house-price-prediction"
        competition_data_dir = self.data_dir / competition_id

        if not competition_data_dir.exists():
            logger.error(f"竞赛数据目录不存在: {competition_data_dir}")
            logger.info(f"请先运行: python prepare_example_data.py")
            return []

        # 检查必要文件
        prepared_dir = competition_data_dir / "prepared"
        if not prepared_dir.exists():
            logger.error(f"数据未准备，请运行 prepare.py")
            return []

        problems = [{
            "task_id": competition_id,
            "competition_dir": str(competition_data_dir),
            "competitions_meta_dir": str(self.competitions_dir / competition_id)
        }]

        logger.debug(f"加载任务: {competition_id}")
        return problems

    def get_result_columns(self) -> List[str]:
        """
        定义结果 CSV 的列

        Returns:
            List[str]: 列名列表
        """
        return [
            "task_id",
            "submission_path",
            "rmse_score",
            "cost",
            "submission_valid",
            "error_message"
        ]

    async def evaluate_problem(
        self,
        problem: Dict[str, Any],
        eval_fn: Callable
    ) -> Tuple[Tuple, Any, Optional[str]]:
        """
        评估一个房价预测任务

        Args:
            problem: 任务信息字典
            eval_fn: DSAT 工作流评估函数

        Returns:
            Tuple: (csv_tuple, report, error_message)
        """
        task_id = problem["task_id"]
        competition_dir = Path(problem["competition_dir"])
        competitions_meta_dir = Path(problem["competitions_meta_dir"])

        logger.info(f"开始评估任务: {task_id}")

        # 定义输出文件路径
        unique_id = uuid.uuid4().hex[:6]
        output_file = Path(self.log_path) / f"submission_{task_id}_{unique_id}.csv"

        # 初始化结果变量
        rmse_score = float('inf')
        cost = 0.0
        submission_valid = False
        error_message = None

        try:
            # 1. 创建 TaskDefinition（Kaggle 风格）
            description_file = competitions_meta_dir / "description.md"
            description = description_file.read_text(encoding='utf-8') if description_file.exists() else ""

            task = TaskDefinition(
                task_id=task_id,
                task_type="kaggle",  # 文件输入输出型
                payload={
                    "description": description,
                    "public_data_dir": str(competition_dir / "prepared" / "public"),
                    "output_submission_path": str(output_file)
                }
            )

            # 2. 执行工作流
            logger.info(f"执行工作流: {task_id}")
            result, cost = await eval_fn(task)

            # 3. 检查提交文件是否生成
            if isinstance(result, str) and result.startswith("[ERROR]"):
                error_message = result
                logger.error(f"工作流执行失败: {error_message}")

            elif output_file.exists():
                # 4. 评分
                try:
                    logger.info(f"开始评分: {task_id}")

                    # 加载提交和答案
                    submission = pd.read_csv(output_file)
                    answer_file = competition_dir / "prepared" / "private" / "answer.csv"
                    answers = pd.read_csv(answer_file)

                    # 动态导入评分函数
                    sys.path.insert(0, str(self.competitions_dir))
                    from custom_house_price_prediction.grade import grade

                    # 计算 RMSE
                    rmse_score = grade(submission, answers)
                    submission_valid = True

                    logger.info(f"任务 {task_id} RMSE: {rmse_score:.2f}")

                except Exception as e:
                    error_message = f"评分失败: {str(e)}"
                    logger.error(error_message, exc_info=True)
            else:
                error_message = "提交文件未生成"
                logger.error(error_message)

        except Exception as e:
            error_message = f"任务评估过程出错: {str(e)}"
            logger.error(error_message, exc_info=True)

        # 构建结果元组
        csv_tuple = (
            task_id,
            str(output_file),
            rmse_score,
            cost,
            submission_valid,
            error_message
        )

        report = {
            "rmse": rmse_score,
            "valid": submission_valid,
            "cost": cost
        }

        return csv_tuple, report, error_message


if __name__ == "__main__":
    """
    独立测试脚本

    运行此脚本以测试 Benchmark 实现（不连接实际工作流）
    """
    import asyncio

    async def mock_eval_fn(task: TaskDefinition) -> Tuple[Any, float]:
        """模拟评估函数 - 生成随机预测"""
        print(f"[Mock] 执行任务: {task.task_id}")

        # 读取测试集数量
        public_dir = Path(task.payload["public_data_dir"])
        sample_submission = pd.read_csv(public_dir / "sample_submission.csv")

        # 生成随机预测（简单基线）
        import numpy as np
        np.random.seed(42)
        predictions = sample_submission.copy()
        predictions['predicted_price'] = np.random.uniform(200000, 400000, len(predictions))

        # 保存提交
        output_path = task.payload["output_submission_path"]
        predictions.to_csv(output_path, index=False)
        print(f"[Mock] 提交已保存: {output_path}")

        return Path(output_path), 0.0

    async def test_benchmark():
        """测试 Benchmark"""
        print("=" * 60)
        print("测试 HousePriceBenchmark")
        print("=" * 60)

        # 创建 Benchmark 实例
        benchmark = HousePriceBenchmark(
            name="house_price_test",
            file_path=None,
            log_path="./test_results"
        )

        if not benchmark.problems:
            print("\n❌ 没有加载到任务")
            print("请先运行:")
            print("  1. python prepare_example_data.py")
            print("  2. python competitions/custom-house-price-prediction/prepare.py")
            return

        print(f"\n✓ 加载了 {len(benchmark.problems)} 个任务\n")

        # 评估第一个任务
        problem = benchmark.problems[0]
        csv_tuple, report, error = await benchmark.evaluate_problem(problem, mock_eval_fn)

        # 显示结果
        print("\n" + "=" * 60)
        print("评估结果:")
        print("=" * 60)
        print(f"任务 ID: {csv_tuple[0]}")
        print(f"RMSE: {csv_tuple[2]:.2f}")
        print(f"有效提交: {csv_tuple[4]}")
        print(f"错误信息: {csv_tuple[5] or '无'}")
        print(f"\n完整报告: {report}")

    # 运行测试
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_benchmark())
