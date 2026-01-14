# web_ui/backend/app/services/agent_dispatcher.py

"""
Agent Dispatcher - 中央调度器（支持所有agent互相调用）

这是agent之间通信的核心组件，负责：
1. 路由agent调用请求
2. 管理agent之间的依赖关系
3. 提供统一的调用接口
4. 处理调用链和上下文传递
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from .agent_registry import (
    AgentType, get_agent_capabilities, get_capability_info,
    can_agent_call, get_agent_description
)
from .llm_factory import get_llm
from .chat_logic import (
    _run_active_exploration,
    _read_eda_context,
    _verify_prepared_data
)
from ..models.llm_formats import CodeResponse, ChatResponse

logger = logging.getLogger(__name__)


class AgentDispatcher:
    """
    Agent中央调度器

    所有agent之间的调用都通过这个dispatcher进行。
    它负责：
    - 验证调用权限
    - 路由到正确的agent实现
    - 传递上下文信息
    - 处理调用链
    - 检测和防止循环调用
    """

    # 配置常量
    MAX_CALL_DEPTH = 10  # 最大调用深度
    MAX_REPEATED_AGENTS = 3  # 同一agent在调用链中最多出现次数

    def __init__(
        self,
        sandbox,
        sandbox_dir: Path,
        base_context: str,
        caller_agent: AgentType = AgentType.DATA_EXPLORER,  # 默认调用者
        call_chain: Optional[List[AgentType]] = None  # 支持传入已有调用链
    ):
        self.sandbox = sandbox
        self.sandbox_dir = sandbox_dir
        self.base_context = base_context
        self.caller_agent = caller_agent

        # 调用链追踪和循环检测
        if call_chain is None:
            self.call_chain: List[AgentType] = [caller_agent]
        else:
            self.call_chain = call_chain.copy()

        # 调用历史记录（用于检测模式）
        self.call_history: List[Dict[str, Any]] = []

    async def call(
        self,
        target_agent: AgentType,
        capability: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        通用的agent调用方法（带循环检测）

        Args:
            target_agent: 要调用的目标agent
            capability: 要使用的能力名称
            **kwargs: 能力特定的参数

        Returns:
            Dict包含调用结果
        """
        # 1. 检查调用权限
        if not can_agent_call(self.caller_agent, target_agent):
            logger.warning(f"⚠️ {self.caller_agent.value} 不允许调用 {target_agent.value}")
            return {
                "success": False,
                "error": f"Permission denied: {self.caller_agent.value} cannot call {target_agent.value}"
            }

        # 2. 检查调用深度
        if len(self.call_chain) >= self.MAX_CALL_DEPTH:
            logger.error(f"🚫 达到最大调用深度 ({self.MAX_CALL_DEPTH})")
            logger.error(f"   调用链: {' → '.join([a.value for a in self.call_chain])}")
            return {
                "success": False,
                "error": f"Maximum call depth ({self.MAX_CALL_DEPTH}) exceeded. Possible infinite loop detected."
            }

        # 3. 检测循环模式
        loop_detection = self._detect_loop_pattern(target_agent)
        if loop_detection["has_loop"]:
            logger.error(f"🚫 检测到循环调用模式: {loop_detection['pattern']}")
            logger.error(f"   调用链: {' → '.join([a.value for a in self.call_chain])}")
            return {
                "success": False,
                "error": f"Loop detected: {loop_detection['pattern']}. Breaking the loop to prevent infinite recursion."
            }

        # 4. 检查同一agent重复调用次数
        agent_count = sum(1 for a in self.call_chain if a == target_agent)
        if agent_count >= self.MAX_REPEATED_AGENTS:
            logger.error(f"🚫 Agent {target_agent.value} 在调用链中出现 {agent_count} 次（最多 {self.MAX_REPEATED_AGENTS} 次）")
            chain_str = ' → '.join([a.value for a in self.call_chain])
            logger.error(f"   调用链: {chain_str}")
            return {
                "success": False,
                "error": f"Agent {target_agent.value} called {agent_count} times (max {self.MAX_REPEATED_AGENTS}). Possible loop detected."
            }

        # 5. 记录到调用链
        self.call_chain.append(target_agent)
        chain_str = ' → '.join([a.value for a in self.call_chain])
        logger.info(f"🔗 Agent调用链 (深度={len(self.call_chain)}): {chain_str}")

        # 6. 记录调用历史
        self.call_history.append({
            "caller": self.caller_agent.value,
            "target": target_agent.value,
            "capability": capability,
            "depth": len(self.call_chain)
        })

        # 7. 路由到具体的agent实现
        try:
            result = await self._route_to_agent(target_agent, capability, **kwargs)
            result["success"] = True
            logger.info(f"✅ {target_agent.value}.{capability}() 执行成功")
        except Exception as e:
            logger.error(f"❌ {target_agent.value}.{capability}() 执行失败: {e}")
            result = {
                "success": False,
                "error": str(e)
            }

        # 8. 恢复调用链
        self.call_chain.pop()

        return result

    def _detect_loop_pattern(self, target_agent: AgentType) -> Dict[str, Any]:
        """
        检测循环调用模式

        检测策略：
        1. 简单循环: A → B → A
        2. 重复模式: A → B → C → A → B → C
        3. 长循环: A → B → C → D → E → A

        Returns:
            {
                "has_loop": bool,
                "pattern": str (如果检测到循环)
            }
        """
        # 检查简单循环：目标agent已经在调用链中
        if target_agent in self.call_chain:
            # 找到目标agent在调用链中的位置
            first_index = self.call_chain.index(target_agent)
            loop_sequence = self.call_chain[first_index:] + [target_agent]

            # 检查是否是立即循环（A → B → A）
            if len(loop_sequence) == 2:
                return {
                    "has_loop": True,
                    "pattern": f"Immediate loop: {' → '.join([a.value for a in loop_sequence])}"
                }

            # 检查是否是短循环（A → B → C → A）
            if len(loop_sequence) <= 4:
                return {
                    "has_loop": True,
                    "pattern": f"Short loop: {' → '.join([a.value for a in loop_sequence])}"
                }

            # 长循环警告
            return {
                "has_loop": True,
                "pattern": f"Long loop detected: {' → '.join([a.value for a in loop_sequence])}"
            }

        # 检查重复模式（A → B → A → B）
        if len(self.call_chain) >= 4:
            # 检查最后4个调用是否是交替模式
            recent = self.call_chain[-4:]
            if len(recent) == 4:
                if recent[0] == recent[2] and recent[1] == target_agent:
                    return {
                        "has_loop": True,
                        "pattern": f"Alternating pattern: {recent[0].value} ↔ {recent[1].value}"
                    }

        # 检查重复的三元组模式（A → B → C → A → B → C）
        if len(self.call_chain) >= 6:
            recent = self.call_chain[-6:]
            pattern1 = recent[:3]
            pattern2 = recent[3:] + [target_agent]

            if pattern1 == pattern2:
                return {
                    "has_loop": True,
                    "pattern": f"Repeating pattern: {' → '.join([a.value for a in pattern1])}"
                }

        # 没有检测到循环
        return {"has_loop": False, "pattern": ""}

    def get_call_chain_info(self) -> Dict[str, Any]:
        """
        获取调用链信息（用于调试）

        Returns:
            {
                "current_chain": List[str],
                "depth": int,
                "agent_counts": Dict[str, int],
                "call_history": List[Dict]
            }
        """
        agent_counts = {}
        for agent in self.call_chain:
            agent_counts[agent.value] = agent_counts.get(agent.value, 0) + 1

        return {
            "current_chain": [a.value for a in self.call_chain],
            "depth": len(self.call_chain),
            "agent_counts": agent_counts,
            "call_history": self.call_history[-10:]  # 最近10次调用
        }

    async def _route_to_agent(
        self,
        target_agent: AgentType,
        capability: str,
        **kwargs
    ) -> Dict[str, Any]:
        """路由到具体的agent实现"""

        # ========== DataExplorer Agent ==========
        if target_agent == AgentType.DATA_EXPLORER:
            return await self._execute_data_explorer(capability, **kwargs)

        # ========== Debugger Agent ==========
        elif target_agent == AgentType.DEBUGGER:
            return await self._execute_debugger(capability, **kwargs)

        # ========== DataPrep Agent ==========
        elif target_agent == AgentType.DATA_PREP:
            return await self._execute_data_prep(capability, **kwargs)

        # ========== Analyst Agent ==========
        elif target_agent == AgentType.ANALYST:
            return await self._execute_analyst(capability, **kwargs)

        # ========== Reporter Agent ==========
        elif target_agent == AgentType.REPORTER:
            return await self._execute_reporter(capability, **kwargs)

        else:
            raise ValueError(f"Unknown agent type: {target_agent}")

    # ==================== DataExplorer Agent 实现 ====================

    async def _execute_data_explorer(self, capability: str, **kwargs) -> Dict[str, Any]:
        """执行DataExplorer的能力"""

        if capability == "analyze_schema":
            # 分析数据schema
            error_msg = kwargs.get("error_msg", "")
            file_path = kwargs.get("file_path", "")

            # 使用已有的探索逻辑
            loading_guide = await _run_active_exploration(
                self.sandbox,
                error_msg or "Schema analysis request",
                self.base_context,
                kwargs.get("chat_summary", "")
            )

            return {
                "schema_info": self._parse_loading_guide(loading_guide),
                "loading_guide": loading_guide,
                "file_structure": self.get_file_tree_context()
            }

        elif capability == "discover_files":
            # 发现文件
            pattern = kwargs.get("pattern", "*")
            files = self._discover_files(pattern)
            file_types = self._classify_files(files)

            return {
                "files": files,
                "file_types": file_types
            }

        elif capability == "detect_encoding":
            # 检测编码
            file_path = kwargs.get("file_path")
            if not file_path:
                raise ValueError("file_path is required for encoding detection")

            encoding = self._detect_file_encoding(file_path)
            return {
                "encoding": encoding,
                "confidence": 0.9
            }

        else:
            raise ValueError(f"Unknown DataExplorer capability: {capability}")

    # ==================== Debugger Agent 实现 ====================

    async def _execute_debugger(self, capability: str, **kwargs) -> Dict[str, Any]:
        """执行Debugger的能力"""

        if capability == "fix_code_error":
            # 修复代码错误
            code = kwargs.get("code")
            error_msg = kwargs.get("error_msg")
            context = kwargs.get("context", "")

            # 使用LLM修复代码
            llm = await get_llm()
            fix_prompt = self._create_fix_prompt(code, error_msg, context)

            try:
                res_model = await llm.call_with_json(fix_prompt, output_model=CodeResponse)
                fixed_code = res_model.code.strip()

                return {
                    "fixed_code": fixed_code,
                    "explanation": res_model.thought
                }
            except Exception as e:
                logger.error(f"Debugger failed: {e}")
                raise

        elif capability == "review_code":
            # 代码审查
            code = kwargs.get("code")
            llm = await get_llm()
            review_prompt = f"""Please review the following code:

```python
{code}
```

Provide feedback on:
1. Correctness
2. Performance
3. Best practices
4. Potential improvements

Respond in JSON with 'thought' and 'response' fields."""

            try:
                res_model = await llm.call_with_json(review_prompt, output_model=ChatResponse)
                return {
                    "review_result": res_model.response,
                    "suggestions": res_model.thought.split("\n") if res_model.thought else []
                }
            except Exception as e:
                logger.error(f"Code review failed: {e}")
                raise

        elif capability == "optimize_performance":
            # 性能优化
            code = kwargs.get("code")
            llm = await get_llm()
            optimize_prompt = f"""Optimize the following code for better performance:

```python
{code}
```

Identify performance bottlenecks and provide an optimized version.
Respond in JSON with 'thought' and 'code' fields."""

            try:
                res_model = await llm.call_with_json(optimize_prompt, output_model=CodeResponse)
                return {
                    "optimized_code": res_model.code.strip(),
                    "improvements": res_model.thought.split("\n") if res_model.thought else []
                }
            except Exception as e:
                logger.error(f"Performance optimization failed: {e}")
                raise

        else:
            raise ValueError(f"Unknown Debugger capability: {capability}")

    # ==================== DataPrep Agent 实现 ====================

    async def _execute_data_prep(self, capability: str, **kwargs) -> Dict[str, Any]:
        """执行DataPrep的能力"""

        if capability == "check_prepared_data":
            # 检查数据准备状态
            error = _verify_prepared_data(self.sandbox_dir)
            is_prepared = (error is None)

            prepared_files = []
            if is_prepared:
                prep_dir = self.sandbox_dir / "prepared_data"
                prep_dir_new = self.sandbox_dir / "prepared"

                if prep_dir.exists():
                    prepared_files.extend([str(f) for f in prep_dir.glob("**/*") if f.is_file()])
                if prep_dir_new.exists():
                    prepared_files.extend([str(f) for f in prep_dir_new.glob("**/*") if f.is_file()])

            # 读取manifest
            manifest = {}
            manifest_file = self.sandbox_dir / "manifest.json"
            if manifest_file.exists():
                try:
                    manifest = json.loads(manifest_file.read_text())
                except:
                    pass

            return {
                "is_prepared": is_prepared,
                "prepared_files": prepared_files,
                "manifest": manifest,
                "error": error
            }

        elif capability == "clean_data":
            # 数据清洗
            source_files = kwargs.get("source_files", [])
            # 返回需要执行的清洗代码（由调用者执行）
            return {
                "cleaned_files": [],
                "cleaning_report": "Data cleaning not yet implemented. Use manual code."
            }

        elif capability == "transform_data":
            # 数据转换
            return {
                "transformed_files": [],
                "transform_report": "Data transformation not yet implemented. Use manual code."
            }

        elif capability == "split_data":
            # 数据分割
            return {
                "train_file": "",
                "test_file": "",
                "answer_file": "",
                "split_report": "Data splitting not yet implemented. Use manual code."
            }

        else:
            raise ValueError(f"Unknown DataPrep capability: {capability}")

    # ==================== Analyst Agent 实现 ====================

    async def _execute_analyst(self, capability: str, **kwargs) -> Dict[str, Any]:
        """执行Analyst的能力"""

        if capability == "generate_statistics":
            # 生成统计（需要执行代码）
            data_source = kwargs.get("data_source", "")
            code = f"""import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('{data_source}')

# Generate statistics
print("Shape:", df.shape)
print("\\nColumns:", df.columns.tolist())
print("\\nData Types:\\n", df.dtypes)
print("\\nBasic Statistics:\\n", df.describe())
print("\\nMissing Values:\\n", df.isnull().sum())
print("\\nUnique Values:\\n", df.nunique())
"""

            result = self.sandbox.run_script(code)

            return {
                "statistics": {
                    "stdout": result.stdout,
                    "stderr": result.stderr
                },
                "summary_text": result.stdout,
                "success": result.success
            }

        elif capability == "create_visualization":
            # 创建可视化
            data_source = kwargs.get("data_source", "")
            viz_type = kwargs.get("viz_type", "scatter")

            code = f"""import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('{data_source}')

# Create visualization
if '{viz_type}' == 'scatter':
    df.plot.scatter(x=df.columns[0], y=df.columns[1])
elif '{viz_type}' == 'hist':
    df[df.columns[0]].hist()
else:
    df.plot()

plt.tight_layout()
plt.savefig('analyst_viz.png', dpi=100)
print("Visualization saved to analyst_viz.png")
"""

            result = self.sandbox.run_script(code)

            return {
                "image_paths": ["analyst_viz.png"] if result.success else [],
                "insights": [result.stdout] if result.success else [],
                "success": result.success
            }

        elif capability == "analyze_correlations":
            # 相关性分析
            data_source = kwargs.get("data_source", "")

            code = f"""import pandas as pd

df = pd.read_csv('{data_source}')

# Select only numeric columns
numeric_df = df.select_dtypes(include=[np.number])

# Calculate correlation
corr = numeric_df.corr()
print("Correlation Matrix:\\n", corr)

# Key correlations
print("\\nKey Correlations:")
for col in corr.columns:
    top_corr = corr[col].abs().sort_values(ascending=False).head(3)
    print(f"\\n{{col}}: {{top_corr.to_dict()}}")
"""

            result = self.sandbox.run_script(code)

            return {
                "correlation_matrix": result.stdout,
                "key_correlations": [],
                "success": result.success
            }

        elif capability == "compare_datasets":
            # 比较数据集
            datasets = kwargs.get("datasets", [])

            if len(datasets) < 2:
                return {"comparison_report": "Need at least 2 datasets to compare", "differences": []}

            # 生成比较代码
            code = f"""import pandas as pd
import sys

df1 = pd.read_csv('{datasets[0]}')
df2 = pd.read_csv('{datasets[1]}')

print("Dataset 1 shape:", df1.shape)
print("Dataset 2 shape:", df2.shape)

print("\\nColumns in both:", set(df1.columns) & set(df2.columns))
print("Columns only in df1:", set(df1.columns) - set(df2.columns))
print("Columns only in df2:", set(df2.columns) - set(df1.columns))

# Compare shapes if columns match
if set(df1.columns) == set(df2.columns):
    print("\\nSame columns, comparing sizes...")
    print(f"df1 size: {{len(df1)}}")
    print(f"df2 size: {{len(df2)}}")
"""

            result = self.sandbox.run_script(code)

            return {
                "comparison_report": result.stdout,
                "differences": result.stdout.split("\n"),
                "success": result.success
            }

        else:
            raise ValueError(f"Unknown Analyst capability: {capability}")

    # ==================== Reporter Agent 实现 ====================

    async def _execute_reporter(self, capability: str, **kwargs) -> Dict[str, Any]:
        """执行Reporter的能力"""

        if capability == "summarize_analysis":
            # 总结分析结果
            analysis_results = kwargs.get("analysis_results", {})
            focus = kwargs.get("focus", "")

            llm = await get_llm()
            summary_prompt = f"""Please summarize the following analysis results:

{json.dumps(analysis_results, indent=2, ensure_ascii=False)}

Focus: {focus if focus else "Provide a comprehensive summary"}

Respond in JSON with 'thought' and 'response' fields."""

            try:
                res_model = await llm.call_with_json(summary_prompt, output_model=ChatResponse)
                return {
                    "summary": res_model.response,
                    "key_findings": res_model.thought.split("\n") if res_model.thought else []
                }
            except Exception as e:
                logger.error(f"Summary failed: {e}")
                raise

        elif capability == "generate_report":
            # 生成报告
            content = kwargs.get("content", {})
            format_type = kwargs.get("format", "markdown")

            report_content = json.dumps(content, indent=2, ensure_ascii=False)

            if format_type == "markdown":
                # 转换为markdown格式
                report_content = f"# Analysis Report\n\n{report_content}"

            return {
                "report_path": "report.txt",
                "report_content": report_content
            }

        elif capability == "format_insights":
            # 格式化洞察
            insights = kwargs.get("insights", [])
            format_style = kwargs.get("format", "bullet")

            if format_style == "bullet":
                formatted = "\n".join([f"• {insight}" for insight in insights])
            else:
                formatted = "\n".join(insights)

            return {
                "formatted_text": formatted,
                "bullet_points": insights
            }

        else:
            raise ValueError(f"Unknown Reporter capability: {capability}")

    # ==================== 辅助方法 ====================

    def get_file_tree_context(self) -> str:
        """获取文件树结构"""
        try:
            import os
            result = ["## Current Workspace File Structure\n"]

            for root, dirs, files in os.walk(self.sandbox_dir):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                level = root.replace(str(self.sandbox_dir), '').count(os.sep)
                indent = ' ' * 2 * level
                result.append(f'{indent}{os.path.basename(root)}/')

                subindent = ' ' * 2 * (level + 1)
                for file in sorted(files):
                    if not file.startswith('.'):
                        result.append(f'{subindent}{file}')

            return '\n'.join(result)
        except Exception as e:
            logger.error(f"Failed to get file tree: {e}")
            return "Unable to retrieve file structure"

    def get_data_schema_summary(self) -> str:
        """获取数据schema摘要"""
        try:
            import pandas as pd
            result = ["\n## Available Data Files and Schema\n"]

            # 检查prepared和raw数据
            dirs_to_check = [
                self.sandbox_dir / "prepared" / "public",
                self.sandbox_dir / "prepared" / "private",
                self.sandbox_dir / "raw"
            ]

            for dir_path in dirs_to_check:
                if dir_path.exists():
                    for csv_file in dir_path.glob("*.csv"):
                        rel_path = csv_file.relative_to(self.sandbox_dir)
                        result.append(f"\n### {rel_path}")

                        try:
                            df = pd.read_csv(csv_file, nrows=1)
                            result.append(f"**Columns**: {', '.join(df.columns.tolist())}")
                            result.append(f"**Shape**: (rows, {len(df.columns)} columns)")
                            result.append(f"**Dtypes**:\n{df.dtypes.to_string()}")
                        except Exception as e:
                            result.append(f"**Error**: {e}")

            return '\n'.join(result)
        except Exception as e:
            logger.error(f"Failed to get schema summary: {e}")
            return f"Unable to retrieve schema: {e}"

    def _discover_files(self, pattern: str = "*") -> List[str]:
        """发现文件"""
        import os
        files = []
        for root, dirs, filenames in os.walk(self.sandbox_dir):
            for filename in filenames:
                if filename.endswith(pattern) or pattern == "*":
                    files.append(str(Path(root) / filename))
        return files

    def _classify_files(self, files: List[str]) -> Dict[str, int]:
        """分类文件"""
        from collections import Counter
        extensions = [Path(f).suffix.lower() for f in files]
        return dict(Counter(extensions))

    def _detect_file_encoding(self, file_path: str) -> str:
        """检测文件编码"""
        try:
            # 简单的编码检测
            with open(file_path, 'rb') as f:
                raw = f.read(10000)  # 读取前10KB

            # 尝试常见编码
            for encoding in ['utf-8', 'gbk', 'gb2312', 'latin-1']:
                try:
                    raw.decode(encoding)
                    return encoding
                except:
                    continue

            return "unknown"
        except Exception as e:
            logger.error(f"Failed to detect encoding: {e}")
            return "unknown"

    def _parse_loading_guide(self, guide: str) -> Dict[str, Any]:
        """解析加载指南"""
        return {
            "raw_guide": guide,
            "files": [],
            "schemas": {}
        }

    def _create_fix_prompt(self, code: str, error_msg: str, context: str) -> str:
        """创建修复prompt"""
        prompt = f"""Fix the following Python code:

## Error Message
{error_msg}

## Context
{context}

## Failed Code
```python
{code}
```

Provide the fixed code in JSON format with 'thought' and 'code' fields.
The 'code' field should contain the COMPLETE fixed script.
"""
        return prompt


