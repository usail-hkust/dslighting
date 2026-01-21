"""
VERL 配置生成器
"""
from typing import Dict, Any, Optional


class VerlConfigBuilder:
    """
    VERL 训练配置构建器

    使用示例:
    >>> config = VerlConfigBuilder.default()
    >>> config = VerlConfigBuilder.qwen()
    >>> config = VerlConfigBuilder.custom(
    ...     model_path="Qwen/Qwen2.5-Coder-1.5B-Instruct",
    ...     learning_rate=1e-6,
    ... )
    """

    @staticmethod
    def default() -> Dict[str, Any]:
        """默认配置"""
        return {
            "algorithm": {
                "adv_estimator": "grpo",
                "use_kl_in_reward": False,
            },
            "data": {
                "train_batch_size": 32,
                "max_prompt_length": 4096,
                "max_response_length": 2048,
            },
            "actor_rollout_ref": {
                "rollout": {
                    "name": "vllm",
                    "n": 4,  # GRPO group size
                    "multi_turn": {"format": "hermes"},
                },
                "actor": {
                    "ppo_mini_batch_size": 32,
                    "optim": {"lr": 1e-6},
                },
                "model": {
                    "path": "Qwen/Qwen2.5-Coder-1.5B-Instruct",
                },
            },
            "trainer": {
                "n_gpus_per_node": 1,
                "val_before_train": True,
                "test_freq": 32,
                "save_freq": 64,
                "total_epochs": 2,
            },
        }

    @staticmethod
    def qwen() -> Dict[str, Any]:
        """Qwen 模型预设"""
        config = VerlConfigBuilder.default()
        config["actor_rollout_ref"]["model"]["path"] = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
        return config

    @staticmethod
    def llama() -> Dict[str, Any]:
        """LLaMA 模型预设"""
        config = VerlConfigBuilder.default()
        config["actor_rollout_ref"]["model"]["path"] = "meta-llama/Llama-3.2-1B-Instruct"
        config["actor_rollout_ref"]["rollout"]["multi_turn"]["format"] = "llama3_json"
        return config

    @staticmethod
    def custom(
        model_path: str,
        learning_rate: float = 1e-6,
        train_batch_size: int = 32,
        group_size: int = 4,
        **kwargs
    ) -> Dict[str, Any]:
        """
        自定义配置

        Parameters
        ----------
        model_path : str
            模型路径
        learning_rate : float
            学习率
        train_batch_size : int
            训练批次大小
        group_size : int
            GRPO group size
        **kwargs
            其他配置参数

        Returns
        -------
        Dict[str, Any]
            VERL 配置
        """
        config = VerlConfigBuilder.default()

        # 应用自定义参数
        config["actor_rollout_ref"]["model"]["path"] = model_path
        config["actor_rollout_ref"]["actor"]["optim"]["lr"] = learning_rate
        config["data"]["train_batch_size"] = train_batch_size
        config["actor_rollout_ref"]["rollout"]["n"] = group_size

        # 应用额外参数
        for key, value in kwargs.items():
            keys = key.split(".")
            config_part = config
            for k in keys[:-1]:
                config_part = config_part[k]
            config_part[keys[-1]] = value

        return config


__all__ = ["VerlConfigBuilder"]
