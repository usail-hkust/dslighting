# web_ui/backend/app/services/agent_registry.py

"""
Agent Registry - 定义所有agent的能力和接口

这个模块定义了系统中每个agent的标准化能力、输入输出格式，
以及agent之间的依赖关系。所有agent必须在此注册才能使用。
"""

from enum import Enum
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass


class AgentType(Enum):
    """Agent类型枚举"""
    DATA_EXPLORER = "DataExplorer"
    DEBUGGER = "Debugger"
    DATA_PREP = "DataPrep"
    ANALYST = "Analyst"
    REPORTER = "Reporter"


@dataclass
class AgentCapability:
    """Agent能力定义"""
    name: str                    # 能力名称
    description: str             # 能力描述
    input_format: Dict[str, Any] # 输入格式要求
    output_format: Dict[str, Any]# 输出格式
    example_use_case: str        # 使用案例


# Agent能力注册表
AGENT_CAPABILITIES: Dict[AgentType, List[AgentCapability]] = {
    AgentType.DATA_EXPLORER: [
        AgentCapability(
            name="analyze_schema",
            description="分析数据文件的结构、列名、类型、编码",
            input_format={
                "file_path": "str - 可选，特定文件的路径",
                "error_msg": "str - 可选，触发分析的错误信息"
            },
            output_format={
                "schema_info": "Dict[str, Any] - 文件schema信息",
                "loading_guide": "str - 如何加载该文件",
                "file_structure": "str - 文件树结构"
            },
            example_use_case="Debugger遇到FileNotFoundError时调用"
        ),
        AgentCapability(
            name="discover_files",
            description="发现并列出workspace中的所有数据文件",
            input_format={
                "pattern": "str - 可选，文件匹配模式"
            },
            output_format={
                "files": "List[str] - 文件路径列表",
                "file_types": "Dict[str, int] - 文件类型统计"
            },
            example_use_case="DataPrep开始前查看可用文件"
        ),
        AgentCapability(
            name="detect_encoding",
            description="检测文件的编码格式",
            input_format={
                "file_path": "str - 文件路径"
            },
            output_format={
                "encoding": "str - 检测到的编码",
                "confidence": "float - 置信度"
            },
            example_use_case="读取文本文件前确定编码"
        )
    ],

    AgentType.DEBUGGER: [
        AgentCapability(
            name="fix_code_error",
            description="修复代码执行错误",
            input_format={
                "code": "str - 错误的代码",
                "error_msg": "str - 错误信息",
                "context": "str - 可选，额外的上下文信息"
            },
            output_format={
                "fixed_code": "str - 修复后的代码",
                "explanation": "str - 修复说明"
            },
            example_use_case="用户代码执行失败后调用"
        ),
        AgentCapability(
            name="review_code",
            description="代码审查和优化建议",
            input_format={
                "code": "str - 待审查的代码"
            },
            output_format={
                "review_result": "str - 审查结果",
                "optimized_code": "str - 可选，优化后的代码",
                "suggestions": "List[str] - 改进建议"
            },
            example_use_case="用户请求代码审查时调用"
        ),
        AgentCapability(
            name="optimize_performance",
            description="性能优化",
            input_format={
                "code": "str - 待优化的代码",
                "performance_issue": "str - 可选，性能问题描述"
            },
            output_format={
                "optimized_code": "str - 优化后的代码",
                "improvements": "List[str] - 改进点列表"
            },
            example_use_case="代码执行慢时调用"
        )
    ],

    AgentType.DATA_PREP: [
        AgentCapability(
            name="clean_data",
            description="数据清洗：处理缺失值、异常值、重复值",
            input_format={
                "source_files": "List[str] - 源文件路径",
                "cleaning_rules": "Dict - 可选，清洗规则"
            },
            output_format={
                "cleaned_files": "List[str] - 清洗后的文件路径",
                "cleaning_report": "str - 清洗报告"
            },
            example_use_case="Analyst发现数据质量问题后调用"
        ),
        AgentCapability(
            name="transform_data",
            description="数据转换：特征工程、格式转换",
            input_format={
                "source_files": "List[str] - 源文件",
                "transformations": "List[Dict] - 转换操作列表"
            },
            output_format={
                "transformed_files": "List[str] - 转换后的文件",
                "transform_report": "str - 转换报告"
            },
            example_use_case="Analyst需要特征工程时调用"
        ),
        AgentCapability(
            name="split_data",
            description="数据分割：train/test/answer分割",
            input_format={
                "source_file": "str - 源文件",
                "split_config": "Dict - 分割配置"
            },
            output_format={
                "train_file": "str - 训练集路径",
                "test_file": "str - 测试集路径",
                "answer_file": "str - 答案文件路径",
                "split_report": "str - 分割报告"
            },
            example_use_case="准备模型训练数据时调用"
        ),
        AgentCapability(
            name="check_prepared_data",
            description="检查数据准备状态",
            input_format={},
            output_format={
                "is_prepared": "bool - 是否已准备好",
                "prepared_files": "List[str] - 已准备的文件",
                "manifest": "Dict - manifest.json内容"
            },
            example_use_case="Analyst开始分析前检查数据"
        )
    ],

    AgentType.ANALYST: [
        AgentCapability(
            name="generate_statistics",
            description="生成统计分析：均值、方差、分布等",
            input_format={
                "data_source": "str - 数据源路径或DataFrame引用",
                "columns": "List[str] - 可选，要分析的列"
            },
            output_format={
                "statistics": "Dict - 统计结果",
                "summary_text": "str - 统计摘要"
            },
            example_use_case="Reporter需要数据统计时调用"
        ),
        AgentCapability(
            name="create_visualization",
            description="创建数据可视化",
            input_format={
                "data_source": "str - 数据源",
                "viz_type": "str - 可视化类型",
                "config": "Dict - 可视化配置"
            },
            output_format={
                "image_paths": "List[str] - 生成的图片路径",
                "insights": "List[str] - 洞察"
            },
            example_use_case="Reporter需要图表时调用"
        ),
        AgentCapability(
            name="analyze_correlations",
            description="相关性分析",
            input_format={
                "data_source": "str - 数据源",
                "method": "str - 相关性计算方法"
            },
            output_format={
                "correlation_matrix": "Dict - 相关性矩阵",
                "key_correlations": "List[Dict] - 主要相关性"
            },
            example_use_case="探索性数据分析时调用"
        ),
        AgentCapability(
            name="compare_datasets",
            description="比较多个数据集的差异",
            input_format={
                "datasets": "List[str] - 数据集路径列表",
                "comparison_type": "str - 比较类型"
            },
            output_format={
                "comparison_report": "str - 比较报告",
                "differences": "List[Dict] - 差异列表"
            },
            example_use_case="比较train和test数据分布时调用"
        )
    ],

    AgentType.REPORTER: [
        AgentCapability(
            name="summarize_analysis",
            description="总结分析结果",
            input_format={
                "analysis_results": "Dict - 分析结果",
                "focus": "str - 可选，关注重点"
            },
            output_format={
                "summary": "str - 总结文本",
                "key_findings": "List[str] - 关键发现"
            },
            example_use_case="Analyst完成分析后调用"
        ),
        AgentCapability(
            name="generate_report",
            description="生成完整报告",
            input_format={
                "content": "Dict - 报告内容",
                "format": "str - 报告格式"
            },
            output_format={
                "report_path": "str - 报告文件路径",
                "report_content": "str - 报告内容"
            },
            example_use_case="任务完成后生成最终报告"
        ),
        AgentCapability(
            name="format_insights",
            description="格式化洞察发现",
            input_format={
                "insights": "List[str] - 洞察列表",
                "format": "str - 格式化风格"
            },
            output_format={
                "formatted_text": "str - 格式化后的文本",
                "bullet_points": "List[str] - 要点列表"
            },
            example_use_case="向用户展示分析结果时调用"
        )
    ]
}


