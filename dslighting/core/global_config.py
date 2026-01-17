"""
Global configuration for DSLighting.

This module provides a central place to store configuration that can be shared
across the DSLighting package, such as parent directories for data and registry.
"""

from pathlib import Path
from typing import Optional
from threading import Lock

class GlobalConfig:
    """
    Thread-safe global configuration for DSLighting.

    This class stores configuration that can be shared across Agent instances,
    such as default parent directories for data and registry.

    Attributes:
        data_parent_dir: Default parent directory for competition data
        registry_parent_dir: Default parent directory for registry configurations
    """
    _instance = None
    _lock = Lock()

    def __new__(cls):
        """Ensure singleton pattern with thread safety."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._data_parent_dir = None
                    cls._instance._registry_parent_dir = None
        return cls._instance

    @property
    def data_parent_dir(self) -> Optional[Path]:
        """Get the default data parent directory."""
        return self._data_parent_dir

    @data_parent_dir.setter
    def data_parent_dir(self, value: Optional[str | Path]):
        """Set the default data parent directory."""
        self._data_parent_dir = Path(value) if value is not None else None

    @property
    def registry_parent_dir(self) -> Optional[Path]:
        """Get the default registry parent directory."""
        return self._registry_parent_dir

    @registry_parent_dir.setter
    def registry_parent_dir(self, value: Optional[str | Path]):
        """Set the default registry parent directory."""
        self._registry_parent_dir = Path(value) if value is not None else None

    def set_parent_dirs(
        self,
        data_parent_dir: Optional[str | Path] = None,
        registry_parent_dir: Optional[str | Path] = None
    ):
        """
        Set default parent directories for data and registry.

        Args:
            data_parent_dir: Default parent directory for competition data.
                           Example: "/path/to/data/competitions"
            registry_parent_dir: Default parent directory for registry configurations.
                                Example: "/path/to/registry"

        Examples:
            >>> config = GlobalConfig()
            >>> config.set_parent_dirs(
            ...     data_parent_dir="/path/to/data/competitions",
            ...     registry_parent_dir="/path/to/registry"
            ... )
        """
        if data_parent_dir is not None:
            self.data_parent_dir = data_parent_dir
        if registry_parent_dir is not None:
            self.registry_parent_dir = registry_parent_dir

    def get_task_paths(self, task_id: str) -> tuple[Optional[Path], Optional[Path]]:
        """
        Get full paths for a task using configured parent directories.

        Args:
            task_id: Task/competition identifier (e.g., "bike-sharing-demand")

        Returns:
            Tuple of (data_dir, registry_dir) or (None, None) if not configured

        Examples:
            >>> config = GlobalConfig()
            >>> config.set_parent_dirs(
            ...     data_parent_dir="/path/to/data/competitions",
            ...     registry_parent_dir="/path/to/registry"
            ... )
            >>> data_dir, registry_dir = config.get_task_paths("bike-sharing-demand")
            >>> print(data_dir)
            /path/to/data/competitions/bike-sharing-demand
            >>> print(registry_dir)
            /path/to/registry/bike-sharing-demand
        """
        data_dir = None
        registry_dir = None

        if self._data_parent_dir is not None:
            data_dir = self._data_parent_dir / task_id

        if self._registry_parent_dir is not None:
            registry_dir = self._registry_parent_dir / task_id

        return data_dir, registry_dir

    def reset(self):
        """Reset all configuration to default values (None)."""
        self._data_parent_dir = None
        self._registry_parent_dir = None

    def __repr__(self) -> str:
        """Return string representation of current configuration."""
        return (
            f"GlobalConfig("
            f"data_parent_dir={self._data_parent_dir}, "
            f"registry_parent_dir={self._registry_parent_dir}"
            f")"
        )


# Global instance
_global_config = GlobalConfig()


def get_global_config() -> GlobalConfig:
    """
    Get the global configuration instance.

    Returns:
        GlobalConfig singleton instance

    Examples:
        >>> from dslighting.core.global_config import get_global_config
        >>> config = get_global_config()
        >>> config.set_parent_dirs(
        ...     data_parent_dir="/path/to/data",
        ...     registry_parent_dir="/path/to/registry"
        ... )
    """
    return _global_config
