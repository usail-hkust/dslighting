"""dslighting.tools.dsflow.prompts.optimizer_prompt

Prompt builder used to mutate workflows during DSFlow optimization.
"""

from __future__ import annotations


def build_optimizer_prompt(
    *,
    experience: str,
    parent_score: float,
    parent_code: str,
    operator_catalog: str,
    task_hint: str,
) -> str:
    task_hint = (task_hint or "").strip()
    if len(task_hint) > 2000:
        task_hint = task_hint[:2000] + "\n...[truncated]..."

    return (
        "You are optimizing a Python DSLighting workflow for data-science competitions.\n\n"
        "# GOAL\n"
        "1. Improve benchmark score\n"
        "2. Enhance generalization across different tasks/datasets\n\n"
        "# APPROACH (choose 1-2 changes)\n"
        "1. Create new operators for reusable logic\n"
        "2. Compose operators into higher-level operators\n"
        "3. Optimize workflow control flow (if/else, loops, parallel execution, validation gates)\n\n"
        "# OUTPUT FORMAT\n"
        "Return a JSON object with fields: thought, modification, graph, operators.\n"
        "Set `graph` to a complete runnable `class Workflow(BaseWorkflow)` with `async def solve(...)`.\n"
        "Do NOT hardcode filenames. Write outputs to `output_path.name` in CWD.\n\n"
        "# OPERATOR RETURN TYPES\n"
        "- Review -> ReviewResponse (is_correct: bool, feedback: str)\n"
        "- ExecutePython -> ExecutionResult (success, stdout, stderr)\n"
        "- Prefer typed outputs for new operators when possible\n\n"
        "# EXAMPLES\n\n"
        "## 1. STANDARD OPERATOR TEMPLATE\n"
        "```python\n"
        "class MyOperatorResponse(BaseModel):\n"
        '    summary: str = Field(description="Short summary")\n'
        '    actions: list[str] = Field(description="Next steps")\n\n'
        "class MyOperator(Operator):\n"
        '    """\n'
        "    Description.\n"
        "    Inputs:\n"
        "    - input1: str - Description\n"
        "    Outputs:\n"
        "    - MyOperatorResponse with summary and actions\n"
        '    """\n'
        "    async def __call__(self, input1: str) -> MyOperatorResponse:\n"
        '        prompt = f"Process {input1}"\n'
        "        return await self.llm_service.call_with_json(prompt, output_model=MyOperatorResponse)\n"
        "```\n\n"
        "## 2. Compose Operators (Higher-Level)\n"
        "```python\n"
        "class ExplorationReport(BaseModel):\n"
        '    summary: str = Field(description="High-level summary")\n'
        '    insights: list[str] = Field(description="Key insights")\n\n'
        "class DataExplorationPipeline(Operator):\n"
        '    """\n'
        "    Composite operator: inspect → plan → code → execute.\n"
        "    Inputs:\n"
        "    - problem: str - Problem description\n"
        "    - io_instructions: str - I/O requirements\n"
        "    Outputs:\n"
        "    - ExplorationReport\n"
        '    """\n'
        "    def __init__(self, llm_service, sandbox_service, operators: dict):\n"
        '        super().__init__(name="DataExplorationPipeline")\n'
        "        self.llm_service = llm_service\n"
        "        self._sandbox = sandbox_service\n"
        "        self._operators = operators\n\n"
        "    async def __call__(self, problem: str, io_instructions: str) -> ExplorationReport:\n"
        '        schema = await self._operators["DSDataInspect"]()\n'
        '        plan = await self._operators["DSProblemAnalysis"](problem, io_instructions)\n'
        '        code = await self._operators["DSCodeGen"](problem, io_instructions, plan)\n'
        '        result = await self._operators["ExecutePython"](code)\n'
        "        if not result.success:\n"
        '            code = await self._operators["DSCodeRefine"](\n'
        "                problem, io_instructions, plan, code, result.stderr\n"
        "            )\n"
        '            result = await self._operators["ExecutePython"](code)\n'
        "        report = await self.llm_service.call_with_json(\n"
        '            f"Summarize insights from:\\n{result.stdout}",\n'
        "            output_model=ExplorationReport,\n"
        "        )\n"
        "        return report\n"
        "```\n\n"
        "## 3. Optimize Workflow Control Flow\n"
        "```python\n"
        "class Workflow(BaseWorkflow):\n"
        "    async def solve(self, description, io_instructions, data_dir, output_path):\n"
        "        # Add validation gate\n"
        "        schema = await self.operators['DSDataInspect']()\n"
        "        if 'required_column' not in schema:\n"
        "            return baseline_model()  # Fallback\n"
        "        \n"
        "        # Review-Revise loop\n"
        "        code = await self.operators['DSCodeGen'](description, io_instructions)\n"
        "        for _ in range(3):  # Retry logic\n"
        "            review = await self.operators['Review'](description, code)\n"
        "            if review.is_correct:\n"
        "                break\n"
        "            code = await self.operators['Revise'](description, code, review.feedback)\n"
        "        \n"
        "        # Execute with error handling\n"
        "        result = await self.operators['ExecutePython'](code)\n"
        "        if not result.success:\n"
        "            code = await self.operators['DSCodeRefine'](..., result.stderr)\n"
        "            result = await self.operators['ExecutePython'](code)\n"
        "```\n\n"
        "# ADVANCED OPERATOR PATTERNS\n"
        "## SERVICE-DEPENDENT OPERATOR\n"
        "```python\n"
        "class ExecutePythonSafe(Operator):\n"
        '    """Runs code in sandbox safely.\n\n'
        "    Inputs:\n"
        "    - code: str\n\n"
        "    Outputs:\n"
        "    - ExecutionResult\n"
        '    """\n'
        "    def __init__(self, sandbox_service: SandboxService):\n"
        '        super().__init__(name="ExecutePythonSafe")\n'
        "        self._sandbox = sandbox_service\n\n"
        "    async def __call__(self, code: str) -> ExecutionResult:\n"
        "        return await self._sandbox.run_script(code)\n"
        "```\n\n"
        "## COMPOSITE OPERATOR\n"
        "Combine existing operators to avoid duplicated logic and improve reuse.\n\n"
        "## WORKFLOW-LEVEL OPERATOR COMPOSITION\n"
        "- Generate → Review → Revise\n"
        "- Plan → Code → Execute → Debug\n\n"
        "# IMPORTANT NOTES\n"
        "- Review operator returns ReviewResponse(is_correct: bool, feedback: str), NOT string\n"
        "- Operator code must define `class <Name>(Operator)` (inherit from Operator)\n"
        "- Operator __init__ required params can ONLY be: llm_service, sandbox_service, workspace, operators, data_perception\n"
        "- Composite operators should accept `operators` in __init__ and call self._operators[...]\n"
        "- Avoid hardcoding columns/files; infer from sample_submission/train schema\n"
        "- Add fallbacks for missing files/columns\n"
        "- Avoid backslashes inside f-string expressions; precompute escaped strings first\n"
        "- Avoid f\"...{'\\n'.join(...)}...\"; compute joined text before the f-string (or use chr(10))\n"
        "- New operators need: docstring with Inputs/Outputs, async __call__()\n\n"
        f"# TASK HINT (for designing operators; do not hardcode specifics)\n{task_hint}\n\n"
        f"# AVAILABLE OPERATORS\n{operator_catalog}\n\n"
        f"# EXPERIENCE LOG\n{experience}\n\n"
        f"# PARENT SCORE\n{parent_score:.4f}\n\n"
        "# PARENT CODE\n"
        f"```python\n{parent_code}\n```\n"
    )


