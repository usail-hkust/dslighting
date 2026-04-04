"""
Tests for CLI progress tracking functionality.

Tests for progress display and tracking features in dslighting CLI.
"""

import time
from io import StringIO
from unittest.mock import Mock, patch, MagicMock

import pytest

from dslighting.cli.progress import (
    ProgressManager,
    RICH_AVAILABLE,
)


class TestProgressManagerInitialization:
    """Tests for ProgressManager initialization."""

    def test_progress_manager_init_default(self):
        """Test ProgressManager initialization with defaults."""
        manager = ProgressManager()
        assert manager.description == "Working..."
        assert manager.transient is False
        assert manager.console is None
        assert manager._progress is None
        assert manager._task_id is None

    def test_progress_manager_init_with_description(self):
        """Test ProgressManager with custom description."""
        manager = ProgressManager(description="Custom task")
        assert manager.description == "Custom task"

    def test_progress_manager_init_transient(self):
        """Test ProgressManager with transient flag."""
        manager = ProgressManager(transient=True)
        assert manager.transient is True

    def test_progress_manager_init_with_console(self):
        """Test ProgressManager with custom console."""
        console = Mock()
        manager = ProgressManager(console=console)
        assert manager.console == console


class TestProgressManagerContextManager:
    """Tests for ProgressManager context manager functionality."""

    def test_progress_manager_enter_without_rich(self):
        """Test entering ProgressManager when rich is not available."""
        if RICH_AVAILABLE:
            pytest.skip("Test only applicable when rich is not available")

        manager = ProgressManager(description="Test")
        result = manager.__enter__()
        assert result == manager

    def test_progress_manager_exit_without_rich(self):
        """Test exiting ProgressManager when rich is not available."""
        if RICH_AVAILABLE:
            pytest.skip("Test only applicable when rich is not available")

        manager = ProgressManager(description="Test")
        manager.__enter__()
        manager.__exit__(None, None, None)
        assert manager._progress is None

    @pytest.mark.skipif(not RICH_AVAILABLE, reason="rich not installed")
    def test_progress_manager_with_rich(self):
        """Test ProgressManager with rich available."""
        manager = ProgressManager(description="Test")
        with manager as m:
            assert m == manager
            assert manager._progress is not None
            assert manager._task_id is not None


class TestProgressManagerUpdate:
    """Tests for ProgressManager update functionality."""

    def test_progress_manager_update_without_rich(self):
        """Test updating progress when rich is not available."""
        if RICH_AVAILABLE:
            pytest.skip("Test only applicable when rich is not available")

        manager = ProgressManager(description="Test")
        manager.update(advance=10)

        # Should not raise any errors
        assert manager._completed == 10

    def test_progress_manager_update_with_description(self):
        """Test updating progress with new description."""
        if RICH_AVAILABLE:
            pytest.skip("Test only when rich is not available")

        manager = ProgressManager(description="Test")
        manager.update(advance=10, description="New description")
        assert manager.description == "New description"


class TestProgressManagerSetDescription:
    """Tests for set_description method."""

    def test_set_description_without_rich(self):
        """Test setting description when rich is not available."""
        if RICH_AVAILABLE:
            pytest.skip("Test only when rich is not available")

        manager = ProgressManager(description="Old description")
        manager.set_description("New description")
        assert manager.description == "New description"


class TestProgressManagerTask:
    """Tests for task context manager."""

    def test_task_context_manager_without_rich(self):
        """Test task context manager when rich is not available."""
        if RICH_AVAILABLE:
            pytest.skip("Test only when rich is not available")

        manager = ProgressManager(description="Main task")

        with manager.task("Subtask", total=100) as task_id:
            # Task should execute without errors
            assert task_id is None

    @pytest.mark.skipif(not RICH_AVAILABLE, reason="rich not installed")
    def test_task_context_manager_with_rich(self):
        """Test task context manager with rich available."""
        manager = ProgressManager(description="Main task")

        # Need to be in context manager for tasks to work
        with manager:
            with manager.task("Subtask", total=100) as task_id:
                # Task should be created
                assert task_id is not None


class TestProgressManagerCreateTask:
    """Tests for create_task method."""

    def test_create_task_without_rich(self):
        """Test creating task when rich is not available."""
        if RICH_AVAILABLE:
            pytest.skip("Test only when rich is not available")

        manager = ProgressManager(description="Main task")
        task_id = manager.create_task("Subtask", total=100)

        # Should return None when rich is not available
        assert task_id is None or task_id == 0


