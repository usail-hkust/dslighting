"""dslighting.tools.dsflow.operators.dynamic_operator

Utilities for importing dynamically generated operator code (from the LLM)
while fixing common issues.
"""

from __future__ import annotations

import ast
import importlib.util
import re
import uuid
from typing import Tuple, Type

from pydantic import BaseModel, Field

from dslighting.core.data.perception import DataPerceptionRuntime
from dslighting.ops.base import Operator
from dslighting.services.llm import LLMService
from dslighting.services.sandbox import SandboxService
from dslighting.services.workspace import WorkspaceService


def fix_operator_imports(code: str) -> str:
    """Fix common import errors in dynamically generated operator code."""
    code = code or ""

    # Compatibility with operators persisted by the standalone DSFlow/DSAT
    # implementation before it was integrated into DSLighting.
    code = code.replace(
        "from dsat.operators.base import Operator",
        "from dslighting.ops.base import Operator",
    )
    code = code.replace(
        "from dsat.services.llm import LLMService",
        "from dslighting.services.llm import LLMService",
    )
    code = code.replace(
        "from dsat.services.sandbox import SandboxService",
        "from dslighting.services.sandbox import SandboxService",
    )
    code = code.replace(
        "from dsat.services.workspace import WorkspaceService",
        "from dslighting.services.workspace import WorkspaceService",
    )

    # Remove incorrect imports that don't exist in dslighting
    incorrect_imports = [
        r"from\s+dslighting\.state\s+import.*\n?",  # dslighting.state doesn't exist
        r"from\s+dslighting\.states\s+import.*\n?",  # should be dslighting.services.states
        r"from\s+dslighting\.memory\s+import.*\n?",  # doesn't exist
        r"from\s+dslighting\.experience\s+import.*\n?",  # should be dslighting.state.search.experience
        r"from\s+dslighting\.history\s+import.*\n?",  # doesn't exist
        r"from\s+dslighting\.context\s+import.*\n?",  # doesn't exist
    ]

    for pattern in incorrect_imports:
        code = re.sub(pattern, "", code)

    # Fix common method name errors
    code = code.replace("llm_service.complete(", "llm_service.call(")
    code = code.replace("llm_service.generate(", "llm_service.call(")
    code = code.replace("llm_service.call_with_string(", "llm_service.call(")
    code = code.replace("sandbox_service.execute_python(", "sandbox_service.run_script(")
    code = re.sub(
        r"(?m)^(\s*)return\s+(self\._sandbox|sandbox_service)\.run_script\(",
        r"\1return await \2.run_script(",
        code,
    )

    return code


def _ensure_operator_base_class(code: str, class_name: str) -> str:
    """
    Ensure the operator class inherits from Operator.

    If the class definition is missing a base list, add (Operator).
    If it has bases but not Operator, append Operator.
    """
    code = code or ""
    if not class_name:
        return code

    pattern = re.compile(
        rf"(class\s+{re.escape(class_name)}\s*)\(([^)]*)\)\s*:",
        re.MULTILINE,
    )
    match = pattern.search(code)
    if match:
        bases = match.group(2).strip()
        base_list = [b.strip() for b in bases.split(",") if b.strip()]
        if any(b == "Operator" or b.endswith(".Operator") for b in base_list):
            return code
        new_bases = ", ".join(base_list + ["Operator"]) if base_list else "Operator"
        start, end = match.span(2)
        return f"{code[:start]}{new_bases}{code[end:]}"

    pattern_no_bases = re.compile(
        rf"(class\s+{re.escape(class_name)}\s*):",
        re.MULTILINE,
    )
    match = pattern_no_bases.search(code)
    if not match:
        return code
    start, end = match.span(1)
    return f"{code[:start]}{match.group(1)}(Operator){code[end:]}"


def _indent_lines(text: str, indent: str) -> str:
    return "\n".join((indent + line if line else line) for line in (text or "").splitlines())


def _normalize_contract_lines(contract: str) -> list[str]:
    text = (contract or "").strip()
    if not text:
        return ["- (not specified)"]
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
    normalized: list[str] = []
    for ln in lines:
        stripped = ln.strip()
        if stripped.startswith(("-", "*")):
            normalized.append(f"- {stripped.lstrip('-* ').strip()}")
        else:
            normalized.append(f"- {stripped}")
    return normalized


