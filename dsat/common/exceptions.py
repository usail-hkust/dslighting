class DSATError(Exception):
    """Base exception for all DSAT-related errors."""
    def __init__(self, message=None, *args, **kwargs):
        if message is None:
            message = "An error occurred in the DSAT framework."
        super().__init__(message, *args)
        self.message = message
        self.details = kwargs.get("details", None)

    def __str__(self):
        if self.details:
            return f"{self.message} Details: {self.details}"
        return self.message

class WorkspaceError(DSATError):
    """Exception raised for workspace-related errors."""
    def __init__(self, message=None, *args, **kwargs):
        if message is None:
            message = "A workspace-related error occurred."
        super().__init__(message, *args, **kwargs)

class SandboxError(DSATError):
    """Exception raised for sandbox execution errors."""
    def __init__(self, message=None, *args, **kwargs):
        if message is None:
            message = "A sandbox execution error occurred."
        super().__init__(message, *args, **kwargs)

class LLMError(DSATError):
    """Exception raised for LLM service errors."""
    def __init__(self, message=None, *args, **kwargs):
        if message is None:
            message = "An LLM service error occurred."
        super().__init__(message, *args, **kwargs)

class DynamicImportError(DSATError):
    """Exception raised when dynamically importing code fails (e.g., syntax errors in generated workflows)."""
    def __init__(self, message=None, *args, **kwargs):
        if message is None:
            message = "A dynamic code import error occurred."
        super().__init__(message, *args, **kwargs)

class WorkflowError(DSATError):
    """Exception raised for workflow execution errors."""
    def __init__(self, message=None, *args, **kwargs):
        if message is None:
            message = "A workflow execution error occurred."
        super().__init__(message, *args, **kwargs)