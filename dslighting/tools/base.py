"""
DSLighting Tool System

This module defines the Tool system that allows researchers to
encapsulate any functionality as a reusable tool.

Design Principles:
- Simple: Just a name, description, and callable function
- Composable: Tools can be combined and chained
- Extensible: Researchers can add custom tools
"""

from typing import Callable, Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class Tool:
    """
    Tool

    A tool represents a reusable function that can be called by an agent.
    Any callable can be wrapped as a tool.

    Attributes:
        name: Unique tool name
        description: Human-readable description
        fn: Callable function

    Example:
        >>> def my_function(x: int) -> int:
        ...     return x * 2
        >>>
        >>> tool = Tool(
        ...     name="doubler",
        ...     description="Doubles a number",
        ...     fn=my_function
        ... )
        >>> tool(5)
        10
    """

    name: str
    description: str
    fn: Callable

    def __call__(self, *args, **kwargs) -> Any:
        """
        Call the tool

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result of calling the underlying function
        """
        return self.fn(*args, **kwargs)

    def __repr__(self) -> str:
        return f"Tool(name={self.name!r}, description={self.description!r})"


class ToolRegistry:
    """
    Tool Registry

    Manages a collection of tools and provides methods to
    register, retrieve, and list tools.

    Example:
        >>> registry = ToolRegistry()
        >>>
        >>> tool1 = Tool(name="tool1", description="First tool", fn=lambda: None)
        >>> registry.register(tool1)
        >>>
        >>> tool2 = Tool(name="tool2", description="Second tool", fn=lambda: None)
        >>> registry.register(tool2)
        >>>
        >>> registry.list_tools()
        {'tool1': Tool(name='tool1', ...), 'tool2': Tool(name='tool2', ...)}
        >>>
        >>> retrieved = registry.get("tool1")
        >>> retrieved.name
        'tool1'
    """

    def __init__(self):
        """Initialize empty tool registry"""
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """
        Register a tool

        Args:
            tool: Tool instance to register

        Raises:
            ValueError: If a tool with the same name already exists

        Example:
            >>> registry = ToolRegistry()
            >>> tool = Tool(name="test", description="Test", fn=lambda: None)
            >>> registry.register(tool)
            >>> "test" in registry.list_tools()
            True
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name

        Args:
            name: Tool name

        Returns:
            Tool if found, None otherwise

        Example:
            >>> registry = ToolRegistry()
            >>> tool = Tool(name="test", description="Test", fn=lambda: None)
            >>> registry.register(tool)
            >>> registry.get("test") is not None
            True
            >>> registry.get("nonexistent") is None
            True
        """
        return self._tools.get(name)

    def list_tools(self) -> Dict[str, Tool]:
        """
        List all registered tools

        Returns:
            Dictionary mapping tool names to Tool instances

        Example:
            >>> registry = ToolRegistry()
            >>> tool1 = Tool(name="t1", description="1", fn=lambda: None)
            >>> tool2 = Tool(name="t2", description="2", fn=lambda: None)
            >>> registry.register(tool1)
            >>> registry.register(tool2)
            >>> list(registry.list_tools().keys())
            ['t1', 't2']
        """
        return self._tools.copy()

    def remove(self, name: str) -> bool:
        """
        Remove a tool by name

        Args:
            name: Tool name to remove

        Returns:
            True if tool was removed, False if it didn't exist

        Example:
            >>> registry = ToolRegistry()
            >>> tool = Tool(name="test", description="Test", fn=lambda: None)
            >>> registry.register(tool)
            >>> registry.remove("test")
            True
            >>> registry.remove("nonexistent")
            False
        """
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def clear(self) -> None:
        """
        Clear all tools

        Example:
            >>> registry = ToolRegistry()
            >>> tool = Tool(name="test", description="Test", fn=lambda: None)
            >>> registry.register(tool)
            >>> registry.clear()
            >>> len(registry.list_tools())
            0
        """
        self._tools.clear()

    def __len__(self) -> int:
        """Return number of registered tools"""
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        """Check if tool is registered"""
        return name in self._tools

    def __repr__(self) -> str:
        return f"ToolRegistry(num_tools={len(self._tools)})"


# Create a global tool registry for convenience
_global_registry = ToolRegistry()


def register_tool(tool: Tool) -> None:
    """
    Register a tool in the global registry

    Args:
        tool: Tool instance to register

    Example:
        >>> from dslighting.tools import Tool, register_tool
        >>>
        >>> tool = Tool(name="global_tool", description="Global", fn=lambda: None)
        >>> register_tool(tool)
    """
    _global_registry.register(tool)


def get_tool(name: str) -> Optional[Tool]:
    """
    Get a tool from the global registry

    Args:
        name: Tool name

    Returns:
        Tool if found, None otherwise
    """
    return _global_registry.get(name)


def list_tools() -> Dict[str, Tool]:
    """
    List all tools in the global registry

    Returns:
        Dictionary of tools
    """
    return _global_registry.list_tools()


__all__ = ["Tool", "ToolRegistry", "register_tool", "get_tool", "list_tools"]
