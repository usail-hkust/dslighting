# web_ui/backend/app/agents/agent_config.py
"""
Agent Configuration and Orchestration

This file defines all agents and their orchestration flow in the Web UI system.
Each agent has a specific role and follows a fixed execution order for different modes.
"""

from enum import Enum
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass

class AgentMode(Enum):
    """Execution modes for different user interactions"""
    EXPLORE = "explore"  # Data exploration and analysis
    PREPARE = "prepare"  # Data preparation and cleaning
    MODEL = "model"      # Model training configuration
    REPORT = "report"    # Report generation

class AgentRole(Enum):
    """Agent roles in the system"""
    # Routing & Decision Agents
    INTENT_ROUTER = "intent_router"
    BLUEPRINT_JUDGE = "blueprint_judge"

    # Data Analysis Agents
    DATA_ANALYST_CODE = "data_analyst_code"      # Generate analysis code
    DATA_ANALYST_SUMMARY = "data_analyst_summary" # Summarize results

    # Data Preparation Agents
    BLUEPRINT_ARCHITECT = "blueprint_architect"  # Design data prep plan
    DATA_PREP_CODE = "data_prep_code"            # Generate prep code

    # Debugging Agents
    DEBUGGER = "debugger"                        # Fix code errors
    EXPLORER = "explorer"                        # Explore data structure

    # Report Agents
    TECHNICAL_WRITER = "technical_writer"        # Generate reports

@dataclass
class AgentConfig:
    """Configuration for a single agent"""
    role: AgentRole
    name: str
    description: str
    prompt_template: Optional[str] = None
    output_model: Optional[str] = None  # Pydantic model name
    is_code_agent: bool = False
    is_report_agent: bool = False

@dataclass
class AgentFlow:
    """Defines a sequence of agents for a specific task"""
    mode: AgentMode
    description: str
    agents: List[AgentRole]
    is_parallel: bool = False  # If True, agents run in parallel

# ============================================================================
# AGENT CONFIGURATIONS
# ============================================================================

AGENT_REGISTRY: Dict[AgentRole, AgentConfig] = {
    # ============================================================================
    # ROUTING & DECISION AGENTS
    # ============================================================================
    AgentRole.INTENT_ROUTER: AgentConfig(
        role=AgentRole.INTENT_ROUTER,
        name="Intent Router",
        description="Routes user requests to appropriate agent based on intent",
        output_model="IntentRouting"
    ),

    AgentRole.BLUEPRINT_JUDGE: AgentConfig(
        role=AgentRole.BLUEPRINT_JUDGE,
        name="Blueprint Judge",
        description="Determines if user approves the proposed blueprint",
        output_model="BlueprintApproval"
    ),

    # ============================================================================
    # DATA ANALYSIS AGENTS (EXPLORE MODE)
    # ============================================================================
    AgentRole.DATA_ANALYST_CODE: AgentConfig(
        role=AgentRole.DATA_ANALYST_CODE,
        name="Data Analyst (Code Generation)",
        description="Generates Python code for data exploration and visualization",
        is_code_agent=True,
        output_model="CodeResponse"
    ),

    AgentRole.DATA_ANALYST_SUMMARY: AgentConfig(
        role=AgentRole.DATA_ANALYST_SUMMARY,
        name="Data Analyst (Result Summary)",
        description="Summarizes code execution results and responds to user questions",
        output_model="ChatResponse"
    ),

    # ============================================================================
    # DATA PREPARATION AGENTS (PREPARE MODE)
    # ============================================================================
    AgentRole.BLUEPRINT_ARCHITECT: AgentConfig(
        role=AgentRole.BLUEPRINT_ARCHITECT,
        name="Blueprint Architect",
        description="Designs data preparation blueprint based on user requirements",
        output_model="TaskBlueprint"
    ),

    AgentRole.DATA_PREP_CODE: AgentConfig(
        role=AgentRole.DATA_PREP_CODE,
        name="Data Preparation Engineer",
        description="Generates and executes data preparation code",
        is_code_agent=True,
        output_model="CodeResponse"
    ),

    # ============================================================================
    # DEBUGGING AGENTS
    # ============================================================================
    AgentRole.DEBUGGER: AgentConfig(
        role=AgentRole.DEBUGGER,
        name="Code Debugger",
        description="Fixes syntax and runtime errors in generated code",
        is_code_agent=True,
        output_model="CodeResponse"
    ),

    AgentRole.EXPLORER: AgentConfig(
        role=AgentRole.EXPLORER,
        name="Data Structure Explorer",
        description="Explores and verifies data file structures and schemas",
        output_model="ExplorerResponse"
    ),

    # ============================================================================
    # REPORT AGENTS
    # ============================================================================
    AgentRole.TECHNICAL_WRITER: AgentConfig(
        role=AgentRole.TECHNICAL_WRITER,
        name="Technical Writer",
        description="Generates technical documentation and reports",
        is_report_agent=True,
        output_model="ReportResponse"
    ),
}

