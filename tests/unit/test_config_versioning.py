"""
Tests for configuration versioning system.

These tests verify:
- Version detection (from _version field and legacy formats)
- All migration paths (0.9->1.0, 0.9->2.0, 1.0->1.1, 1.1->2.0)
- Migration history recording
- Convenience functions
"""

import sys
import os
import importlib.util

# Load the versioning module directly without triggering package init
_versioning_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "dslighting", "core", "config", "versioning.py"
)

_versioning_spec = importlib.util.spec_from_file_location("versioning", _versioning_path)
versioning_module = importlib.util.module_from_spec(_versioning_spec)
_versioning_spec.loader.exec_module(versioning_module)

# Extract classes and functions for use in tests
ConfigVersionManager = versioning_module.ConfigVersionManager
ConfigVersionManagerFactory = versioning_module.ConfigVersionManagerFactory
ConfigVersionError = versioning_module.ConfigVersionError
MigrationNotSupportedError = versioning_module.MigrationNotSupportedError
InvalidVersionError = versioning_module.InvalidVersionError
get_version_manager = versioning_module.get_version_manager
detect_config_version = versioning_module.detect_config_version
migrate_config = versioning_module.migrate_config
is_config_compatible = versioning_module.is_config_compatible

import pytest
from typing import Dict, Any


