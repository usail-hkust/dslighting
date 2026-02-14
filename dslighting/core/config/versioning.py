"""
Configuration Version Management System.

This module provides configuration version detection, migration, and compatibility
checking for DSLighting. It ensures backward compatibility when configuration
formats change between versions.

Features:
- Version detection: Automatically detect config version from _version field
- Configuration migration: Migrate configs from old versions to new versions
- Version compatibility: Check if a config version is compatible with current version
- Migration hooks: Support custom migration functions
- Migration history: Track migration history in the config

Version History:
- 2.0: Current config format with structured sections

Example Usage:
    >>> from dslighting.core.config.versioning import ConfigVersionManager
    >>> manager = ConfigVersionManager()
    >>>
    >>> # Detect version of existing config
    >>> version = manager.detect_version(config)
    >>>
    >>> # Check compatibility
    >>> is_compatible = manager.is_compatible(config)
"""

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple
from typing_extensions import ClassVar

logger = logging.getLogger(__name__)


class ConfigVersionError(Exception):
    """Base exception for configuration version errors."""
    pass


class MigrationNotSupportedError(ConfigVersionError):
    """Raised when migration between versions is not supported."""
    pass


class InvalidVersionError(ConfigVersionError):
    """Raised when version string is invalid."""
    pass


