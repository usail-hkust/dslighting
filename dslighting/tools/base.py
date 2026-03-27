"""
DSLighting Tool System

This module defines the Tool system that allows researchers to
encapsulate any functionality as a reusable tool.

Design Principles:
- Simple: Just a name, description, and callable function
- Composable: Tools can be combined and chained
- Extensible: Researchers can add custom tools
"""

import inspect
import time
from typing import Callable, Dict, Any, Optional, List, Type
from dataclasses import dataclass, field
from threading import Lock
from pydantic import BaseModel, Field

from dslighting.logging.events import emit_runtime_event, is_tool_trace_enabled


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
        version: Tool version string (semantic versioning)
        author: Tool author
        tags: List of tags for categorization
        dependencies: List of required dependencies
        input_schema: Optional input schema type (Pydantic BaseModel)
        output_schema: Optional output schema type (Pydantic BaseModel)
        metadata: Additional metadata dictionary

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
    version: str = "1.0.0"
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    input_schema: Optional[Type[BaseModel]] = None
    output_schema: Optional[Type[BaseModel]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Call the tool.

        Args:
            *args: Positional arguments passed to the underlying function.
            **kwargs: Keyword arguments passed to the underlying function.

        Returns:
            Any: The result returned by the underlying function fn.
        """
        if not is_tool_trace_enabled():
            return self.fn(*args, **kwargs)

        started = time.perf_counter()
        payload_args = {"args": list(args), "kwargs": kwargs}
        try:
            result = self.fn(*args, **kwargs)
        except Exception as exc:
            emit_runtime_event(
                "tool.call.failed",
                f"Tool '{self.name}' failed",
                tags={
                    "tool_name": self.name,
                    "tool_version": self.version,
                    "tool_description": self.description,
                },
                metrics={"duration_seconds": round(time.perf_counter() - started, 4)},
                payloads={"tool_args": payload_args},
                error={"type": type(exc).__name__, "message": str(exc)},
            )
            raise

        if inspect.isawaitable(result):
            async def _await_and_trace():
                try:
                    awaited = await result
                except Exception as exc:
                    emit_runtime_event(
                        "tool.call.failed",
                        f"Tool '{self.name}' failed",
                        tags={
                            "tool_name": self.name,
                            "tool_version": self.version,
                            "tool_description": self.description,
                        },
                        metrics={"duration_seconds": round(time.perf_counter() - started, 4)},
                        payloads={"tool_args": payload_args},
                        error={"type": type(exc).__name__, "message": str(exc)},
                    )
                    raise
                emit_runtime_event(
                    "tool.call.completed",
                    f"Tool '{self.name}' completed",
                    tags={
                        "tool_name": self.name,
                        "tool_version": self.version,
                        "tool_description": self.description,
                    },
                    metrics={"duration_seconds": round(time.perf_counter() - started, 4)},
                    payloads={"tool_args": payload_args, "tool_result": awaited},
                )
                return awaited

            return _await_and_trace()

        emit_runtime_event(
            "tool.call.completed",
            f"Tool '{self.name}' completed",
            tags={
                "tool_name": self.name,
                "tool_version": self.version,
                "tool_description": self.description,
            },
            metrics={"duration_seconds": round(time.perf_counter() - started, 4)},
            payloads={"tool_args": payload_args, "tool_result": result},
        )
        return result

    def __repr__(self) -> str:
        """
        Return a string representation of the Tool.

        Returns:
            str: A string in the format 'Tool(name='...', description='...')'.
        """
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
        self._lock: Lock = Lock()

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
        with self._lock:
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
        with self._lock:
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
        with self._lock:
            self._tools.clear()

    def __len__(self) -> int:
        """
        Return the number of registered tools.

        Returns:
            int: The count of tools currently registered in the registry.
        """
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        """
        Check if a tool with the given name is registered.

        Args:
            name (str): The name of the tool to check.

        Returns:
            bool: True if a tool with the name exists, False otherwise.
        """
        return name in self._tools

    def __repr__(self) -> str:
        return f"ToolRegistry(num_tools={len(self._tools)})"


class VersionedToolRegistry:
    """
    Versioned Tool Registry

    Registry supporting multiple versions of the same tool.
    Each tool name can have multiple versions, with a default version specified.

    Attributes:
        _tools: Dictionary mapping tool names to version dictionaries
        _default_versions: Dictionary mapping tool names to their default version

    Example:
        >>> registry = VersionedToolRegistry()
        >>>
        >>> tool_v1 = Tool(name="calculator", description="Calc", fn=lambda x: x*2, version="1.0.0")
        >>> tool_v2 = Tool(name="calculator", description="Calc v2", fn=lambda x: x**2, version="2.0.0")
        >>>
        >>> registry.register(tool_v1, set_default=True)
        >>> registry.register(tool_v2, set_default=True)
        >>>
        >>> registry.get("calculator")  # Gets default version
        Tool(name='calculator', ...)
        >>> registry.get("calculator", version="1.0.0")
        Tool(name='calculator', ...)
    """

    def __init__(self):
        """Initialize empty versioned tool registry"""
        self._tools: Dict[str, Dict[str, Tool]] = {}
        self._default_versions: Dict[str, str] = {}
        self._lock: Lock = Lock()

    def register(self, tool: Tool, set_default: bool = True) -> None:
        """
        Register a tool with versioning

        Args:
            tool: Tool instance to register
            set_default: If True, set this version as the default for the tool name

        Example:
            >>> registry = VersionedToolRegistry()
            >>> tool = Tool(name="test", description="Test", fn=lambda: None, version="1.0.0")
            >>> registry.register(tool, set_default=True)
            >>> "test" in registry.list_tools()
            True
        """
        with self._lock:
            if tool.name not in self._tools:
                self._tools[tool.name] = {}
            self._tools[tool.name][tool.version] = tool
            if set_default:
                self._default_versions[tool.name] = tool.version

    def get(self, name: str, version: Optional[str] = None) -> Optional[Tool]:
        """
        Get a tool by name and optional version

        Args:
            name: Tool name
            version: Optional version string. If None, returns the default version.

        Returns:
            Tool if found, None otherwise

        Example:
            >>> registry = VersionedToolRegistry()
            >>> tool = Tool(name="test", description="Test", fn=lambda: None, version="1.0.0")
            >>> registry.register(tool)
            >>> registry.get("test") is not None
            True
            >>> registry.get("test", version="1.0.0") is not None
            True
            >>> registry.get("nonexistent") is None
            True
        """
        if name not in self._tools:
            return None
        if version is None:
            default_version = self._default_versions.get(name)
            if default_version is None:
                return None
            return self._tools[name].get(default_version)
        return self._tools[name].get(version)

    def list_tools(self, version: Optional[str] = None) -> Dict[str, Tool]:
        """
        List all registered tools or tools of a specific version

        Args:
            version: Optional version string. If None, lists default versions only.

        Returns:
            Dictionary mapping tool names to Tool instances

        Example:
            >>> registry = VersionedToolRegistry()
            >>> tool1 = Tool(name="t1", description="1", fn=lambda: None, version="1.0.0")
            >>> tool2 = Tool(name="t2", description="2", fn=lambda: None, version="1.0.0")
            >>> registry.register(tool1)
            >>> registry.register(tool2)
            >>> list(registry.list_tools().keys())
            ['t1', 't2']
        """
        if version is None:
            result = {}
            for name, default_version in self._default_versions.items():
                tool = self._tools[name].get(default_version)
                if tool:
                    result[name] = tool
            return result
        else:
            return {
                name: tools.get(version)
                for name, tools in self._tools.items()
                if version in tools
            }

    def list_versions(self, name: str) -> List[str]:
        """
        List all available versions for a tool

        Args:
            name: Tool name

        Returns:
            List of version strings sorted in ascending order

        Example:
            >>> registry = VersionedToolRegistry()
            >>> registry.register(Tool(name="test", description="Test", fn=lambda: None, version="2.0.0"))
            >>> registry.register(Tool(name="test", description="Test", fn=lambda: None, version="1.0.0"))
            >>> registry.list_versions("test")
            ['1.0.0', '2.0.0']
        """
        if name not in self._tools:
            return []
        return sorted(self._tools[name].keys())

    def get_default_version(self, name: str) -> Optional[str]:
        """
        Get the default version for a tool

        Args:
            name: Tool name

        Returns:
            Default version string if found, None otherwise
        """
        return self._default_versions.get(name)

    def set_default_version(self, name: str, version: str) -> bool:
        """
        Set the default version for a tool

        Args:
            name: Tool name
            version: Version string to set as default

        Returns:
            True if successful, False if tool or version not found
        """
        with self._lock:
            if name not in self._tools or version not in self._tools[name]:
                return False
            self._default_versions[name] = version
            return True

    def remove(self, name: str, version: Optional[str] = None) -> bool:
        """
        Remove a tool or a specific version

        Args:
            name: Tool name
            version: Optional version string. If None, removes all versions.

        Returns:
            True if removed, False otherwise
        """
        with self._lock:
            if name not in self._tools:
                return False
            if version is None:
                del self._tools[name]
                if name in self._default_versions:
                    del self._default_versions[name]
                return True
            if version not in self._tools[name]:
                return False
            del self._tools[name][version]
            if self._default_versions.get(name) == version:
                remaining_versions = list(self._tools[name].keys())
                if remaining_versions:
                    self._default_versions[name] = remaining_versions[0]
                else:
                    del self._default_versions[name]
                    del self._tools[name]
            return True

    def clear(self) -> None:
        """Clear all tools"""
        with self._lock:
            self._tools.clear()
            self._default_versions.clear()

    def __len__(self) -> int:
        """Return number of tools (unique names)"""
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        """Check if tool name is registered"""
        return name in self._tools

    def __repr__(self) -> str:
        total_versions = sum(len(versions) for versions in self._tools.values())
        return f"VersionedToolRegistry(num_tools={len(self._tools)}, total_versions={total_versions})"


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
    List all tools in the global registry.

    Returns:
        Dict[str, Tool]: A dictionary mapping tool names to Tool instances.
    """
    return _global_registry.list_tools()
