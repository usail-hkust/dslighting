# 如何在 DSLighting 中新增 Operator 和 Prompt

## 📋 目录
1. [创建自定义 Operator](#1-创建自定义-operator)
2. [创建自定义 Prompts](#2-创建自定义-prompts)
3. [在自定义 Agent 中使用](#3-在自定义-agent-中使用)
4. [注册到系统（可选）](#4-注册到系统可选)

---

## 1. 创建自定义 Operator

### 1.1 Operator 基类

所有 Operator 都继承自 `dsat.operators.base.Operator`：

```python
# dsat/operators/base.py

from abc import ABC, abstractmethod
from typing import Optional, Any

class Operator(ABC):
    """所有 Operator 的基类"""

    def __init__(self,
                 llm_service: Optional["LLMService"] = None,
                 name: Optional[str] = None):
        self.llm_service = llm_service
        self.name = name

    @abstractmethod
    async def __call__(self, *args, **kwargs) -> Any:
        """Operator 的主要方法"""
        raise NotImplementedError
```

### 1.2 创建简单 Operator（不使用 LLM）

```python
# dslighting/operators/custom_ops.py

from dsat.operators.base import Operator
from pathlib import Path

class FileReadOperator(Operator):
    """读取文件内容的 Operator"""

    def __init__(self, base_path: str = "."):
        super().__init__(name="file_read")
        self.base_path = Path(base_path)

    async def __call__(self, filename: str) -> str:
        """读取文件"""
        file_path = self.base_path / filename

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        return file_path.read_text(encoding="utf-8")


class DirectoryListOperator(Operator):
    """列出目录内容的 Operator"""

    def __init__(self):
        super().__init__(name="directory_list")

    async def __call__(self, path: str, pattern: str = "*") -> list:
        """列出目录"""
        from pathlib import Path

        target_path = Path(path)
        if not target_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")

        if target_path.is_file():
            return [str(target_path)]

        # 列出文件
        files = list(target_path.glob(pattern))
        return [str(f) for f in files]
```

### 1.3 创建 LLM Operator（使用 LLM）

```python
# dslighting/operators/llm_ops.py

from dsat.operators.base import Operator
from dsat.services.llm import LLMService

class CodeRefactorOperator(Operator):
    """代码重构 Operator - 使用 LLM 改进代码质量"""

    def __init__(self, llm_service: LLMService):
        super().__init__(llm_service=llm_service, name="code_refactor")

    async def __call__(self, code: str, refactoring_goal: str) -> str:
        """重构代码"""

        prompt = f"""
You are a code refactoring expert. Your task is to improve the given code based on the refactoring goal.

Refactoring Goal: {refactoring_goal}

Original Code:
```python
{code}
```

Please provide the refactored code. Return only the code in a ```python``` block.
"""

        # 调用 LLM
        refactored_code = await self.llm_service.call(prompt)

        # 解析代码
        import re
        code_match = re.search(r'```python\n(.*?)```', refactored_code, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()

        return refactored_code


class DocumentationGeneratorOperator(Operator):
    """文档生成 Operator - 使用 LLM 生成代码文档"""

    def __init__(self, llm_service: LLMService):
        super().__init__(llm_service=llm_service, name="doc_generator")

    async def __call__(self, code: str, doc_style: str = "google") -> str:
        """生成文档"""

        prompt = f"""
Generate documentation for the following code using {doc_style} style.

Code:
```python
{code}
```

Provide comprehensive documentation including:
- Class/function purpose
- Parameters
- Returns
- Raises
- Examples

Return the documentation in a code block.
"""

        docs = await self.llm_service.call(prompt)
        return docs
```

### 1.4 创建复杂 Operator（组合多个操作）

```python
# dslighting/operators/advanced_ops.py

from dsat.operators.base import Operator
from dsat.services.llm import LLMService
from dsat.services.sandbox import SandboxService
from pathlib import Path

class TestAndDebugOperator(Operator):
    """测试和调试 Operator - 自动测试和修复代码"""

    def __init__(self,
                 llm_service: LLMService,
                 sandbox_service: SandboxService,
                 max_retries: int = 3):
        super().__init__(
            llm_service=llm_service,
            name="test_and_debug"
        )
        self.sandbox = sandbox_service
        self.max_retries = max_retries

    async def __call__(self,
                       code: str,
                       test_code: str,
                       mode: str = "script") -> dict:
        """
        测试和调试代码

        Returns:
            dict: {
                "success": bool,
                "fixed_code": str,
                "error": str,
                "attempts": int
            }
        """

        for attempt in range(self.max_retries):
            # 执行代码
            result = self.sandbox.run_script(code)

            # 如果成功，尝试测试
            if result.success:
                test_result = self.sandbox.run_script(test_code)

                if test_result.success:
                    return {
                        "success": True,
                        "fixed_code": code,
                        "error": None,
                        "attempts": attempt + 1
                    }

            # 如果失败，使用 LLM 修复
            error_msg = result.stderr if not result.success else test_result.stderr

            fix_prompt = f"""
The following code failed with an error. Please fix it.

Code:
```python
{code}
```

Error:
```
{error_msg}
```

Please provide the fixed code. Return only the code in a ```python``` block.
"""

            fixed_code = await self.llm_service.call(fix_prompt)

            # 解析修复后的代码
            import re
            code_match = re.search(r'```python\n(.*?)```', fixed_code, re.DOTALL)
            if code_match:
                code = code_match.group(1).strip()

        # 如果所有尝试都失败
        return {
            "success": False,
            "fixed_code": code,
            "error": "Max retries exceeded",
            "attempts": self.max_retries
        }
```

---

## 2. 创建自定义 Prompts

### 2.1 Prompt 模板基础

DSAT 使用简单的字符串格式化来创建 prompts：

```python
# dsat/prompts/my_custom_prompts.py

def create_analysis_prompt(task_description: str, data_summary: str, user_goal: str) -> str:
    """创建分析任务的 prompt"""

    prompt = f"""
You are an expert data scientist. Your task is to {task_description}.

## Data Summary
{data_summary}

## User Goal
{user_goal}

## Instructions
1. Analyze the data carefully
2. Identify key patterns and insights
3. Generate appropriate code to achieve the user's goal
4. Ensure your code follows best practices

Please provide your analysis and code in the following format:

```text
## Analysis
[Your analysis here]

## Code
```python
[Your code here]
```
```

    return prompt


def create_optimization_prompt(
    original_code: str,
    performance_metrics: str,
    optimization_target: str
) -> str:
    """创建优化任务的 prompt"""

    prompt = f"""
You are a code optimization expert. Help optimize the following code.

## Original Code
```python
{original_code}
```

## Current Performance
{performance_metrics}

## Optimization Target
{optimization_target}

Please provide optimized code with explanations.

Return your response in the following format:

```text
## Optimization Strategy
[Your strategy here]

## Optimized Code
```python
[Your optimized code here]
```

## Expected Improvement
[Your expected improvement here]
```
"""

    return prompt
```

### 2.2 创建可复用的 Prompt 组件

```python
# dslighting/prompts/components.py

def get_system_role(role: str = "data_scientist") -> str:
    """获取系统角色定义"""

    roles = {
        "data_scientist": "You are an expert data scientist with strong knowledge of machine learning, statistics, and data analysis.",
        "software_engineer": "You are a senior software engineer specializing in Python, algorithms, and code optimization.",
        "ml_researcher": "You are a machine learning researcher with expertise in deep learning, neural networks, and model optimization.",
    }

    return roles.get(role, "You are a helpful AI assistant.")


def get_code_style_guidelines(language: str = "python") -> str:
    """获取代码风格指南"""

    if language == "python":
        return """
Please follow these Python best practices:
- Use type hints where appropriate
- Write docstrings for functions and classes
- Follow PEP 8 style guide
- Use meaningful variable names
- Add comments for complex logic
- Handle errors appropriately
"""
    elif language == "r":
        return """
Please follow these R best practices:
- Use meaningful variable names
- Write functions that do one thing well
- Add comments for complex logic
- Follow standard R style conventions
"""
    else:
        return ""


def build_full_prompt(
    task: str,
    context: str,
    constraints: str = "",
    examples: str = "",
    role: str = "data_scientist",
    language: str = "python"
) -> str:
    """构建完整的 prompt"""

    prompt_parts = []

    # 1. 系统角色
    prompt_parts.append(f"# Role\n{get_system_role(role)}\n")

    # 2. 任务描述
    prompt_parts.append(f"# Task\n{task}\n")

    # 3. 上下文信息
    if context:
        prompt_parts.append(f"# Context\n{context}\n")

    # 4. 约束条件
    if constraints:
        prompt_parts.append(f"# Constraints\n{constraints}\n")

    # 5. 示例
    if examples:
        prompt_parts.append(f"# Examples\n{examples}\n")

    # 6. 代码风格指南
    prompt_parts.append(f"# Code Style\n{get_code_style_guidelines(language)}\n")

    # 7. 输出格式
    prompt_parts.append("""# Output Format
Please provide your response in the following format:

```text
## Analysis
[Your analysis here]

## Approach
[Your approach here]

## Code
```python
[Your code here]
```

## Explanation
[Your explanation here]
```
""")

    return "\n".join(prompt_parts)
```

### 2.3 创建领域特定的 Prompts

```python
# dslighting/prompts/domains.py

class DataSciencePrompts:
    """数据科学领域的 prompts"""

    @staticmethod
    def eda_prompt(data_info: str) -> str:
        """探索性数据分析 prompt"""
        return f"""
Perform exploratory data analysis (EDA) on the following dataset:

{data_info}

Please include:
1. Data Overview (shape, types, missing values)
2. Statistical Summary
3. Visualizations (describe what you would create)
4. Key Insights
5. Recommendations for further analysis

Provide Python code for the EDA process.
"""

    @staticmethod
    def feature_engineering_prompt(
        data_description: str,
        target_variable: str
    ) -> str:
        """特征工程 prompt"""
        return f"""
Perform feature engineering for the following dataset:

Data Description:
{data_description}

Target Variable: {target_variable}

Please:
1. Analyze existing features
2. Create new features through transformations
3. Encode categorical variables appropriately
4. Handle missing values
5. Scale/normalize features if needed

Provide Python code with clear explanations.
"""

    @staticmethod
    def model_selection_prompt(
        task_type: str,
        data_description: str
    ) -> str:
        """模型选择 prompt"""
        return f"""
Recommend the best machine learning approach for:

Task Type: {task_type}
Data Description:
{data_description}

Please recommend:
1. Top 3 suitable models with justifications
2. Pros and cons of each model
3. Hyperparameters to tune
4. Evaluation metrics to use

Provide clear reasoning for your recommendations.
"""


class CodeGenerationPrompts:
    """代码生成领域的 prompts"""

    @staticmethod
    def unit_test_prompt(function_code: str) -> str:
        """单元测试生成 prompt"""
        return f"""
Generate comprehensive unit tests for the following function:

```python
{function_code}
```

Please include:
1. Normal cases
2. Edge cases
3. Error handling
4. Mock setup if needed
5. Test data generation

Use pytest framework.
"""

    @staticmethod
    def api_integration_prompt(api_spec: str) -> str:
        """API 集成 prompt"""
        return f"""
Create Python code to integrate with the following API:

API Specification:
{api_spec}

Please provide:
1. API client implementation
2. Error handling
3. Rate limiting considerations
4. Example usage
"""
```

---

## 3. 在自定义 Agent 中使用

### 3.1 使用自定义 Operator

```python
# /Users/liufan/Applications/Github/dslighting/dsat/workflows/manual/my_enhanced_agent.py

from dsat.workflows.base import DSATWorkflow
from dslighting.operator.custom_ops import FileReadOperator, DirectoryListOperator
from dslighting.operators.llm_ops import CodeRefactorOperator, DocumentationGeneratorOperator

class MyEnhancedAgent(DSATWorkflow):
    """使用自定义 Operator 的 Agent"""

    def __init__(self, operators, services, agent_config):
        super().__init__(operators, services, agent_config)

        # DSAT 标准操作器
        self.generate_op = operators["generate"]
        self.execute_op = operators["execute"]
        self.review_op = operators["review"]

        # 自定义操作器
        self.file_read_op = operators.get("file_read")
        self.directory_list_op = operators.get("directory_list")
        self.code_refactor_op = operators.get("code_refactor")
        self.doc_generator_op = operators.get("doc_generator")

    async def solve(self, description, io_instructions, data_dir, output_path):
        """使用自定义 Operator"""

        # 1. 列出数据目录
        if self.directory_list_op:
            files = await self.directory_list_op(path=str(data_dir), pattern="*.csv")
            print(f"Found files: {files}")

        # 2. 读取参考文件
        if self.file_read_op:
            try:
                reference = await self.file_read_op("reference_solution.py")
                print(f"Reference solution loaded")
            except:
                reference = None

        # 3. 生成初始代码
        from dslighting.prompts.domains import DataSciencePrompts
        prompt = DataSciencePrompts.feature_engineering_prompt(
            data_description="Tabular data with mixed types",
            target_variable="target"
        )

        plan, code = await self.generate_op(system_prompt=prompt)

        # 4. 使用 Code Refactor 改进代码
        if self.code_refactor_op:
            refactored_code = await self.code_refactor_op(
                code=code,
                refactoring_goal="Improve performance and readability"
            )
            code = refactored_code

        # 5. 执行代码
        result = await self.execute_op(code=code, mode="script")

        # 6. 生成文档
        if self.doc_generator_op and result.success:
            docs = await self.doc_generator_op(code=code, doc_style="google")
            print(f"Documentation:\n{docs}")

        # 7. 保存最终代码
        # ...
```

### 3.2 使用自定义 Prompts

```python
from dslighting.prompts.components import build_full_prompt

class MyAgent(DSATWorkflow):
    async def solve(self, description, io_instructions, data_dir, output_path):
        """使用自定义 Prompts"""

        # 构建完整 prompt
        prompt = build_full_prompt(
            task=description,
            context=f"I/O Requirements:\n{io_instructions}",
            constraints="Time limit: 5 minutes\nMemory limit: 4GB",
            examples="",  # 可以添加示例
            role="data_scientist",
            language="python"
        )

        # 使用 prompt 生成代码
        plan, code = await self.generate_op(system_prompt=prompt)

        # 执行...
        result = await self.execute_op(code=code, mode="script")
```

---

## 4. 注册到系统（可选）

### 4.1 注册自定义 Operator

```python
# /Users/liufan/Applications/Github/dslighting/dsat/operators/__init__.py

from .base import Operator
from .llm_basic import GenerateCodeAndPlanOperator, PlanOperator, ReviewOperator
from .code import ExecuteAndTestOperator

# 导入自定义 Operators
from dslighting.operators.custom_ops import FileReadOperator, DirectoryListOperator
from dslighting.operators.llm_ops import CodeRefactorOperator, DocumentationGeneratorOperator

__all__ = [
    "Operator",
    "GenerateCodeAndPlanOperator",
    "PlanOperator",
    "ReviewOperator",
    "ExecuteAndTestOperator",
    # 自定义 Operators
    "FileReadOperator",
    "DirectoryListOperator",
    "CodeRefactorOperator",
    "DocumentationGeneratorOperator",
]
```

### 4.2 在 Factory 中使用自定义 Operator

```python
# /Users/liufan/Applications/Github/dslighting/dsat/workflows/factory.py

class MyEnhancedAgentWorkflowFactory(WorkflowFactory):
    def create_workflow(self, config, benchmark=None):
        # 创建标准服务
        workspace = WorkspaceService(run_name=config.run.name)
        llm_service = LLMService(config=config.llm)
        sandbox_service = SandboxService(workspace=workspace, timeout=config.sandbox.timeout)

        # 创建标准操作器
        operators = {
            "generate": GenerateCodeAndPlanOperator(llm_service=llm_service),
            "execute": ExecuteAndTestOperator(sandbox_service=sandbox_service),
            "review": ReviewOperator(llm_service=llm_service),
        }

        # 添加自定义操作器
        from dslighting.operators.custom_ops import FileReadOperator, DirectoryListOperator
        from dslighting.operators.llm_ops import CodeRefactorOperator

        operators["file_read"] = FileReadOperator(base_path=str(workspace.get_path("sandbox_workdir")))
        operators["directory_list"] = DirectoryListOperator()
        operators["code_refactor"] = CodeRefactorOperator(llm_service=llm_service)

        # 创建服务字典
        services = {
            "llm": llm_service,
            "sandbox": sandbox_service,
            "workspace": workspace,
        }

        # 创建 workflow
        return MyEnhancedAgent(operators, services, config.agent.model_dump())
```

---

## 5. 完整示例

### 5.1 创建自定义 Operator

```python
# /Users/liufan/Applications/Github/dslighting/dslighting/operators/my_operators.py

from dsat.operators.base import Operator
from dsat.services.llm import LLMService
from dsat.services.sandbox import SandboxService
from pathlib import Path
import re

class CodeOptimizerOperator(Operator):
    """代码优化 Operator - 结合静态分析和 LLM"""

    def __init__(self,
                 llm_service: LLMService,
                 sandbox_service: SandboxService):
        super().__init__(
            llm_service=llm_service,
            sandbox_service=sandbox_service,
            name="code_optimizer"
        )
        self.sandbox = sandbox_service

    async def __call__(self,
                       code: str,
                       optimization_type: str = "performance") -> dict:
        """
        优化代码

        Args:
            code: 原始代码
            optimization_type: 优化类型 (performance, readability, security)

        Returns:
            dict: {
                "original_code": str,
                "optimized_code": str,
                "improvements": list,
                "metrics": dict
            }
        """

        # 1. 静态分析（简单示例）
        lines = code.split('\n')
        original_length = len(lines)
        original_complexity = self._calculate_complexity(code)

        # 2. 使用 LLM 优化
        if optimization_type == "performance":
            prompt = f"""
Optimize this code for performance:

```python
{code}
```

Focus on:
- Algorithm efficiency
- Memory usage
- Computational complexity

Return only the optimized code in a ```python``` block.
"""
        elif optimization_type == "readability":
            prompt = f"""
Improve the readability of this code:

```python
{code}
```

Focus on:
- Variable naming
- Code structure
- Comments and documentation
- Following PEP 8

Return only the optimized code in a ```python``` block.
"""
        else:
            prompt = f"""
Review and improve this code:

```python
{code}
```

Return only the improved code in a ```python``` block.
"""

        optimized_code = await self.llm_service.call(prompt)

        # 解析代码
        code_match = re.search(r'```python\n(.*?)```', optimized_code, re.DOTALL)
        if code_match:
            optimized_code = code_match.group(1).strip()
        else:
            optimized_code = optimized_code  # 如果解析失败，使用原始输出

        # 3. 计算改进指标
        new_lines = optimized_code.split('\n')
        new_length = len(new_lines)
        new_complexity = self._calculate_complexity(optimized_code)

        improvements = []
        if new_length < original_length:
            improvements.append(f"Reduced code length by {original_length - new_length} lines")
        if new_complexity < original_complexity:
            improvements.append(f"Reduced complexity from {original_complexity} to {new_complexity}")

        # 4. 测试优化后的代码
        test_result = self.sandbox.run_script(optimized_code)

        return {
            "original_code": code,
            "optimized_code": optimized_code,
            "improvements": improvements,
            "metrics": {
                "original_length": original_length,
                "optimized_length": new_length,
                "original_complexity": original_complexity,
                "optimized_complexity": new_complexity,
                "test_success": test_result.success
            }
        }

    def _calculate_complexity(self, code: str) -> int:
        """简单的复杂度计算（示例）"""
        # 这里只是一个简单的示例
        # 实际应用中可以使用更复杂的算法（如 cyclomatic complexity）
        complexity = 0

        # 计算 if/for/while 语句
        complexity += code.count('if ')
        complexity += code.count('for ')
        complexity += code.count('while ')

        # 计算嵌套层级
        max_nest = 0
        current_nest = 0
        for char in code:
            if char in '{':
                current_nest += 1
                max_nest = max(max_nest, current_nest)
            elif char == '}':
                current_nest -= 1

        complexity += max_nest * 2

        return complexity
```

### 5.2 创建自定义 Prompt 模板

```python
# /Users/liufan/Applications/Github/dslighting/dslighting/prompts/templates.py

class AgentPromptTemplates:
    """Agent Prompt 模板"""

    @staticmethod
    def create_iterative_prompt(
        iteration: int,
        task_description: str,
        previous_attempts: list,
        best_score: float,
        target_score: float
    ) -> str:
        """创建迭代改进的 prompt"""

        previous_summary = "\n\n".join([
            f"Iteration {att['iteration']}: Score {att['score']}\nPlan: {att['plan'][:100]}..."
            for att in previous_attempts[:3]
        ])

        prompt = f"""
You are working on iteration {iteration} of optimizing a solution.

## Task
{task_description}

## Goal
Achieve a score of at least {target_score:.2f}
Current best score: {best_score:.2f}

## Previous Attempts
{previous_summary}

## Instructions
Analyze the previous attempts and propose an improvement strategy. Focus on:
1. What worked well
2. What didn't work
3. What to change in this iteration

Provide your response in the following format:

```text
## Analysis
[Your analysis of previous attempts]

## Improvement Strategy
[Your strategy for this iteration]

## Code
```python
[Your improved code]
```
"""

        return prompt

    @staticmethod
    def create_collaborative_prompt(
        task_description: str,
        agent_specialties: list,
        available_tools: list
    ) -> str:
        """创建多 Agent 协作的 prompt"""

        specialties_str = "\n".join([
            f"- {agent}: {spec}"
            for agent, spec in agent_specialties.items()
        ])

        tools_str = "\n".join([
            f"- {tool}"
            for tool in available_tools
        ])

        prompt = f"""
You are part of a multi-agent team working on:

## Task
{task_description}

## Team Specializations
{specialties_str}

## Available Tools
{tools_str}

Your role is to:
1. Leverage your specialized expertise
2. Use appropriate tools
3. Collaborate effectively with the team
4. Contribute to the overall solution

Provide your contribution in the following format:

```text
## My Analysis
[Your analysis of the task]

## My Contribution
[Your specific contribution - code, analysis, advice]

## Collaboration Notes
[Any notes for team coordination]
```
"""

        return prompt
```

### 5.3 在 Agent 中使用

```python
# /Users/liufan/Applications/Github/dslighting/dsat/workflows/manual/my_ultimate_agent.py

from dsat.workflows.base import DSATWorkflow
from dslighting.operators.my_operators import CodeOptimizerOperator
from dslighting.prompts.templates import AgentPromptTemplates

class MyUltimateAgent(DSATWorkflow):
    """使用自定义 Operator 和 Prompts 的终极 Agent"""

    def __init__(self, operators, services, agent_config):
        super().__init__(operators, services, agent_config)

        # 标准操作器
        self.generate_op = operators["generate"]
        self.execute_op = operators["execute"]
        self.review_op = operators["review"]

        # 自定义操作器
        self.optimizer_op = operators.get("optimizer")

    async def solve(self, description, io_instructions, data_dir, output_path):
        """结合自定义 Operator 和 Prompts"""

        best_score = 0.0
        target_score = 0.95
        previous_attempts = []
        max_iterations = 5

        for iteration in range(max_iterations):
            print(f"\n=== Iteration {iteration + 1} ===")

            # 使用自定义 Prompt 模板
            prompt = AgentPromptTemplates.create_iterative_prompt(
                iteration=iteration + 1,
                task_description=description,
                previous_attempts=previous_attempts,
                best_score=best_score,
                target_score=target_score
            )

            # 生成代码
            plan, code = await self.generate_op(system_prompt=prompt)

            # 使用自定义 Operator 优化代码
            if self.optimizer_op:
                result = await self.optimizer_op(
                    code=code,
                    optimization_type="performance"
                )
                code = result["optimized_code"]
                print(f"Optimization improvements: {result['improvements']}")

            # 执行代码
            exec_result = await self.execute_op(code=code, mode="script")

            # 评分
            if exec_result.success:
                score = self._extract_score(exec_result.stdout)

                if score > best_score:
                    best_score = score
                    print(f"✓ New best score: {score:.4f}")

                # 记录尝试
                previous_attempts.append({
                    "iteration": iteration + 1,
                    "plan": plan,
                    "code": code,
                    "score": score
                })

                if score >= target_score:
                    print(f"🎉 Target score achieved!")
                    break

        print(f"\nFinal score: {best_score:.4f}")

    def _extract_score(self, output: str) -> float:
        """从输出中提取分数"""
        import re
        score_match = re.search(r'Score[:\s]+([0-9.]+)', output)
        if score_match:
            return float(score_match.group(1))
        return 0.0
```

---

## 🎯 总结

### ✅ 创建自定义 Operator

1. **继承 Operator 基类**
2. **实现 `__call__` 方法**
3. **可以注入 LLMService, SandboxService 等**
4. **返回任意类型的结果**

### ✅ 创建自定义 Prompts

1. **使用字符串格式化**
2. **创建可复用的模板**
3. **按领域组织**
4. **支持参数化**

### ✅ 集成到 Agent

1. **在 Factory 中添加自定义 Operator**
2. **在 Agent 中使用自定义 Prompts**
3. **通过 operators 和 services 字典传递**
4. **完全模块化和可扩展**

### 📁 文件组织

```
dslighting/
├── operators/
│   ├── custom_ops.py          # 自定义 Operators
│   ├── llm_ops.py              # LLM Operators
│   └── advanced_ops.py         # 高级 Operators
├── prompts/
│   ├── templates.py            # Prompt 模板
│   ├── components.py           # Prompt 组件
│   └── domains.py              # 领域 Prompts
└── dsat/workflows/manual/
    └── my_agent.py              # 使用自定义 Operator 和 Prompt
```

**现在您可以完全控制 DSLighting 的 Operator 和 Prompts 了！** 🎉
