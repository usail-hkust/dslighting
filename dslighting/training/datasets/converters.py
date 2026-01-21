"""
训练数据集转换器
"""
from typing import List, Dict, Any
import pandas as pd
from pathlib import Path


class DatasetConverter:
    """
    将 DSLighting 任务转换为 Agent-Lightning 训练格式

    输出格式：
    [
        {
            "task_id": "bike-sharing-demand",
            "data_dir": "/path/to/data",
            "metadata": {...}
        },
        ...
    ]
    """

    def __init__(
        self,
        data_parent_dir: str,
        registry_parent_dir: str,
    ):
        self.data_parent_dir = Path(data_parent_dir)
        self.registry_parent_dir = Path(registry_parent_dir)

    def from_task_list(
        self,
        task_ids: List[str],
    ) -> List[Dict[str, Any]]:
        """
        从任务 ID 列表创建训练数据集

        Parameters
        ----------
        task_ids : List[str]
            任务 ID 列表

        Returns
        -------
        List[Dict[str, Any]]
            训练数据集
        """
        dataset = []

        for task_id in task_ids:
            task_entry = {
                "task_id": task_id,
                "data_dir": str(self.data_parent_dir / task_id),
                "metadata": self._load_task_metadata(task_id),
            }
            dataset.append(task_entry)

        return dataset

    def from_registry(self) -> List[Dict[str, Any]]:
        """
        从 registry 目录加载所有可用任务

        Returns
        -------
        List[Dict[str, Any]]
            所有任务的训练数据集
        """
        task_dirs = [d for d in self.registry_parent_dir.iterdir() if d.is_dir()]
        task_ids = [d.name for d in task_dirs]
        return self.from_task_list(task_ids)

    def from_parquet(
        self,
        parquet_path: str,
    ) -> List[Dict[str, Any]]:
        """
        从 Parquet 文件加载训练数据集

        Parameters
        ----------
        parquet_path : str
            Parquet 文件路径

        Returns
        -------
        List[Dict[str, Any]]
            训练数据集
        """
        df = pd.read_parquet(parquet_path)
        return df.to_dict("records")

    def _load_task_metadata(self, task_id: str) -> Dict[str, Any]:
        """加载任务元数据"""
        import yaml

        config_path = self.registry_parent_dir / task_id / "config.yaml"

        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
        else:
            return {}


__all__ = ["DatasetConverter"]