def ensure_operator_docstring(
    code: str,
    *,
    class_name: str,
    description: str = "",
    inputs: str = "",
    outputs: str = "",
) -> Tuple[str, bool]:
    """
    Ensure the operator class has a docstring describing Inputs/Outputs.

    Returns (new_code, changed).
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code, False

    class_node: ast.ClassDef | None = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            class_node = node
            break
    if class_node is None:
        return code, False

    inferred_inputs = ""
    inferred_outputs = ""
    if not (inputs or "").strip() or not (outputs or "").strip():
        call_node = None
        for item in class_node.body:
            if isinstance(item, ast.AsyncFunctionDef) and item.name == "__call__":
                call_node = item
                break
        if call_node is not None:
            parts: list[str] = []
            for arg in (call_node.args.args or [])[1:]:
                ann = ""
                if arg.annotation is not None:
                    try:
                        ann = ast.unparse(arg.annotation)
                    except Exception:
                        ann = ""
                parts.append(f"- {arg.arg}{(': ' + ann) if ann else ''}")
            if call_node.args.vararg is not None:
                parts.append(f"- *{call_node.args.vararg.arg}")
            if call_node.args.kwarg is not None:
                parts.append(f"- **{call_node.args.kwarg.arg}")
            inferred_inputs = "\n".join(parts).strip()

            if call_node.returns is not None:
                try:
                    inferred_outputs = ast.unparse(call_node.returns)
                except Exception:
                    inferred_outputs = ""
            inferred_outputs = inferred_outputs.strip()

    effective_inputs = (inputs or "").strip() or inferred_inputs
    effective_outputs = (outputs or "").strip() or inferred_outputs
    if not effective_inputs.strip():
        effective_inputs = "(no inputs)"
    if not effective_outputs.strip():
        effective_outputs = "Any"

    code = code or ""
    desc = (description or "").strip()

    doc_lines: list[str] = []
    if desc:
        doc_lines.append(desc)
        doc_lines.append("")
    doc_lines.append("Inputs:")
    doc_lines.extend(_normalize_contract_lines(effective_inputs))
    doc_lines.append("")
    doc_lines.append("Outputs:")
    doc_lines.extend(_normalize_contract_lines(effective_outputs))

    doc = "\n".join(doc_lines).replace('"""', '\\"""')

    existing_doc = (ast.get_docstring(class_node) or "").strip()
    if existing_doc and "inputs:" in existing_doc.lower() and "outputs:" in existing_doc.lower():
        return code, False

    lines = code.splitlines(keepends=True)
    class_indent = re.match(r"^[ \t]*", lines[class_node.lineno - 1]).group(0)
    body_indent = class_indent + "    "

    doc_lines = doc.splitlines()
    block_lines: list[str] = [f'{body_indent}"""{doc_lines[0] if doc_lines else ""}']
    block_lines.extend(f"{body_indent}{ln}" for ln in doc_lines[1:])
    block_lines.append(f'{body_indent}"""')
    doc_block = "\n".join(block_lines) + "\n"

    # If a docstring exists, it is always the first statement in the class body.
    first_stmt = class_node.body[0] if class_node.body else None
    if (
        first_stmt is not None
        and isinstance(first_stmt, ast.Expr)
        and isinstance(getattr(first_stmt, "value", None), ast.Constant)
        and isinstance(getattr(first_stmt.value, "value", None), str)
        and getattr(first_stmt, "lineno", None) is not None
        and getattr(first_stmt, "end_lineno", None) is not None
    ):
        start = int(first_stmt.lineno) - 1
        end = int(first_stmt.end_lineno) - 1
        lines[start : end + 1] = [doc_block]
        return "".join(lines), True

    # Otherwise insert before the first class body statement.
    insert_line = int(class_node.body[0].lineno) - 1 if class_node.body else int(class_node.lineno)
    lines[insert_line:insert_line] = [doc_block]
    return "".join(lines), True