# ============================================================================
# AGENT FLOWS (Orchestration Sequences)
# ============================================================================

AGENT_FLOWS: Dict[AgentMode, List[AgentFlow]] = {
    # ============================================================================
    # EXPLORE MODE - Data Analysis Flow
    # ============================================================================
    AgentMode.EXPLORE: [
        AgentFlow(
            mode=AgentMode.EXPLORE,
            description="Standard data analysis: Generate code → Execute → Summarize",
            agents=[
                AgentRole.DATA_ANALYST_CODE,    # Step 1: Generate code
                AgentRole.DATA_ANALYST_SUMMARY  # Step 2: Summarize results
            ]
        ),
        AgentFlow(
            mode=AgentMode.EXPLORE,
            description="Data analysis with error recovery: Code → Debug → Summarize",
            agents=[
                AgentRole.DATA_ANALYST_CODE,    # Step 1: Generate code
                AgentRole.DEBUGGER,              # Step 2: Fix errors (if needed)
                AgentRole.DATA_ANALYST_SUMMARY  # Step 3: Summarize results
            ]
        ),
    ],

    # ============================================================================
    # PREPARE MODE - Data Preparation Flow
    # ============================================================================
    AgentMode.PREPARE: [
        AgentFlow(
            mode=AgentMode.PREPARE,
            description="Blueprint creation flow: Architect → Judge → User Approval",
            agents=[
                AgentRole.BLUEPRINT_ARCHITECT,  # Step 1: Design blueprint
                AgentRole.BLUEPRINT_JUDGE,      # Step 2: Judge approval
            ]
        ),
        AgentFlow(
            mode=AgentMode.PREPARE,
            description="Blueprint implementation: Generate code → Execute",
            agents=[
                AgentRole.DATA_PREP_CODE,        # Step 1: Generate prep code
                AgentRole.DEBUGGER,              # Step 2: Fix errors (if needed)
            ]
        ),
    ],

    # ============================================================================
    # MODEL MODE - Model Training Configuration
    # ============================================================================
    AgentMode.MODEL: [
        AgentFlow(
            mode=AgentMode.MODEL,
            description="Model training advice and configuration",
            agents=[
                AgentRole.DATA_ANALYST_SUMMARY,  # Provide recommendations
            ]
        ),
    ],

    # ============================================================================
    # REPORT MODE - Report Generation
    # ============================================================================
    AgentMode.REPORT: [
        AgentFlow(
            mode=AgentMode.REPORT,
            description="Generate technical report",
            agents=[
                AgentRole.TECHNICAL_WRITER,       # Step 1: Generate report
            ]
        ),
    ],
}

# ============================================================================
# AGENT STATUS MESSAGES (for UI feedback)
# ============================================================================

AGENT_STATUS_MESSAGES = {
    AgentRole.INTENT_ROUTER: "分析意图...",
    AgentRole.BLUEPRINT_JUDGE: "判断方案...",
    AgentRole.DATA_ANALYST_CODE: "生成分析代码...",
    AgentRole.DATA_ANALYST_SUMMARY: "总结分析结果...",
    AgentRole.BLUEPRINT_ARCHITECT: "设计方案...",
    AgentRole.DATA_PREP_CODE: "生成处理代码...",
    AgentRole.DEBUGGER: "调试代码...",
    AgentRole.EXPLORER: "探索数据结构...",
    AgentRole.TECHNICAL_WRITER: "生成报告...",
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_agent_config(role: AgentRole) -> AgentConfig:
    """Get configuration for a specific agent"""
    return AGENT_REGISTRY.get(role)

def get_flow_for_mode(mode: AgentMode, index: int = 0) -> Optional[AgentFlow]:
    """Get the agent flow for a specific mode"""
    flows = AGENT_FLOWS.get(mode, [])
    if index < len(flows):
        return flows[index]
    return flows[0] if flows else None

def get_agent_status_message(role: AgentRole) -> str:
    """Get the status message for an agent (for UI display)"""
    return AGENT_STATUS_MESSAGES.get(role, "处理中...")
