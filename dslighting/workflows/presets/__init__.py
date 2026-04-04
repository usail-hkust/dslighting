"""
Preset Workflows - Ready-to-Use Workflows

统一导出的预设 workflows
"""
try:
    # ========== Manual Workflows ==========
    from dslighting.workflows.manual.autokaggle_workflow import AutoKaggleWorkflow
    from dslighting.workflows.manual.data_interpreter_workflow import DataInterpreterWorkflow
    from dslighting.workflows.manual.deepanalyze_workflow import DeepAnalyzeWorkflow
    from dslighting.workflows.manual.dsagent_workflow import DSAgentWorkflow

    # ========== Search Workflows ==========
    from dslighting.workflows.search.aide_workflow import AIDEWorkflow
    from dslighting.workflows.search.automind_workflow import AutoMindWorkflow
    from dslighting.workflows.search.aflow_workflow import AFlowWorkflow
    from dslighting.workflows.search.react_workflow import ReActWorkflow

    # 创建别名（为了向后兼容和简化命名）
    AIDE = AIDEWorkflow
    AutoKaggle = AutoKaggleWorkflow
    DataInterpreter = DataInterpreterWorkflow
    DeepAnalyze = DeepAnalyzeWorkflow
    DSAgent = DSAgentWorkflow
    AutoMind = AutoMindWorkflow
    AFlow = AFlowWorkflow
    ReAct = ReActWorkflow

except ImportError as e:
    # 如果 workflows 不可用，提供占位符
    AIDE = None
    AutoKaggle = None
    DataInterpreter = None
    DeepAnalyze = None
    DSAgent = None
    AutoMind = None
    AFlow = None
    ReAct = None
    AIDEWorkflow = None
    AutoKaggleWorkflow = None
    DataInterpreterWorkflow = None
    DeepAnalyzeWorkflow = None
    DSAgentWorkflow = None
    AutoMindWorkflow = None
    AFlowWorkflow = None
    ReActWorkflow = None

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
    "ReAct",
    # 完整类名
    "AIDEWorkflow",
    "AutoKaggleWorkflow",
    "DataInterpreterWorkflow",
    "DeepAnalyzeWorkflow",
    "DSAgentWorkflow",
    "AutoMindWorkflow",
    "AFlowWorkflow",
    "ReActWorkflow",
]
