"""
Preset Agents - Ready-to-Use Agents

完全从 DSAT 重新导出的预设 agents
"""
try:
    # ========== Manual Workflows ==========
    from dsat.workflows.manual.autokaggle_workflow import AutoKaggleWorkflow
    from dsat.workflows.manual.data_interpreter_workflow import DataInterpreterWorkflow
    from dsat.workflows.manual.deepanalyze_workflow import DeepAnalyzeWorkflow
    from dsat.workflows.manual.dsagent_workflow import DSAgentWorkflow

    # ========== Search Workflows ==========
    from dsat.workflows.search.aide_workflow import AIDEWorkflow
    from dsat.workflows.search.automind_workflow import AutoMindWorkflow
    from dsat.workflows.search.aflow_workflow import AFlowWorkflow

    # 创建别名（为了向后兼容和简化命名）
    AIDE = AIDEWorkflow
    AutoKaggle = AutoKaggleWorkflow
    DataInterpreter = DataInterpreterWorkflow
    DeepAnalyze = DeepAnalyzeWorkflow
    DSAgent = DSAgentWorkflow
    AutoMind = AutoMindWorkflow
    AFlow = AFlowWorkflow

except ImportError as e:
    # 如果 DSAT 不可用，提供占位符
    AIDE = None
    AutoKaggle = None
    DataInterpreter = None
    DeepAnalyze = None
    DSAgent = None
    AutoMind = None
    AFlow = None
    AIDEWorkflow = None
    AutoKaggleWorkflow = None
    DataInterpreterWorkflow = None
    DeepAnalyzeWorkflow = None
    DSAgentWorkflow = None
    AutoMindWorkflow = None
    AFlowWorkflow = None

__all__ = [
    # 手动 workflows
    "AIDE",
    "AutoKaggle",
    "DataInterpreter",
    "DeepAnalyze",
    "DSAgent",
    # 搜索 workflows
    "AutoMind",
    "AFlow",
    # 完整类名
    "AIDEWorkflow",
    "AutoKaggleWorkflow",
    "DataInterpreterWorkflow",
    "DeepAnalyzeWorkflow",
    "DSAgentWorkflow",
    "AutoMindWorkflow",
    "AFlowWorkflow",
]
