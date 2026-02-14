"""
Utility for dynamically importing and instantiating classes from code strings.
Ported from the AFlow project for use in the meta-optimization evaluation step.
"""
import ast
import importlib.util
import sys
from typing import Any, Dict
import logging

from dslighting.error import DynamicImportError

logger = logging.getLogger(__name__)

_BLOCKED_IMPORT_MODULES = {
    "os",
    "subprocess",
    "socket",
    "shutil",
    "pickle",
}

_BLOCKED_CALLS = {
    "eval",
    "exec",
    "__import__",
    "open",
    "compile",
    "input",
    "os.system",
    "os.popen",
    "subprocess.Popen",
    "subprocess.run",
    "subprocess.call",
    "subprocess.check_call",
    "subprocess.check_output",
    "shutil.rmtree",
}


def _attribute_to_name(node: ast.AST) -> str:
    """Convert an AST attribute chain to dotted notation, best effort."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _attribute_to_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _validate_code_safety(code_string: str) -> None:
    """
    Perform minimal static safety checks before executing dynamic workflow code.

    We only allow a constrained subset of Python by rejecting imports/calls that
    can escape the sandbox or execute arbitrary system commands directly.
    """
    try:
        tree = ast.parse(code_string)
    except SyntaxError:
        # Let caller wrap syntax errors into DynamicImportError consistently.
        raise

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_root = alias.name.split(".", 1)[0]
                if module_root in _BLOCKED_IMPORT_MODULES:
                    raise DynamicImportError(f"Blocked import in dynamic workflow code: '{module_root}'")

        if isinstance(node, ast.ImportFrom):
            module_name = (node.module or "").split(".", 1)[0]
            if module_name in _BLOCKED_IMPORT_MODULES:
                raise DynamicImportError(f"Blocked import in dynamic workflow code: '{module_name}'")

        if isinstance(node, ast.Call):
            called = _attribute_to_name(node.func)
            if called in _BLOCKED_CALLS:
                raise DynamicImportError(f"Blocked function call in dynamic workflow code: '{called}'")


def import_workflow_from_string(code_string: str, class_name: str = "Workflow") -> Any:
    """
    Dynamically imports a workflow class from a code string.
    
    Args:
        code_string: The string containing the Python code.
        class_name: The name of the class to import (default: "Workflow").
    
    Returns:
        The workflow class.
        
    Raises:
        DynamicImportError: If the import fails for any reason.
    """
    module_name = None
    try:
        _validate_code_safety(code_string)

        # Create a temporary, unique module name to avoid conflicts
        module_name = f"dynamic_workflow_module_{hash(code_string)}"
        if module_name in sys.modules:
            del sys.modules[module_name]

        spec = importlib.util.spec_from_loader(module_name, loader=None)
        module = importlib.util.module_from_spec(spec)

        # Inject necessary base classes and types into the module's scope
        # to prevent NameError during exec.
        module.__dict__["BaseWorkflow"] = __import__("dslighting.workflows.base", fromlist=["BaseWorkflow"]).BaseWorkflow
        module.__dict__["Path"] = __import__("pathlib").Path
        module.__dict__["asyncio"] = __import__("asyncio")
        module.__dict__["shutil"] = __import__("shutil")
        module.__dict__["Dict"] = __import__("typing").Dict
        module.__dict__["Any"] = __import__("typing").Any
        module.__dict__["List"] = __import__("typing").List
        module.__dict__["LLMService"] = __import__("dslighting.services.llm", fromlist=["LLMService"]).LLMService
        module.__dict__["SandboxService"] = __import__("dslighting.services.sandbox", fromlist=["SandboxService"]).SandboxService
        module.__dict__["parse_plan_and_code"] = __import__(
            "dslighting.utils.parsing",
            fromlist=["parse_plan_and_code"],
        ).parse_plan_and_code
        
        # Execute the code within the new module's namespace
        exec(code_string, module.__dict__)

        # Get the class from the module
        WorkflowClass = getattr(module, class_name, None)

        if WorkflowClass:
            return WorkflowClass
        else:
            error_msg = f"Class '{class_name}' not found in the provided dynamic code."
            logger.error(error_msg)
            raise DynamicImportError(error_msg)
            
    except DynamicImportError:
        raise
    except Exception as e:
        error_msg = f"Error during dynamic class import (e.g., syntax error): {e}"
        logger.error(error_msg, exc_info=True)
        raise DynamicImportError(error_msg) from e
    finally:
        if module_name and module_name in sys.modules:
            del sys.modules[module_name]
