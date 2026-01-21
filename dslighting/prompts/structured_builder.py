"""
Structured Prompt Builder - 基于 Dict 格式的 Prompt 构建器

推荐用法：使用 Pydantic 定义输入输出模型，然后用 StructuredPromptBuilder 构建 prompt
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel


class StructuredPromptBuilder:
    """
    结构化 Prompt 构建器

    推荐格式：
    ```python
    prompt_dict = {
        "Role": "You are an expert...",
        "Task Goal": "...",
        "Input Data": {...},
        "Instructions": {
            "Goal": "...",
            "Guideline": "...",
        }
    }
    ```

    Example:
        builder = StructuredPromptBuilder()
        prompt = builder.build(prompt_dict)
    """

    def __init__(self, max_length: Optional[int] = None):
        """
        初始化构建器

        Args:
            max_length: 最大 prompt 长度（字符数）
        """
        self.max_length = max_length

    def build(self, prompt_dict: Dict[str, Any]) -> str:
        """
        构建最终的 prompt 字符串

        Args:
            prompt_dict: 结构化的 prompt 字典

        Returns:
            格式化的 prompt 字符串
        """
        prompt = self._dict_to_str(prompt_dict, indent=0)

        # 截断到最大长度
        if self.max_length and len(prompt) > self.max_length:
            prompt = prompt[:self.max_length] + "\n...[truncated]"

        return prompt

    def _dict_to_str(self, d: Dict, indent: int = 0) -> str:
        """将字典转换为格式化的字符串"""
        lines = []
        prefix = "  " * indent

        for key, value in d.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                lines.append(self._dict_to_str(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{prefix}{key}:")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(f"{prefix}  -")
                        lines.append(self._dict_to_str(item, indent + 2))
                    else:
                        lines.append(f"{prefix}  - {item}")
            else:
                lines.append(f"{prefix}{key}: {value}")

        return "\n".join(lines)


class PromptTemplate:
    """
    Prompt 模板基类

    推荐继承此类来定义你的 Prompt 模板

    Example:
        class MyOperatorPrompt(PromptTemplate):
            def get_input_schema(self):
                return MyInputModel

            def get_output_schema(self):
                return MyOutputModel

            def build(self, **kwargs):
                return {
                    "Role": "You are...",
                    "Task": kwargs["task"],
                    ...
                }
    """

    def get_input_schema(self) -> Optional[BaseModel]:
        """
        返回输入的 Pydantic 模型

        Returns:
            Pydantic BaseModel 类
        """
        return None

    def get_output_schema(self) -> Optional[BaseModel]:
        """
        返回输出的 Pydantic 模型

        Returns:
            Pydantic BaseModel 类
        """
        return None

    def build(self, **kwargs) -> Dict[str, Any]:
        """
        构建 prompt 字典

        Args:
            **kwargs: 输入参数

        Returns:
            prompt 字典
        """
        raise NotImplementedError("Subclasses must implement build()")


# ============ 辅助函数 ============

def truncate_output(text: str, max_length: int) -> str:
    """
    截断输出到指定长度

    Args:
        text: 原始文本
        max_length: 最大长度

    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "\n...[truncated]"


def format_code_block(code: str, language: str = "python") -> str:
    """
    格式化代码块

    Args:
        code: 代码
        language: 语言

    Returns:
        格式化的代码块
    """
    return f"```{language}\n{code}\n```"


def create_structured_prompt(
    role: str,
    task_goal: str,
    instructions: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
    guidelines: Optional[List[str]] = None,
    requirements: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    快速创建结构化 prompt 的辅助函数

    Args:
        role: 角色
        task_goal: 任务目标
        instructions: 指令字典
        context: 上下文信息（可选）
        guidelines: 指导原则列表（可选）
        requirements: 需求列表（可选）

    Returns:
        prompt 字典
    """
    prompt_dict = {
        "Role": role,
        "Task Goal": task_goal,
    }

    # 添加上下文
    if context:
        prompt_dict.update(context)

    # 构建指令
    instructions_dict = dict(instructions)

    # 添加指导原则
    if guidelines:
        instructions_dict["Guidelines"] = guidelines

    # 添加需求
    if requirements:
        instructions_dict["Requirements"] = requirements

    prompt_dict["Instructions"] = instructions_dict

    return prompt_dict
