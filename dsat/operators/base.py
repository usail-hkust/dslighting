from abc import ABC, abstractmethod
from typing import Optional, Any

from dsat.services.llm import LLMService

class Operator(ABC):
    """
    Abstract base class for a self-contained capability.

    Operators are the "verbs" of the agent framework, representing discrete
    actions like generating code, executing it, or reviewing results.
    """
    def __init__(self, llm_service: Optional[LLMService] = None, name: Optional[str] = None):
        self.name = name or self.__class__.__name__
        self.llm_service = llm_service

    @abstractmethod
    async def __call__(self, *args, **kwargs) -> Any:
        """
        Executes the operator's logic. All operator calls are asynchronous.
        """
        raise NotImplementedError