def validate_operator_source(code: str, *, class_name: str) -> None:
    """
    Validate operator source code before executing it.

    Requirements:
    - Defines `class <class_name>(Operator)` (directly or via attribute reference).
    - Class docstring contains "Inputs:" and "Outputs:".
    - Implements `async def __call__(...)`.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise ValueError(f"Operator code has syntax error: {e}") from e

    allowed_top_level = (
        ast.Import,
        ast.ImportFrom,
        ast.ClassDef,
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.Assign,
        ast.AnnAssign,
        ast.Expr,
    )

    def _is_safe_call(call_node: ast.Call) -> bool:
        func = call_node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            return func.value.id == "logging" and func.attr == "getLogger"
        return False

    def _contains_unsafe_call(expr: ast.AST) -> bool:
        for inner in ast.walk(expr):
            if isinstance(inner, ast.Call) and not _is_safe_call(inner):
                return True
        return False

    for node in tree.body:
        if isinstance(node, ast.Expr):
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                continue  # module docstring
            raise ValueError("Operator code must not execute expressions at module import time.")
        if isinstance(node, ast.Assign):
            if _contains_unsafe_call(node.value):
                raise ValueError(
                    "Operator code must not execute calls at module import time (top-level assignment)."
                )
        if isinstance(node, ast.AnnAssign) and node.value is not None:
            if _contains_unsafe_call(node.value):
                raise ValueError(
                    "Operator code must not execute calls at module import time (top-level annotated assignment)."
                )
        if not isinstance(node, allowed_top_level):
            raise ValueError(
                f"Operator code contains unsupported top-level statement: {type(node).__name__}."
            )

    class_node: ast.ClassDef | None = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            class_node = node
            break
    if class_node is None:
        raise ValueError(f"Operator class '{class_name}' not found in source.")

    def is_operator_base(expr: ast.expr) -> bool:
        if isinstance(expr, ast.Name):
            return expr.id == "Operator"
        if isinstance(expr, ast.Attribute):
            return expr.attr == "Operator"
        if isinstance(expr, ast.Subscript):
            return is_operator_base(expr.value)
        return False

    if not any(is_operator_base(base) for base in class_node.bases):
        raise ValueError(f"Operator class '{class_name}' must inherit from Operator.")

    doc = (ast.get_docstring(class_node) or "").strip()
    if "inputs:" not in doc.lower() or "outputs:" not in doc.lower():
        raise ValueError(
            f"Operator '{class_name}' must include a class docstring with 'Inputs:' and 'Outputs:'."
        )

    call_method = None
    for item in class_node.body:
        if isinstance(item, ast.AsyncFunctionDef) and item.name == "__call__":
            call_method = item
            break
    if call_method is None:
        raise ValueError(f"Operator '{class_name}' must implement `async def __call__(...)`.")


def import_operator_from_code(
    code: str,
    class_name: str,
    *,
    description: str = "",
    inputs: str = "",
    outputs: str = "",
) -> Type[Operator]:
    """
    Import an Operator subclass from source code.

    The code is executed in a fresh module namespace with common dependencies injected.
    Validates operator code structure and ensures proper docstrings before importing.
    """
    code = fix_operator_imports(code)
    code = _ensure_operator_base_class(code, class_name)
    code, _changed = ensure_operator_docstring(
        code,
        class_name=class_name,
        description=description,
        inputs=inputs,
        outputs=outputs,
    )
    validate_operator_source(code, class_name=class_name)

    # Import all necessary Pydantic dependencies and common imports
    module_name = f"dsflow_custom_op_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_loader(module_name, loader=None)
    module = importlib.util.module_from_spec(spec)

    # Inject common dependencies that operators might need
    import_dict = {
        "Operator": Operator,
        "LLMService": LLMService,
        "SandboxService": SandboxService,
        "WorkspaceService": WorkspaceService,
        "DataPerceptionRuntime": DataPerceptionRuntime,
        "BaseModel": BaseModel,
        "Field": Field,
        # Add commonly used typing imports
        "List": list,
        "Dict": dict,
        "Any": object,
    }

    # Try to import ExecutionResult if available
    try:
        from dslighting.utils.typing import ExecutionResult

        import_dict["ExecutionResult"] = ExecutionResult
    except ImportError:
        pass

    module.__dict__.update(import_dict)

    try:
        exec(code, module.__dict__)
    except Exception as e:
        raise ValueError(f"Failed to execute operator code for '{class_name}': {e}") from e

    cls = getattr(module, class_name, None)
    if cls is None:
        raise ValueError(f"Class '{class_name}' not found in operator code after execution.")
    if not isinstance(cls, type) or not issubclass(cls, Operator):
        raise TypeError(f"'{class_name}' is not an Operator subclass.")

    return cls
