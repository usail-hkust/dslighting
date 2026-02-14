"""
Progress management for DSLighting CLI operations.

Provides a reusable progress manager using rich for displaying
progress bars and status updates during long-running operations.
"""

from contextlib import contextmanager
from typing import Optional, Any

try:
    from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, BarColumn, TextColumn
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class ProgressManager:
    """Reusable progress manager for CLI operations."""

    def __init__(
        self,
        description: str = "Working...",
        transient: bool = False,
        console=None
    ):
        """
        Initialize the progress manager.

        Args:
            description: Default task description
            transient: Whether progress bars disappear when done
            console: Optional rich console instance
        """
        self.description = description
        self.transient = transient
        self.console = console
        self._progress: Optional[Progress] = None
        self._task_id: Optional[int] = None

    def __enter__(self) -> "ProgressManager":
        """Enter context manager and start progress display."""
        if RICH_AVAILABLE:
            self._progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TimeElapsedColumn(),
                console=self.console,
                transient=self.transient,
            )
            self._progress.__enter__()
            self._task_id = self._progress.add_task(self.description, total=100)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager and stop progress display."""
        if self._progress is not None:
            self._progress.__exit__(exc_type, exc_val, exc_tb)
            self._progress = None
            self._task_id = None

    def update(
        self,
        advance: float = 0,
        description: Optional[str] = None,
        refresh: bool = True,
        **kwargs
    ) -> None:
        """
        Update the current task progress.

        Args:
            advance: Amount to advance the progress bar
            description: New description (optional)
            refresh: Whether to refresh the display
            **kwargs: Additional arguments passed to rich.progress
        """
        if self._progress is not None and self._task_id is not None:
            self._progress.advance(self._task_id, advance=advance)
            if description:
                self._progress.update(
                    self._task_id,
                    description=description,
                    refresh=refresh,
                    **kwargs
                )

    def set_description(self, description: str, refresh: bool = True) -> None:
        """Update the task description."""
        if self._progress is not None and self._task_id is not None:
            self._progress.update(
                self._task_id,
                description=description,
                refresh=refresh
            )

    @contextmanager
    def task(
        self,
        description: str,
        total: float = 100,
        start: bool = True
    ):
        """
        Context manager for a temporary task.

        Args:
            description: Task description
            total: Total value for the progress bar
            start: Whether to start the task immediately

        Yields:
            Task ID for the created task
        """
        if RICH_AVAILABLE and self._progress is not None:
            task_id = self._progress.add_task(description, total=total, start=start)
            try:
                yield task_id
            finally:
                self._progress.remove_task(task_id)
        else:
            # Fallback when rich is not available
            yield None

    def create_task(
        self,
        description: str,
        total: float = 100,
        start: bool = True
    ) -> Optional[int]:
        """
        Create a new task and return its ID.

        Args:
            description: Task description
            total: Total value for the progress bar
            start: Whether to start the task immediately

        Returns:
            Task ID for the created task or None if rich is not available
        """
        if RICH_AVAILABLE and self._progress is not None:
            return self._progress.add_task(description, total=total, start=start)
        return None  # Return None when rich is not available

    def stop_task(self, task_id: int) -> None:
        """
        Stop and remove a task.

        Args:
            task_id: ID of the task to remove
        """
        if RICH_AVAILABLE and self._progress is not None:
            self._progress.remove_task(task_id)

    @property
    def is_active(self) -> bool:
        """Check if the progress manager is currently active."""
        return self._progress is not None and self._progress._running


# Fallback simple progress class when rich is not available
if not RICH_AVAILABLE:

    class _FallbackProgressManager:
        """Fallback progress manager when rich is not installed."""

        def __init__(
            self,
            description: str = "Working...",
            transient: bool = False,
            console=None
        ):
            self.description = description
            self.transient = transient
            self.console = console
            self._task_id = None
            self._completed = 0

        def __enter__(self) -> "ProgressManager":
            print(f"[{self.description}]")
            return self

        def __exit__(self, exc_type, exc_val, exc_tb) -> None:
            print(f"[Done: {self.description}]")

        def update(self, advance: float = 0, description: Optional[str] = None, **kwargs) -> None:
            self._completed += advance
            if description:
                self.description = description
            print(f"[{self.description}] {self._completed}%")

        def set_description(self, description: str, refresh: bool = True) -> None:
            self.description = description

        @contextmanager
        def task(self, description: str, total: float = 100, start: bool = True):
            print(f"[{description}]")
            try:
                yield None
            finally:
                print(f"[Done: {description}]")

        def create_task(self, description: str, total: float = 100, start: bool = True) -> int:
            print(f"[{description}]")
            return 0

        def stop_task(self, task_id: int) -> None:
            pass

        @property
        def is_active(self) -> bool:
            return False