# ==================== 便捷函数 ====================

async def get_enhanced_debug_context(
    dispatcher: AgentDispatcher,
    error_msg: str,
    chat_summary: str = ""
) -> str:
    """
    为debug agent构建增强上下文

    这个函数展示agent互相调用的实际应用：
    1. 调用DataExplorer获取文件结构
    2. 调用DataExplorer获取schema
    3. 如果有数据错误，调用DataExplorer生成加载指南
    """
    context_parts = []

    # 1. 获取文件树
    file_tree = dispatcher.get_file_tree_context()
    context_parts.append(file_tree)

    # 2. 获取数据schema
    schema_summary = dispatcher.get_data_schema_summary()
    context_parts.append(schema_summary)

    # 3. 如果是数据错误，调用DataExplorer agent
    data_error_keywords = [
        "FileNotFoundError", "No such file", "encoding",
        "column", "dtype", "KeyError"
    ]

    if any(kw in error_msg for kw in data_error_keywords):
        logger.info("🔍 数据相关问题 - 调用 DataExplorer agent")

        # 使用agent调用机制
        result = await dispatcher.call(
            target_agent=AgentType.DATA_EXPLORER,
            capability="analyze_schema",
            error_msg=error_msg,
            chat_summary=chat_summary
        )

        if result.get("success"):
            context_parts.append("\n## Data Loading Guide\n")
            context_parts.append(result.get("loading_guide", ""))

    return '\n'.join(context_parts)