class TestConfigVersionManager:
    """Tests for ConfigVersionManager class."""

    @pytest.fixture
    def manager(self):
        """Create a fresh ConfigVersionManager for each test."""
        return ConfigVersionManager()

    def test_detect_version_from_field(self, manager):
        """Test version detection from _version field."""
        # Version specified explicitly
        config = {"_version": "1.0", "llm": {"model": "gpt-4"}}
        assert manager.detect_version(config) == "1.0"

        config = {"_version": "1.1", "llm": {"model": "gpt-4"}}
        assert manager.detect_version(config) == "1.1"

        config = {"_version": "2.0", "llm": {"model": "gpt-4"}}
        assert manager.detect_version(config) == "2.0"

    def test_detect_version_legacy_0_9(self, manager):
        """Test version detection for legacy 0.9 format."""
        # Legacy format without _version field
        config = {"model": "gpt-4", "temperature": 0.7}
        assert manager.detect_version(config) == "0.9"

        config = {
            "model": "gpt-4",
            "api_key": "sk-xxx",
            "api_base": "https://api.openai.com/v1",
        }
        assert manager.detect_version(config) == "0.9"

    def test_detect_version_current(self, manager):
        """Test version detection for current version."""
        # No version field and no legacy keys
        config = {"unknown_key": "value"}
        assert manager.detect_version(config) == manager.VERSION

    def test_migrate_0_9_to_1_0(self, manager):
        """Test migration from 0.9 to 1.0."""
        # Legacy config
        legacy = {
            "model": "gpt-4",
            "temperature": 0.7,
            "api_key": "sk-xxx",
            "workflow_name": "aide",
            "timeout": 3600,
        }

        migrated = manager.migrate(legacy, from_version="0.9", to_version="1.0")

        # Check version
        assert migrated["_version"] == "1.0"

        # Check restructured sections
        assert "llm" in migrated
        assert migrated["llm"]["model"] == "gpt-4"
        assert migrated["llm"]["temperature"] == 0.7

        assert "workflow" in migrated
        assert migrated["workflow"]["name"] == "aide"

        assert "sandbox" in migrated
        assert migrated["sandbox"]["timeout"] == 3600

    def test_migrate_1_0_to_1_1(self, manager):
        """Test migration from 1.0 to 1.1."""
        config = {
            "_version": "1.0",
            "llm": {"model": "gpt-4"},
            "workflow": {"name": "aide"},
            "run": {"name": "test"},
        }

        migrated = manager.migrate(config, from_version="1.0", to_version="1.1")

        assert migrated["_version"] == "1.1"
        assert "task" in migrated
        assert "dag_runtime" in migrated["run"]

    def test_migrate_1_1_to_2_0(self, manager):
        """Test migration from 1.1 to 2.0."""
        config = {
            "_version": "1.1",
            "llm": {"model": "gpt-4"},
            "workflow": {"name": "aide", "params": {}},
            "agent": {"search": {}},
        }

        migrated = manager.migrate(config, from_version="1.1", to_version="2.0")

        assert migrated["_version"] == "2.0"
        assert "agent" in migrated
        assert migrated["agent"]["search"]["num_drafts"] == 5

    def test_migrate_0_9_to_2_0_direct(self, manager):
        """Test direct migration from 0.9 to 2.0."""
        legacy = {
            "model": "gpt-4",
            "temperature": 0.7,
            "api_key": "sk-xxx",
            "workflow_name": "aide",
            "timeout": 3600,
        }

        migrated = manager.migrate(legacy, from_version="0.9", to_version="2.0")

        assert migrated["_version"] == "2.0"
        assert "llm" in migrated
        assert "workflow" in migrated
        assert "sandbox" in migrated
        assert "agent" in migrated

    def test_migrate_0_9_to_2_0_auto(self, manager):
        """Test migration from 0.9 to 2.0 with auto-detection."""
        # Legacy config without version field
        legacy = {
            "model": "gpt-4",
            "temperature": 0.7,
        }

        migrated = manager.migrate(legacy, to_version="2.0")

        assert migrated["_version"] == "2.0"
        # All sections should be created
        assert "llm" in migrated
        assert "agent" in migrated
        assert "task" in migrated

    def test_migrate_auto_detect_version(self, manager):
        """Test migration with auto-detected version."""
        # Legacy config without version
        legacy = {
            "model": "gpt-4",
            "temperature": 0.7,
        }

        migrated = manager.migrate(legacy, to_version="2.0")

        assert migrated["_version"] == "2.0"

    def test_no_migration_needed(self, manager):
        """Test when no migration is needed."""
        current = {
            "_version": manager.VERSION,
            "llm": {"model": "gpt-4"},
        }

        result = manager.migrate(current, to_version=manager.VERSION)

        assert result["_version"] == manager.VERSION

    def test_get_migration_path(self, manager):
        """Test migration path calculation."""
        # Direct path
        path = manager.get_migration_path("1.0", "1.1")
        assert path == [("1.0", "1.1")]

        # Multi-step path
        path = manager.get_migration_path("0.9", "1.1")
        assert ("0.9", "1.0") in path
        assert ("1.0", "1.1") in path

        # Multi-step path for 0.9 to 2.0
        path = manager.get_migration_path("0.9", "2.0")
        assert len(path) == 1  # Direct migration defined
        assert path[0] == ("0.9", "2.0")

        # Same version returns empty path
        path = manager.get_migration_path("1.0", "1.0")
        assert path == []

    def test_is_compatible(self, manager):
        """Test version compatibility check."""
        # Current version is compatible
        current = {"_version": manager.VERSION}
        assert manager.is_compatible(current) is True

        # All supported versions are compatible
        for version in manager.SUPPORTED_VERSIONS:
            config = {"_version": version}
            assert manager.is_compatible(config) is True

        # Legacy 0.9 is compatible
        legacy = {"model": "gpt-4"}
        assert manager.is_compatible(legacy) is True

    def test_validate_version(self, manager):
        """Test version validation."""
        # Valid versions should not raise
        for version in manager.SUPPORTED_VERSIONS:
            manager._validate_version(version)  # Should not raise

        # Invalid version should raise
        with pytest.raises(InvalidVersionError):
            manager._validate_version("invalid")

        with pytest.raises(InvalidVersionError):
            manager._validate_version("3.0")

    def test_migration_history(self, manager):
        """Test migration history recording."""
        legacy = {"model": "gpt-4"}

        migrated = manager.migrate(legacy, from_version="0.9", to_version="1.1")

        assert "_migration_history" in migrated
        assert len(migrated["_migration_history"]) == 2

        # Check history entries
        for entry in migrated["_migration_history"]:
            assert "from_version" in entry
            assert "to_version" in entry
            assert "timestamp" in entry

        # Verify history order
        history = migrated["_migration_history"]
        assert history[0]["from_version"] == "0.9"
        assert history[0]["to_version"] == "1.0"
        assert history[1]["from_version"] == "1.0"
        assert history[1]["to_version"] == "1.1"

    def test_migration_history_direct(self, manager):
        """Test migration history for direct migration."""
        legacy = {"model": "gpt-4"}

        migrated = manager.migrate(legacy, from_version="0.9", to_version="2.0")

        # Direct migration should record one entry
        assert "_migration_history" in migrated
        assert len(migrated["_migration_history"]) == 1
        assert migrated["_migration_history"][0]["from_version"] == "0.9"
        assert migrated["_migration_history"][0]["to_version"] == "2.0"


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_detect_config_version(self):
        """Test detect_config_version function."""
        config = {"_version": "1.0"}
        assert detect_config_version(config) == "1.0"

    def test_migrate_config(self):
        """Test migrate_config function."""
        legacy = {"model": "gpt-4"}
        migrated = migrate_config(legacy)

        assert migrated["_version"] == "2.0"

    def test_is_config_compatible(self):
        """Test is_config_compatible function."""
        config = {"_version": "2.0"}
        assert is_config_compatible(config) is True


