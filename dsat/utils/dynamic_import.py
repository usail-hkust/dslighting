"""
Utility for dynamically importing and instantiating classes from code strings.
Ported from the AFlow project for use in the meta-optimization evaluation step.
"""
import importlib.util
import sys
from typing import Any, Optional, Dict
import logging
from dsat.common.exceptions import DynamicImportError # Import the new exception

logger = logging.getLogger(__name__)

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
    try:
        # Create a temporary, unique module name to avoid conflicts
        module_name = f"dynamic_workflow_module_{hash(code_string)}"
        if module_name in sys.modules:
            del sys.modules[module_name]

        spec = importlib.util.spec_from_loader(module_name, loader=None)
        module = importlib.util.module_from_spec(spec)

        # Inject necessary base classes and types into the module's scope
        # to prevent NameError during exec.
        module.__dict__['DSATWorkflow'] = __import__('dsat.workflows.base', fromlist=['DSATWorkflow']).DSATWorkflow
        module.__dict__['Path'] = __import__('pathlib').Path
        module.__dict__['asyncio'] = __import__('asyncio')
        module.__dict__['shutil'] = __import__('shutil')
        module.__dict__['Dict'] = __import__('typing').Dict
        module.__dict__['Any'] = __import__('typing').Any
        module.__dict__['List'] = __import__('typing').List
        module.__dict__['LLMService'] = __import__('dsat.services.llm', fromlist=['LLMService']).LLMService
        module.__dict__['SandboxService'] = __import__('dsat.services.sandbox', fromlist=['SandboxService']).SandboxService
        module.__dict__['parse_plan_and_code'] = __import__('dsat.utils.parsing', fromlist=['parse_plan_and_code']).parse_plan_and_code
        
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
        raise # Re-raise if already caught
    except Exception as e:
        error_msg = f"Error during dynamic class import (e.g., syntax error): {e}"
        logger.error(error_msg, exc_info=True)
        raise DynamicImportError(error_msg) from e
    finally:
        if module_name in sys.modules:
            del sys.modules[module_name]