class ConfigVersionManager:
    """
    Manages configuration versions and provides migration functionality.

    This class handles:
    - Detecting the version of a configuration
    - Checking version compatibility
    - Recording migration history

    Attributes:
        VERSION: Current configuration version (class constant)
        SUPPORTED_VERSIONS: List of all supported versions
        MIN_COMPATIBLE_VERSION: Minimum compatible version for this manager
    """

    # Current configuration version
    VERSION: ClassVar[str] = "2.0"

    # All supported versions in order
    SUPPORTED_VERSIONS: ClassVar[List[str]] = ["2.0"]

    # Minimum compatible version
    MIN_COMPATIBLE_VERSION: ClassVar[str] = "2.0"

    # Version ordering for comparison
    _VERSION_ORDER: ClassVar[Dict[str, int]] = {
        v: i for i, v in enumerate(SUPPORTED_VERSIONS)
    }

    def __init__(self) -> None:
        """Initialize the configuration version manager."""
        # Migration registry (empty - no legacy migrations needed for v2.0)
        self._migration_registry: Dict[Tuple[str, str], Callable[[Dict], Dict]] = {}

    def detect_version(self, config: Dict[str, Any]) -> str:
        """
        Detect the version of a configuration.

        Args:
            config: Configuration dictionary to check.

        Returns:
            Detected version string. Returns VERSION if no version field exists.

        Examples:
            >>> config_with_version = {"_version": "2.0", "llm": {...}}
            >>> manager.detect_version(config_with_version)
            '2.0'

            >>> config_without_version = {"llm": {...}}
            >>> manager.detect_version(config_without_version)
            '2.0'
        """
        # Check for explicit version field
        if "_version" in config:
            version = str(config["_version"])
            if version not in self.SUPPORTED_VERSIONS:
                logger.warning(
                    f"Unknown config version '{version}'. "
                    f"Supported versions: {self.SUPPORTED_VERSIONS}. "
                    f"Assuming compatibility with latest version."
                )
                return self.VERSION
            return version

        # Default to current version for unknown configs
        return self.VERSION

    def migrate(
        self,
        config: Dict[str, Any],
        from_version: Optional[str] = None,
        to_version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Ensure configuration has the correct version.

        For v2.0+, this simply adds the _version field if missing.
        Legacy migrations (v0.9, v1.0, v1.1) are no longer supported.

        Args:
            config: Configuration dictionary to migrate.
            from_version: Source version (deprecated, auto-detected).
            to_version: Target version (deprecated, defaults to current).

        Returns:
            Configuration dictionary with version field set.

        Raises:
            MigrationNotSupportedError: If legacy version detected.

        Examples:
            >>> config = {"llm": {"model": "gpt-4"}}
            >>> migrated = manager.migrate(config)
            >>> migrated["_version"]
            '2.0'
        """
        current_version = self.detect_version(config)
        target_version = to_version or self.VERSION

        # No changes needed if already at target version
        if current_version == target_version:
            return config

        # Legacy versions no longer supported
        if current_version not in self.SUPPORTED_VERSIONS:
            raise MigrationNotSupportedError(
                f"Legacy version '{current_version}' is no longer supported. "
                f"Please upgrade your config to v2.0 format. "
                f"Supported versions: {self.SUPPORTED_VERSIONS}"
            )

        # Initialize migration history
        migration_history: List[Dict[str, Any]] = config.get("_migration_history", [])

        # Record migration step
        migration_history.append({
            "from_version": current_version,
            "to_version": target_version,
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Update version and history
        migrated_config = config.copy()
        migrated_config["_version"] = target_version
        migrated_config["_migration_history"] = migration_history

        return migrated_config

    def get_migration_path(self, from_version: str, to_version: str) -> List[Tuple[str, str]]:
        """
        Calculate the migration path between two versions.

        For v2.0+, returns empty list since no migrations are needed.

        Args:
            from_version: Source version.
            to_version: Target version.

        Returns:
            List of (from_version, to_version) tuples representing the path.

        Examples:
            >>> manager.get_migration_path("2.0", "2.0")
            []
        """
        self._validate_version(from_version)
        self._validate_version(to_version)

        # Same version, no migration needed
        if from_version == to_version:
            return []

        # Only v2.0 is supported, so no migration path for different versions
        return [(from_version, to_version)]

    def is_version_supported(self, version: str) -> bool:
        """
        Check if a version is supported.

        Args:
            version: Version string to check.

        Returns:
            True if version is in supported versions range.
        """
        try:
            self._validate_version(version)
            return True
        except InvalidVersionError:
            return False

    def is_compatible(self, config: Dict[str, Any]) -> bool:
        """
        Check if a configuration is compatible with current version.

        Args:
            config: Configuration dictionary to check.

        Returns:
            True if config can be migrated to current version.
        """
        version = self.detect_version(config)
        return self.is_version_supported(version)

    def _validate_version(self, version: str) -> None:
        """
        Validate a version string.

        Args:
            version: Version string to validate.

        Raises:
            InvalidVersionError: If version is not valid.
        """
        if version not in self.SUPPORTED_VERSIONS:
            raise InvalidVersionError(
                f"Invalid version '{version}'. "
                f"Must be one of: {self.SUPPORTED_VERSIONS}"
            )

    def register_migration(
        self, from_version: str, to_version: str, migration_func: Callable[[Dict], Dict]
    ) -> None:
        """
        Register a custom migration function.

        This allows extending the migration system with custom migrations.

        Args:
            from_version: Source version.
            to_version: Target version.
            migration_func: Function that takes a config dict and returns migrated dict.
        """
        self._migration_registry[(from_version, to_version)] = migration_func
        logger.info(
            f"Registered custom migration: {from_version} -> {to_version}"
        )

    # =====================================================================
    # Migration Functions (Legacy - kept for reference)
    # =====================================================================
    # Legacy migration functions removed. Only v2.0 format is now supported.


class ConfigVersionManagerFactory:
    """
    Factory for creating ConfigVersionManager instances.

    This factory supports creating managers with custom migration functions
    and different default versions.
    """

    _instance: Optional["ConfigVersionManagerFactory"] = None
    _managers: Dict[str, ConfigVersionManager] = {}

    def __new__(cls) -> "ConfigVersionManagerFactory":
        """Create singleton factory instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._managers = {}
        return cls._instance

    def get_manager(
        self, version: Optional[str] = None
    ) -> ConfigVersionManager:
        """
        Get a ConfigVersionManager instance.

        Args:
            version: Optional version string for specific manager.

        Returns:
            ConfigVersionManager instance.
        """
        version = version or "default"

        if version not in self._managers:
            self._managers[version] = ConfigVersionManager()

        return self._managers[version]

    def register_custom_migration(
        self,
        from_version: str,
        to_version: str,
        migration_func: Callable[[Dict], Dict],
        version: Optional[str] = None,
    ) -> None:
        """
        Register a custom migration for a specific manager.

        Args:
            from_version: Source version.
            to_version: Target version.
            migration_func: Migration function.
            version: Manager version (default: default manager).
        """
        manager = self.get_manager(version)
        manager.register_migration(from_version, to_version, migration_func)


# Global version manager instance
version_manager = ConfigVersionManager()


def get_version_manager() -> ConfigVersionManager:
    """
    Get the global configuration version manager.

    Returns:
        Global ConfigVersionManager instance.
    """
    return version_manager


def detect_config_version(config: Dict[str, Any]) -> str:
    """
    Detect the version of a configuration.

    This is a convenience function that uses the global version manager.

    Args:
        config: Configuration dictionary.

    Returns:
        Detected version string.
    """
    return version_manager.detect_version(config)


def migrate_config(
    config: Dict[str, Any],
    to_version: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Migrate a configuration to the specified version.

    This is a convenience function that uses the global version manager.

    Args:
        config: Configuration dictionary to migrate.
        to_version: Target version (default: current version).

    Returns:
        Migrated configuration.
    """
    return version_manager.migrate(config, to_version=to_version)


def is_config_compatible(config: Dict[str, Any]) -> bool:
    """
    Check if a configuration is compatible.

    This is a convenience function that uses the global version manager.

    Args:
        config: Configuration dictionary.

    Returns:
        True if configuration is compatible.
    """
    return version_manager.is_compatible(config)


__all__ = [
    # Main classes
    "ConfigVersionManager",
    "ConfigVersionManagerFactory",
    # Exceptions
    "ConfigVersionError",
    "MigrationNotSupportedError",
    "InvalidVersionError",
    # Convenience functions
    "get_version_manager",
    "detect_config_version",
    "migrate_config",
    "is_config_compatible",
]
