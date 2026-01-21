"""
示例: 自定义 Operator

这是一个完整的示例，展示如何创建自定义 Operator 并在 Agent 中使用。
"""
import logging
from typing import Dict, Any

from dslighting.operators import Operator
from dslighting.services import LLMService

logger = logging.getLogger(__name__)


class TextAnalysisOperator(Operator):
    """
    文本分析 Operator - 示例

    功能：使用 LLM 分析文本
    """

    def __init__(
        self,
        llm_service: LLMService,
        analysis_type: str = "sentiment",
        **kwargs
    ):
        """
        初始化

        Args:
            llm_service: LLM 服务
            analysis_type: 分析类型 (sentiment, keywords, summary)
        """
        super().__init__(name="TextAnalysisOperator", **kwargs)
        self.llm_service = llm_service
        self.analysis_type = analysis_type

    async def __call__(
        self,
        text: str,
        custom_instruction: str = ""
    ) -> Dict[str, Any]:
        """
        分析文本

        Args:
            text: 要分析的文本
            custom_instruction: 自定义指令

        Returns:
            分析结果字典
        """
        logger.info(f"[{self.name}] Analyzing text (type: {self.analysis_type})")

        # 构建提示
        if self.analysis_type == "sentiment":
            prompt = f"""
Please analyze the sentiment of the following text.
Respond with a JSON object containing:
- sentiment: "positive", "negative", or "neutral"
- confidence: a number between 0 and 1
- key_points: list of key points

Text:
{text}
"""
        elif self.analysis_type == "keywords":
            prompt = f"""
Please extract the main keywords from the following text.
Respond with a JSON object containing:
- keywords: list of keywords
- topics: list of main topics

Text:
{text}
"""
        elif self.analysis_type == "summary":
            prompt = f"""
Please provide a concise summary of the following text.
Respond with a JSON object containing:
- summary: the summary text
- word_count: number of words in summary

Text:
{text}
"""
        else:
            raise ValueError(f"Unknown analysis type: {self.analysis_type}")

        # 添加自定义指令
        if custom_instruction:
            prompt += f"\n\nAdditional instruction:\n{custom_instruction}"

        # 调用 LLM
        try:
            response = await self.llm_service.call(prompt)
            logger.info(f"[{self.name}] Analysis completed")

            return {
                "analysis_type": self.analysis_type,
                "raw_response": response,
                "text_length": len(text),
            }

        except Exception as e:
            logger.error(f"[{self.name}] Analysis failed: {e}")
            raise


# 也在 custom/__init__.py 中导出
# from .example_operator import TextAnalysisOperator
