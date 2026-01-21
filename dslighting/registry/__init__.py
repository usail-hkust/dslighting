"""
DSLighting Registry - Task configuration loader

加载任务配置文件（config.yaml）和描述文件（description.md）
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Any

import yaml

logger = logging.getLogger(__name__)


def load_task_config(task_id: str) -> Dict[str, Any]:
    """
    加载任务配置

    Args:
        task_id: 任务 ID（例如 "bike-sharing-demand"）

    Returns:
        配置字典，包含:
        - data_path: 数据目录路径
        - description: description.md 文件路径
        - task_description: 任务描述文本（如果 description.md 存在）
        - dataset: 数据集配置（sample_submission, answers 等）
        - grader: 评分器配置

    Raises:
        FileNotFoundError: 如果任务配置文件不存在
    """
    # 获取 registry 目录
    registry_dir = Path(__file__).parent
    task_dir = registry_dir / task_id

    if not task_dir.exists():
        raise FileNotFoundError(f"Task configuration not found: {task_id}")

    # 加载 config.yaml
    config_file = task_dir / "config.yaml"
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")

    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 添加 description.md 路径
    description_file = task_dir / "description.md"
    if description_file.exists():
        config["description"] = str(description_file)
        # 同时加载 description 内容作为 task_description
        with open(description_file, 'r', encoding='utf-8') as f:
            config["task_description"] = f.read()
    else:
        logger.warning(f"Description file not found: {description_file}")
        config["description"] = None
        config["task_description"] = config.get("name", task_id)

    # 添加数据路径
    # 尝试多个可能的数据目录位置
    data_parent_dir = None

    # 可能的父目录
    possible_parents = [
        # 当前项目的 data/competitions/
        Path.cwd() / "data" / "competitions",
        # DSLighting package 的 data/competitions/
        Path(__file__).parent.parent.parent / "data" / "competitions",
        # MLE-Bench 的 competitions/
        Path(__file__).parent.parent.parent / "benchmarks" / "mlebench" / "competitions",
        # 绝对路径
        Path("/Users/liufan/Applications/Github/dslighting/data/competitions"),
    ]

    for parent_dir in possible_parents:
        data_path = parent_dir / task_id
        if data_path.exists():
            data_parent_dir = data_path
            logger.info(f"Found data directory: {data_parent_dir}")
            break

    if data_parent_dir:
        config["data_path"] = str(data_parent_dir)
    else:
        logger.warning(f"Could not find data directory for task: {task_id}")
        config["data_path"] = None

    logger.debug(f"Loaded task config: {task_id}")
    return config


def list_available_tasks() -> list:
    """
    列出所有可用的任务

    Returns:
        任务 ID 列表
    """
    registry_dir = Path(__file__).parent
    task_dirs = [d.name for d in registry_dir.iterdir() if d.is_dir() and not d.name.startswith('_')]
    return sorted(task_dirs)