def build_workflow_repair_prompt(
    *,
    error_message: str,
    invalid_code: str,
    operator_catalog: str,
) -> str:
    """
    Build a focused prompt to repair invalid workflow code without changing intent.
    """
    error_message = (error_message or "").strip()
    invalid_code = (invalid_code or "").strip()

    return (
        "You are repairing a generated DSLighting workflow so it can be imported.\n\n"
        "# GOAL\n"
        "Fix syntax/escaping issues only. Preserve the workflow's logic and behavior.\n\n"
        "# OUTPUT FORMAT\n"
        "Return a JSON object with fields: thought, modification, graph, operators.\n"
        "Set `graph` to a complete runnable `class Workflow(BaseWorkflow)` with `async def solve(...)`.\n"
        "Do NOT hardcode filenames. Write outputs to `output_path.name` in CWD.\n\n"
        "# IMPORTANT NOTES\n"
        "- Avoid backslashes inside f-string expressions\n"
        "- Avoid f\"...{'\\n'.join(...)}...\"; precompute joined text or use chr(10)\n"
        "- Keep the operator usage unchanged unless required to fix syntax\n\n"
        f"# ERROR\n{error_message}\n\n"
        "# INVALID WORKFLOW CODE\n"
        f"```python\n{invalid_code}\n```\n\n"
        f"# AVAILABLE OPERATORS\n{operator_catalog}\n"
    )


def build_operator_repair_prompt(
    *,
    error_message: str,
    operator_spec: str,
    operator_catalog: str,
    existing_names: str,
) -> str:
    """
    Build a focused prompt to repair a single operator definition.
    """
    error_message = (error_message or "").strip()
    operator_spec = (operator_spec or "").strip()
    existing_names = (existing_names or "").strip()

    return (
        "You are repairing a single DSLighting operator so it can be registered and instantiated.\n\n"
        "# GOAL\n"
        "Fix syntax/validation/initialization issues only. Preserve the operator's intent.\n\n"
        "# OUTPUT FORMAT\n"
        "Return a JSON object with fields: name, description, inputs, outputs, triggers, task_types, code.\n"
        "The code must define `class <name>(Operator)` with `async def __call__(...)`.\n\n"
        "# IMPORTANT NOTES\n"
        "- __init__ required params can ONLY be: llm_service, sandbox_service, workspace, operators, data_perception\n"
        "- Include a class docstring with Inputs: and Outputs:\n"
        "- Avoid backslashes inside f-string expressions\n"
        "- Avoid f\"...{'\\n'.join(...)}...\"; precompute joined text or use chr(10)\n"
        "- Do NOT use existing operator names\n\n"
        f"# ERROR\n{error_message}\n\n"
        f"# EXISTING OPERATOR NAMES\n{existing_names}\n\n"
        "# ORIGINAL OPERATOR SPEC\n"
        f"{operator_spec}\n\n"
        f"# AVAILABLE OPERATORS\n{operator_catalog}\n"
    )