class TestProgressManagerStopTask:
    """Tests for stop_task method."""

    def test_stop_task_without_rich(self):
        """Test stopping task when rich is not available."""
        if RICH_AVAILABLE:
            pytest.skip("Test only when rich is not available")

        manager = ProgressManager(description="Main task")
        manager.stop_task(0)

        # Should not raise any errors


class TestProgressManagerIsActive:
    """Tests for is_active property."""

    def test_is_active_without_rich(self):
        """Test is_active when rich is not available."""
        if RICH_AVAILABLE:
            pytest.skip("Test only when rich is not available")

        manager = ProgressManager(description="Test")
        assert manager.is_active is False

    @pytest.mark.skipif(not RICH_AVAILABLE, reason="rich not installed")
    def test_is_active_with_rich(self):
        """Test is_active with rich available."""
        manager = ProgressManager(description="Test")
        # Progress is not active until context manager is entered
        assert manager.is_active is False

        with manager:
            # Progress object should be created
            assert manager._progress is not None

        # Progress should be cleaned up after exiting
        assert manager._progress is None


class TestProgressManagerIntegration:
    """Integration tests for ProgressManager."""

    def test_progress_manager_lifecycle_without_rich(self):
        """Test complete lifecycle when rich is not available."""
        if RICH_AVAILABLE:
            pytest.skip("Test only when rich is not available")

        manager = ProgressManager(description="Test task")

        with manager:
            manager.update(advance=25)
            manager.set_description("Updated description")

            with manager.task("Subtask 1"):
                pass

            task_id = manager.create_task("Subtask 2")
            if task_id is not None:
                manager.stop_task(task_id)

        # Should complete without errors
        assert True

    @pytest.mark.skipif(not RICH_AVAILABLE, reason="rich not installed")
    def test_progress_manager_with_multiple_tasks(self):
        """Test ProgressManager with multiple tasks."""
        manager = ProgressManager(description="Main task")

        with manager:
            # Create multiple tasks
            task1 = manager.create_task("Task 1", total=100)
            task2 = manager.create_task("Task 2", total=100)

            # Update progress
            manager.update(advance=50)

            # Clean up tasks
            if task1:
                manager.stop_task(task1)
            if task2:
                manager.stop_task(task2)

    @pytest.mark.skipif(not RICH_AVAILABLE, reason="rich not installed")
    def test_progress_manager_nested_tasks(self):
        """Test ProgressManager with nested tasks."""
        manager = ProgressManager(description="Main task")

        with manager:
            with manager.task("Outer task"):
                manager.update(advance=25)
                with manager.task("Inner task"):
                    manager.update(advance=25)
                manager.update(advance=25)


class TestRichAvailability:
    """Tests for RICH_AVAILABLE flag."""

    def test_rich_available_is_bool(self):
        """Test that RICH_AVAILABLE is a boolean."""
        assert isinstance(RICH_AVAILABLE, bool)

    def test_progress_manager_works_regardless_of_rich(self):
        """Test that ProgressManager works regardless of rich availability."""
        manager = ProgressManager(description="Test")

        # Should be able to create without errors
        assert manager is not None

        # Should be able to use as context manager
        with manager:
            manager.update(advance=10)


class TestProgressManagerEdgeCases:
    """Tests for edge cases and error handling."""

    def test_progress_manager_empty_description(self):
        """Test ProgressManager with empty description."""
        manager = ProgressManager(description="")
        assert manager.description == ""

    def test_progress_manager_unicode_description(self):
        """Test ProgressManager with unicode description."""
        manager = ProgressManager(description="Test 🚀")
        assert manager.description == "Test 🚀"

    def test_progress_manager_very_long_description(self):
        """Test ProgressManager with very long description."""
        description = "Test " * 100
        manager = ProgressManager(description=description)
        assert manager.description == description

    def test_progress_manager_zero_advance(self):
        """Test updating with zero advance."""
        manager = ProgressManager(description="Test")
        manager.update(advance=0)

        # Should not raise errors
        assert True

    def test_progress_manager_negative_advance(self):
        """Test updating with negative advance."""
        if RICH_AVAILABLE:
            pytest.skip("Rich may handle negative advances differently")

        manager = ProgressManager(description="Test")
        manager.update(advance=-10)

        # Should handle gracefully
        assert True