# Agent依赖关系图
AGENT_DEPENDENCIES: Dict[AgentType, List[AgentType]] = {
    AgentType.DEBUGGER: [AgentType.DATA_EXPLORER],  # Debugger可能需要DataExplorer分析数据问题
    AgentType.DATA_PREP: [AgentType.DATA_EXPLORER], # DataPrep可能需要了解原始数据结构
    AgentType.ANALYST: [AgentType.DATA_PREP, AgentType.DATA_EXPLORER],  # Analyst可能需要检查数据准备状态
    AgentType.REPORTER: [AgentType.ANALYST],        # Reporter需要Analyst的结果来生成报告
    AgentType.DATA_EXPLORER: []                     # DataExplorer是基础agent，无依赖
}


def get_agent_capabilities(agent_type: AgentType) -> List[AgentCapability]:
    """获取指定agent的所有能力"""
    return AGENT_CAPABILITIES.get(agent_type, [])


def get_capability_info(agent_type: AgentType, capability_name: str) -> Optional[AgentCapability]:
    """获取特定agent的特定能力详情"""
    capabilities = get_agent_capabilities(agent_type)
    for cap in capabilities:
        if cap.name == capability_name:
            return cap
    return None


def can_agent_call(caller: AgentType, target: AgentType) -> bool:
    """
    检查一个agent是否可以调用另一个agent

    规则：
    1. 所有agent都可以调用Debugger（获取代码修复帮助）
    2. 所有agent都可以调用DataExplorer（获取数据信息）
    3. 同类型agent可以互相调用（递归调用自身的能力）
    4. Analyst可以调用DataPrep（检查数据准备）
    5. Reporter可以调用Analyst（获取分析结果）
    6. Debugger和DataPrep可以互相调用（修复数据准备代码）
    """
    # 规则1: 所有agent都可以调用DataExplorer（基础agent）
    if target == AgentType.DATA_EXPLORER:
        return True

    # 规则2: 所有agent都可以调用Debugger（获取代码修复帮助）
    if target == AgentType.DEBUGGER:
        return True

    # 规则3: 同类型agent可以互相调用（递归调用自身的能力）
    if caller == target:
        return True

    # 规则4: Reporter可以调用Analyst（获取分析结果用于报告）
    if caller == AgentType.REPORTER and target == AgentType.ANALYST:
        return True

    # 规则5: Analyst可以调用DataPrep（检查/准备数据）
    if caller == AgentType.ANALYST and target == AgentType.DATA_PREP:
        return True

    # 规则6: Debugger和DataPrep可以互相调用（修复数据准备代码）
    if caller in [AgentType.DEBUGGER, AgentType.DATA_PREP] and target in [AgentType.DEBUGGER, AgentType.DATA_PREP]:
        return True

    # 其他情况不允许调用
    return False