class TestMigrationFunctions:
    """Tests for individual migration functions."""

    @pytest.fixture
    def manager(self):
        """Create a fresh ConfigVersionManager for each test."""
        return ConfigVersionManager()

    def test_migrate_0_9_preserves_unknown_keys(self, manager):
        """Test that unknown keys are preserved during migration."""
        legacy = {
            "model": "gpt-4",
            "custom_key": "custom_value",
            "another_key": 123,
        }

        migrated = manager.migrate(legacy, from_version="0.9", to_version="1.0")

        assert migrated.get("custom_key") == "custom_value"
        assert migrated.get("another_key") == 123

    def test_migrate_1_0_creates_agent_section(self, manager):
        """Test that agent section is created in 1.0 migration."""
        config = {
            "_version": "0.9",
            "model": "gpt-4",
        }

        migrated = manager.migrate(config, from_version="0.9", to_version="1.0")

        assert "agent" in migrated
        assert "search" in migrated["agent"]
        assert migrated["agent"]["search"]["num_drafts"] == 5
        assert "autokaggle" in migrated["agent"]

    def test_migrate_1_1_adds_dag_runtime(self, manager):
        """Test that dag_runtime is added in 1.1 migration."""
        config = {
            "_version": "1.0",
            "llm": {"model": "gpt-4"},
            "run": {"name": "test"},
        }

        migrated = manager.migrate(config, from_version="1.0", to_version="1.1")

        assert "dag_runtime" in migrated["run"]
        dag_runtime = migrated["run"]["dag_runtime"]
        assert dag_runtime["enabled"] is False
        assert dag_runtime["max_inflight_nodes"] == 256

    def test_migrate_1_1_adds_task_section(self, manager):
        """Test that task section is added in 1.1 migration."""
        config = {
            "_version": "1.0",
            "llm": {"model": "gpt-4"},
        }

        migrated = manager.migrate(config, from_version="1.0", to_version="1.1")

        assert "task" in migrated
        assert migrated["task"]["goal"] == "Solve the given data science task."
        assert migrated["task"]["eval_metric"] is None

    def test_migrate_2_0_handles_workspace_base_dir(self, manager):
        """Test that workspace_base_dir is moved in 2.0 migration."""
        config = {
            "_version": "1.1",
            "llm": {"model": "gpt-4"},
            "workflow": {
                "name": "aide",
                "params": {"workspace_base_dir": "/workspace"}
            },
        }

        migrated = manager.migrate(config, from_version="1.1", to_version="2.0")

        # workspace_base_dir should be moved to run.parameters.workspace_dir
        assert "run" in migrated
        assert "parameters" in migrated["run"]
        assert migrated["run"]["parameters"]["workspace_dir"] == "/workspace"


