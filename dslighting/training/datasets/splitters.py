"""
训练/验证集分割工具
"""
from typing import List, Dict, Any, Tuple
import random


def train_test_split_tasks(
    tasks: List[Dict[str, Any]],
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    将任务列表分割为训练集和测试集

    Parameters
    ----------
    tasks : List[Dict[str, Any]]
        任务列表
    test_size : float
        测试集比例
    random_state : int
        随机种子

    Returns
    -------
    train_tasks : List[Dict[str, Any]]
        训练任务
    test_tasks : List[Dict[str, Any]]
        测试任务
    """
    random.seed(random_state)
    shuffled = tasks.copy()
    random.shuffle(shuffled)

    split_idx = int(len(shuffled) * (1 - test_size))
    train_tasks = shuffled[:split_idx]
    test_tasks = shuffled[split_idx:]

    return train_tasks, test_tasks


__all__ = ["train_test_split_tasks"]