def get_agent_description(agent_type: AgentType) -> str:
    """获取agent的描述"""
    descriptions = {
        AgentType.DATA_EXPLORER: "数据探索专家 - 分析数据结构、文件格式、编码，提供加载指南",
        AgentType.DEBUGGER: "代码调试专家 - 修复错误、优化性能、代码审查",
        AgentType.DATA_PREP: "数据准备专家 - 数据清洗、转换、分割，确保数据质量",
        AgentType.ANALYST: "数据分析专家 - 统计分析、可视化、相关性分析",
        AgentType.REPORTER: "报告生成专家 - 总结发现、生成报告、格式化洞察"
    }
    return descriptions.get(agent_type, "Unknown Agent")


def print_agent_registry():
    """打印所有agent的能力（用于调试）"""
    for agent_type, capabilities in AGENT_CAPABILITIES.items():
        print(f"\n{'='*60}")
        print(f"🤖 {get_agent_description(agent_type)}")
        print(f"{'='*60}")
        print(f"Can be called by: {[t.value for t in AgentType if can_agent_call(t, agent_type)]}\n")

        for cap in capabilities:
            print(f"  📌 {cap.name}")
            print(f"     {cap.description}")
            print(f"     Example: {cap.example_use_case}\n")


if __name__ == "__main__":
    print_agent_registry()