class TestVersionMigrationParameterized:
    """Parameterized tests for version migrations using pytest.mark.parametrize."""

    @pytest.fixture
    def manager(self):
        """Create a fresh ConfigVersionManager for each test."""
        return ConfigVersionManager()

    @pytest.mark.parametrize(
        "from_version,to_version",
        [
            ("0.9", "1.0"),
            ("0.9", "2.0"),
            ("1.0", "2.0"),
            ("1.0", "1.1"),
            ("1.1", "2.0"),
        ],
    )
    def test_migrate_preserves_llm_config(self, manager, from_version, to_version):
        """Test that LLM configuration is preserved during migration."""
        # Create a config that would have LLM settings
        if from_version == "0.9":
            config = {"model": "gpt-4", "temperature": 0.7, "api_key": "sk-xxx"}
        else:
            config = {
                "_version": from_version,
                "llm": {"model": "gpt-4", "temperature": 0.7},
            }

        migrated = manager.migrate(config, from_version=from_version, to_version=to_version)

        # LLM config should be preserved
        assert "llm" in migrated
        assert migrated["llm"]["model"] == "gpt-4"

    @pytest.mark.parametrize(
        "from_version,to_version",
        [
            ("0.9", "1.0"),
            ("0.9", "1.1"),
            ("0.9", "2.0"),
            ("1.0", "1.1"),
            ("1.0", "2.0"),
            ("1.1", "2.0"),
        ],
    )
    def test_migrate_adds_version_field(self, manager, from_version, to_version):
        """Test that migrated config has correct version field."""
        if from_version == "0.9":
            config = {"model": "gpt-4"}
        else:
            config = {"_version": from_version}

        migrated = manager.migrate(config, from_version=from_version, to_version=to_version)

        assert "_version" in migrated
        assert migrated["_version"] == to_version

    @pytest.mark.parametrize(
        "from_version,to_version",
        [
            ("0.9", "1.0"),
            ("0.9", "1.1"),
            ("0.9", "2.0"),
        ],
    )
    def test_migrate_adds_agent_section(self, manager, from_version, to_version):
        """Test that agent section is added during migration from 0.9."""
        config = {"model": "gpt-4"}

        migrated = manager.migrate(config, from_version=from_version, to_version=to_version)

        assert "agent" in migrated
        assert "search" in migrated["agent"]

    @pytest.mark.parametrize(
        "from_version,to_version",
        [
            ("0.9", "1.1"),
            ("0.9", "2.0"),
            ("1.0", "1.1"),
            ("1.0", "2.0"),
        ],
    )
    def test_migrate_adds_task_section(self, manager, from_version, to_version):
        """Test that task section is added in migrations to 1.1+."""
        if from_version == "0.9":
            config = {"model": "gpt-4"}
        else:
            config = {"_version": from_version}

        migrated = manager.migrate(config, from_version=from_version, to_version=to_version)

        # Task section should be present for versions 1.1 and above
        assert "task" in migrated
        assert migrated["task"]["goal"] == "Solve the given data science task."

    @pytest.mark.parametrize(
        "from_version,to_version,expected_path_length",
        [
            ("0.9", "1.0", 1),
            ("0.9", "1.1", 2),
            ("0.9", "2.0", 1),  # Direct migration defined
            ("1.0", "1.1", 1),
            ("1.0", "2.0", 2),
            ("1.1", "2.0", 1),
        ],
    )
    def test_migration_path_length(self, manager, from_version, to_version, expected_path_length):
        """Test that migration path has expected length."""
        path = manager.get_migration_path(from_version, to_version)
        assert len(path) == expected_path_length

    @pytest.mark.parametrize(
        "from_version,to_version",
        [
            ("0.9", "1.0"),
            ("1.0", "1.1"),
            ("1.1", "2.0"),
            ("0.9", "2.0"),
        ],
    )
    def test_migration_history_recorded(self, manager, from_version, to_version):
        """Test that migration history is recorded."""
        if from_version == "0.9":
            config = {"model": "gpt-4"}
        else:
            config = {"_version": from_version}

        migrated = manager.migrate(config, from_version=from_version, to_version=to_version)

        assert "_migration_history" in migrated
        assert len(migrated["_migration_history"]) >= 1

        # All history entries should have required fields
        for entry in migrated["_migration_history"]:
            assert "from_version" in entry
            assert "to_version" in entry
            assert "timestamp" in entry

    @pytest.mark.parametrize(
        "from_version",
        ["0.9", "1.0", "1.1", "2.0"],
    )
    def test_detect_all_supported_versions(self, manager, from_version):
        """Test that all supported versions can be detected."""
        config = {"_version": from_version}
        detected = manager.detect_version(config)
        assert detected == from_version

    @pytest.mark.parametrize(
        "from_version,to_version",
        [
            ("0.9", "1.0"),
            ("0.9", "2.0"),
            ("1.0", "2.0"),
        ],
    )
    def test_migrate_preserves_unknown_keys(self, manager, from_version, to_version):
        """Test that unknown keys are preserved during migration."""
        if from_version == "0.9":
            config = {"model": "gpt-4", "custom_field": "custom_value", "another_field": 123}
        else:
            config = {"_version": from_version, "custom_field": "custom_value", "another_field": 123}

        migrated = manager.migrate(config, from_version=from_version, to_version=to_version)

        assert migrated.get("custom_field") == "custom_value"
        assert migrated.get("another_field") == 123

class TestConfigVersionManagerEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.fixture
    def manager(self):
        """Create a fresh ConfigVersionManager for each test."""
        return ConfigVersionManager()

    def test_unsupported_version_raises_error(self, manager):
        """Test that unsupported versions raise InvalidVersionError."""
        config = {"_version": "0.5"}

        # Unsupported version raises InvalidVersionError during validation
        with pytest.raises(InvalidVersionError):
            manager.migrate(config, from_version="0.5", to_version="2.0")

    def test_invalid_version_raises_error(self, manager):
        """Test that invalid version strings raise InvalidVersionError."""
        with pytest.raises(InvalidVersionError):
            manager._validate_version("invalid.version")

    def test_migrate_backward_path(self, manager):
        """Test migration path calculation for backward direction."""
        config = {"_version": "2.0"}

        # Backward migration should return a path
        path = manager.get_migration_path("2.0", "1.0")
        assert len(path) > 0

    def test_unknown_version_returns_current(self, manager):
        """Test that unknown versions default to current."""
        config = {"_version": "99.0"}
        detected = manager.detect_version(config)

        # Unknown version should return current version with warning
        assert detected == manager.VERSION

    def test_empty_config_defaults_to_current(self, manager):
        """Test that empty config defaults to current version."""
        config = {}
        detected = manager.detect_version(config)

        assert detected == manager.VERSION

    def test_migration_does_not_modify_original(self, manager):
        """Test that migration returns a new dict, not modifying original."""
        legacy = {
            "model": "gpt-4",
            "temperature": 0.7,
        }

        migrated = manager.migrate(legacy, from_version="0.9", to_version="2.0")

        # Original should not have _version
        assert "_version" not in legacy
        # Migrated should have _version
        assert "_version" in migrated
        assert migrated["_version"] == "2.0"


class TestVersionManagerConstants:
    """Tests for version manager class constants."""

    def test_version_constants(self):
        """Test that version constants are correct."""
        assert ConfigVersionManager.VERSION == "2.0"
        assert "0.9" in ConfigVersionManager.SUPPORTED_VERSIONS
        assert "1.0" in ConfigVersionManager.SUPPORTED_VERSIONS
        assert "1.1" in ConfigVersionManager.SUPPORTED_VERSIONS
        assert "2.0" in ConfigVersionManager.SUPPORTED_VERSIONS

    def test_min_compatible_version(self):
        """Test minimum compatible version."""
        assert ConfigVersionManager.MIN_COMPATIBLE_VERSION == "0.9"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
