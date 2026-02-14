"""
Configuration File Watching and Hot Reload System.

This module provides configuration file monitoring with automatic reload,
debouncing, and callback notifications. It supports both hot reload (in-place
updates) and cold reload (full restart) modes.

Features:
- Watch multiple configuration files simultaneously
- Support YAML and JSON formats
- Debounce handling to avoid frequent reloads
- Thread-safe operations
- Hot reload and cold reload modes
- Callback mechanism for change notifications
- Integration with ConfigBuilder

Example Usage:
    >>> from dslighting.core.config.watch import ConfigWatcher
    >>> def on_config_changed(new_config):
    ...     print(f"Config updated: {new_config}")
    >>> watcher = ConfigWatcher(debounce_seconds=1.0)
    >>> watcher.watch_file("/path/to/config.yaml", on_config_changed)
    >>> watcher.start()  # Starts watching in background
"""

import json
import logging
import os
import threading
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
import queue

logger = logging.getLogger(__name__)


class ReloadMode(Enum):
    """Configuration reload modes."""
    HOT = "hot"      # In-place update without restarting
    COLD = "cold"    # Full restart required


class FileFormat(Enum):
    """Supported configuration file formats."""
    YAML = "yaml"
    JSON = "json"
    UNKNOWN = "unknown"


@dataclass
class WatchedFile:
    """Represents a watched configuration file."""
    file_path: str
    format: FileFormat
    last_modified: float
    last_content_hash: str
    last_content: Optional[Dict[str, Any]] = None
    callback: Optional[Callable[[Dict[str, Any], "WatchedFile"], None]] = None
    reload_mode: ReloadMode = ReloadMode.HOT
    enabled: bool = True
    error_count: int = 0
    last_error: Optional[str] = None

    def update_content(
        self,
        content: Dict[str, Any],
        modified_time: float,
        content_hash: str
    ) -> None:
        """Update file content information."""
        self.last_content = content
        self.last_modified = modified_time
        self.last_content_hash = content_hash
        self.error_count = 0
        self.last_error = None


@dataclass
class ReloadEvent:
    """Represents a configuration reload event."""
    file_path: str
    event_type: str  # "modified", "added", "removed"
    timestamp: datetime
    reload_mode: ReloadMode
    success: bool
    error_message: Optional[str] = None
    new_content: Optional[Dict[str, Any]] = None
    old_content: Optional[Dict[str, Any]] = None


class ConfigWatcherError(Exception):
    """Base exception for config watcher errors."""
    pass


class WatcherNotStartedError(ConfigWatcherError):
    """Raised when watcher is accessed before starting."""
    pass


class InvalidFileError(ConfigWatcherError):
    """Raised when a file path is invalid."""
    pass


class ConfigWatcher:
    """
    Configuration file watcher with hot reload support.

    This class monitors configuration files for changes and automatically
    reloads them when modifications are detected. It supports:
    - Multiple file watching
    - Debounced reloads
    - Thread-safe operations
    - Hot and cold reload modes
    - Change callbacks

    Attributes:
        debounce_seconds: Minimum time between reloads (debounce).
        poll_interval_seconds: File poll interval in seconds.
        auto_start: Whether to auto-start watching on first file add.
        max_retry_count: Maximum retries on reload failure.
    """

    def __init__(
        self,
        debounce_seconds: float = 1.0,
        poll_interval_seconds: float = 0.5,
        auto_start: bool = False,
        max_retry_count: int = 3,
    ) -> None:
        """
        Initialize the configuration watcher.

        Args:
            debounce_seconds: Minimum seconds between reloads for same file.
            poll_interval_seconds: File poll interval for non-watchdog systems.
            auto_start: Whether to auto-start when first file is added.
            max_retry_count: Maximum retry attempts on reload failure.
        """
        self.debounce_seconds = debounce_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self.auto_start = auto_start
        self.max_retry_count = max_retry_count

        # Thread-safe data structures
        self._lock = threading.RLock()
        self._watched_files: Dict[str, WatchedFile] = {}
        self._event_queue: queue.Queue = queue.Queue()
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)

        # State
        self._running = False
        self._watch_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Statistics
        self._stats = {
            "total_reloads": 0,
            "successful_reloads": 0,
            "failed_reloads": 0,
            "last_reload_time": None,
        }

    @property
    def is_running(self) -> bool:
        """Check if the watcher is running."""
        return self._running

    @property
    def watched_files(self) -> List[str]:
        """Get list of watched file paths."""
        with self._lock:
            return list(self._watched_files.keys())

    @property
    def stats(self) -> Dict[str, Any]:
        """Get watcher statistics."""
        with self._lock:
            return {
                **self._stats,
                "watched_count": len(self._watched_files),
                "running": self._running,
            }

    # =====================================================================
    # File Management
    # =====================================================================

    def watch_file(
        self,
        file_path: str,
        callback: Optional[Callable[[Dict[str, Any], "WatchedFile"], None]] = None,
        reload_mode: ReloadMode = ReloadMode.HOT,
        immediate_load: bool = True,
    ) -> WatchedFile:
        """
        Add a file to the watch list.

        Args:
            file_path: Path to the configuration file.
            callback: Optional callback on config change.
            reload_mode: Reload mode (hot or cold).
            immediate_load: Whether to load the file immediately.

        Returns:
            WatchedFile object.

        Raises:
            InvalidFileError: If file path is invalid.
        """
        file_path = os.path.abspath(file_path)

        if not os.path.exists(file_path):
            raise InvalidFileError(f"File not found: {file_path}")

        format_type = self._detect_format(file_path)

        with self._lock:
            # Check if already watching
            if file_path in self._watched_files:
                logger.info(f"File already being watched: {file_path}")
                return self._watched_files[file_path]

            # Read initial content
            modified_time = os.path.getmtime(file_path)
            content, content_hash = self._read_and_hash_file(file_path, format_type)

            # Create watched file
            watched = WatchedFile(
                file_path=file_path,
                format=format_type,
                last_modified=modified_time,
                last_content_hash=content_hash,
                last_content=content,
                callback=callback,
                reload_mode=reload_mode,
            )
            self._watched_files[file_path] = watched

            # Register callback if provided
            if callback:
                self._callbacks[file_path].append(callback)

            logger.info(f"Added file to watch: {file_path} ({format_type.value})")

            # Auto-start if enabled
            if self.auto_start and not self._running:
                self.start()

            return watched

    def unwatch_file(self, file_path: str) -> bool:
        """
        Remove a file from the watch list.

        Args:
            file_path: Path to the configuration file.

        Returns:
            True if file was removed, False if not found.
        """
        file_path = os.path.abspath(file_path)

        with self._lock:
            if file_path not in self._watched_files:
                return False

            del self._watched_files[file_path]
            if file_path in self._callbacks:
                del self._callbacks[file_path]

            logger.info(f"Removed file from watch: {file_path}")
            return True

    def update_callback(
        self,
        file_path: str,
        callback: Callable[[Dict[str, Any], "WatchedFile"], None]
    ) -> bool:
        """
        Update the callback for a watched file.

        Args:
            file_path: Path to the configuration file.
            callback: New callback function.

        Returns:
            True if updated, False if file not found.
        """
        file_path = os.path.abspath(file_path)

        with self._lock:
            if file_path not in self._watched_files:
                return False

            self._watched_files[file_path].callback = callback
            self._callbacks[file_path] = [callback]
            return True

    def add_callback(
        self,
        file_path: str,
        callback: Callable[[Dict[str, Any], "WatchedFile"], None]
    ) -> bool:
        """
        Add an additional callback for a watched file.

        Args:
            file_path: Path to the configuration file.
            callback: Callback function to add.

        Returns:
            True if added, False if file not found.
        """
        file_path = os.path.abspath(file_path)

        with self._lock:
            if file_path not in self._watched_files:
                return False

            self._watched_files[file_path].callback = callback
            self._callbacks[file_path].append(callback)
            return True

    # =====================================================================
    # Watch Control
    # =====================================================================

    def start(self) -> None:
        """Start watching files in a background thread."""
        with self._lock:
            if self._running:
                logger.warning("Watcher is already running")
                return

            self._stop_event.clear()
            self._running = True
            self._watch_thread = threading.Thread(
                target=self._watch_loop,
                name="ConfigWatcher",
                daemon=True
            )
            self._watch_thread.start()
            logger.info("ConfigWatcher started")

    def stop(self) -> None:
        """Stop watching files."""
        with self._lock:
            if not self._running:
                return

            self._stop_event.set()
            self._running = False

            if self._watch_thread and self._watch_thread.is_alive():
                self._watch_thread.join(timeout=2.0)

            self._watch_thread = None
            logger.info("ConfigWatcher stopped")

    def pause(self) -> None:
        """Pause watching without stopping the thread."""
        self._stop_event.set()

    def resume(self) -> None:
        """Resume watching after pause."""
        self._stop_event.clear()

    def wait_for_reload(
        self,
        timeout: Optional[float] = None,
        file_path: Optional[str] = None
    ) -> bool:
        """
        Wait for a reload event.

        Args:
            timeout: Maximum time to wait in seconds.
            file_path: Optional specific file to wait for.

        Returns:
            True if event received, False on timeout.
        """
        try:
            event = self._event_queue.get(timeout=timeout)
            if file_path is None or event.file_path == file_path:
                return True
            # Put back if not our file
            self._event_queue.put(event)
            return False
        except queue.Empty:
            return False

    # =====================================================================
    # Manual Reload
    # =====================================================================

    def reload_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Force reload a specific file.

        Args:
            file_path: Path to the configuration file.

        Returns:
            Tuple of (success, error_message).
        """
        file_path = os.path.abspath(file_path)

        with self._lock:
            if file_path not in self._watched_files:
                return False, f"File not being watched: {file_path}"

            watched = self._watched_files[file_path]

        try:
            new_content, new_hash = self._read_and_hash_file(file_path, watched.format)

            with self._lock:
                old_content = watched.last_content
                watched.update_content(new_content, watched.last_modified, new_hash)

            # Create event
            event = ReloadEvent(
                file_path=file_path,
                event_type="manual",
                timestamp=datetime.utcnow(),
                reload_mode=watched.reload_mode,
                success=True,
                new_content=new_content,
                old_content=old_content,
            )
            self._event_queue.put(event)
            self._stats["total_reloads"] += 1
            self._stats["successful_reloads"] += 1
            self._stats["last_reload_time"] = datetime.utcnow().isoformat()

            # Call callbacks
            self._invoke_callbacks(watched, new_content, old_content)

            logger.info(f"Manual reload completed for: {file_path}")
            return True, None

        except Exception as e:
            logger.error(f"Manual reload failed for {file_path}: {e}")
            self._stats["failed_reloads"] += 1

            with self._lock:
                watched.error_count += 1
                watched.last_error = str(e)

            return False, str(e)

    def reload_all(self) -> Dict[str, Tuple[bool, str]]:
        """
        Reload all watched files.

        Returns:
            Dictionary mapping file paths to (success, error) tuples.
        """
        results = {}
        for file_path in list(self._watched_files.keys()):
            success, error = self.reload_file(file_path)
            results[file_path] = (success, error or "")
        return results

    # =====================================================================
    # Global Callbacks
    # =====================================================================

    def on_reload(
        self,
        callback: Callable[[ReloadEvent], None]
    ) -> None:
        """
        Register a global reload event callback.

        Args:
            callback: Function to call on each reload event.
        """
        with self._lock:
            self._callbacks["_global"].append(callback)

    def on_reload_success(
        self,
        callback: Callable[[ReloadEvent], None]
    ) -> None:
        """
        Register a callback for successful reloads.

        Args:
            callback: Function to call on successful reload.
        """
        with self._lock:
            self._callbacks["_success"].append(callback)

    def on_reload_failure(
        self,
        callback: Callable[[ReloadEvent], None]
    ) -> None:
        """
        Register a callback for failed reloads.

        Args:
            callback: Function to call on failed reload.
        """
        with self._lock:
            self._callbacks["_failure"].append(callback)

    # =====================================================================
    # Integration with ConfigBuilder
    # =====================================================================

    def integrate_with_builder(
        self,
        builder,
        config_key: str = "config"
    ) -> None:
        """
        Integrate watcher with a ConfigBuilder instance.

        This sets up automatic config reloading through the builder.

        Args:
            builder: ConfigBuilder instance.
            config_key: Attribute name for config on builder.
        """
        def reload_callback(content: Dict[str, Any], watched: WatchedFile) -> None:
            """Callback to reload config via builder."""
            try:
                new_config = builder.load_config_from_dict(content)
                if hasattr(builder, config_key):
                    setattr(builder, config_key, new_config)
                logger.info(f"Config reloaded via builder for: {watched.file_path}")
            except Exception as e:
                logger.error(f"Failed to reload config via builder: {e}")

        # Add this callback to all watched files
        with self._lock:
            for watched in self._watched_files.values():
                self.add_callback(watched.file_path, reload_callback)

        logger.info(f"ConfigWatcher integrated with ConfigBuilder")

    # =====================================================================
    # Internal Methods
    # =====================================================================

    def _watch_loop(self) -> None:
        """Background watch loop."""
        while not self._stop_event.is_set():
            try:
                self._check_all_files()
            except Exception as e:
                logger.error(f"Error in watch loop: {e}")

            # Wait for poll interval or stop event
            self._stop_event.wait(self.poll_interval_seconds)

    def _check_all_files(self) -> None:
        """Check all watched files for changes."""
        with self._lock:
            files_to_check = [
                (path, watched)
                for path, watched in self._watched_files.items()
                if watched.enabled
            ]

        for file_path, watched in files_to_check:
            try:
                self._check_file(file_path, watched)
            except Exception as e:
                logger.error(f"Error checking file {file_path}: {e}")
                watched.error_count += 1
                watched.last_error = str(e)

    def _check_file(self, file_path: str, watched: WatchedFile) -> None:
        """Check a single file for changes."""
        if not os.path.exists(file_path):
            logger.warning(f"Watched file deleted: {file_path}")
            return

        # Check modification time
        current_modified = os.path.getmtime(file_path)

        # Debounce: skip if too soon after last change
        time_since_modified = current_modified - watched.last_modified
        if time_since_modified < self.debounce_seconds:
            return

        # Check content hash
        new_content, new_hash = self._read_and_hash_file(file_path, watched.format)

        if new_hash != watched.last_content_hash:
            self._trigger_reload(file_path, watched, new_content, new_hash, current_modified)

    def _trigger_reload(
        self,
        file_path: str,
        watched: WatchedFile,
        new_content: Dict[str, Any],
        new_hash: str,
        modified_time: float
    ) -> None:
        """Trigger a configuration reload."""
        old_content = watched.last_content

        # Update watched file state
        with self._lock:
            watched.update_content(new_content, modified_time, new_hash)

        # Create event
        event = ReloadEvent(
            file_path=file_path,
            event_type="modified",
            timestamp=datetime.utcnow(),
            reload_mode=watched.reload_mode,
            success=True,
            new_content=new_content,
            old_content=old_content,
        )
        self._event_queue.put(event)

        # Update stats
        self._stats["total_reloads"] += 1
        self._stats["successful_reloads"] += 1
        self._stats["last_reload_time"] = datetime.utcnow().isoformat()

        # Invoke callbacks
        self._invoke_callbacks(watched, new_content, old_content)

        logger.info(f"Config reloaded: {file_path}")

    def _invoke_callbacks(
        self,
        watched: WatchedFile,
        new_content: Dict[str, Any],
        old_content: Optional[Dict[str, Any]]
    ) -> None:
        """Invoke all registered callbacks for a config change."""
        # File-specific callbacks
        file_callbacks = self._callbacks.get(watched.file_path, [])

        # Global callbacks
        global_callbacks = self._callbacks.get("_global", [])
        success_callbacks = self._callbacks.get("_success", [])
        failure_callbacks = self._callbacks.get("_failure", [])

        # Prepare event
        event = ReloadEvent(
            file_path=watched.file_path,
            event_type="modified",
            timestamp=datetime.utcnow(),
            reload_mode=watched.reload_mode,
            success=True,
            new_content=new_content,
            old_content=old_content,
        )

        # Invoke file-specific callback first
        if watched.callback:
            try:
                watched.callback(new_content, watched)
            except Exception as e:
                logger.error(f"Error in file callback: {e}")
                event.success = False
                event.error_message = str(e)

        # Invoke other callbacks
        for callback in file_callbacks + global_callbacks:
            if callback != watched.callback:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in callback: {e}")

        # Success/failure callbacks
        if event.success:
            for callback in success_callbacks:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in success callback: {e}")
        else:
            for callback in failure_callbacks:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in failure callback: {e}")

    def _detect_format(self, file_path: str) -> FileFormat:
        """Detect file format from extension."""
        ext = Path(file_path).suffix.lower()
        if ext in (".yaml", ".yml"):
            return FileFormat.YAML
        elif ext == ".json":
            return FileFormat.JSON
        else:
            return FileFormat.UNKNOWN

    def _read_and_hash_file(
        self,
        file_path: str,
        format_type: FileFormat
    ) -> Tuple[Dict[str, Any], str]:
        """
        Read a configuration file and compute its hash.

        Args:
            file_path: Path to the configuration file.
            format_type: Detected file format.

        Returns:
            Tuple of (parsed_content, content_hash).

        Raises:
            InvalidFileError: If file cannot be parsed.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content_str = f.read()

        # Compute hash
        content_hash = hashlib.md5(content_str.encode("utf-8")).hexdigest()

        # Parse content
        if format_type == FileFormat.YAML:
            import yaml
            try:
                content = yaml.safe_load(content_str) or {}
            except yaml.YAMLError as e:
                raise InvalidFileError(f"Invalid YAML in {file_path}: {e}")

        elif format_type == FileFormat.JSON:
            try:
                content = json.loads(content_str)
            except json.JSONDecodeError as e:
                raise InvalidFileError(f"Invalid JSON in {file_path}: {e}")

        else:
            # Try YAML first, then JSON
            import yaml
            try:
                content = yaml.safe_load(content_str) or {}
            except yaml.YAMLError:
                try:
                    content = json.loads(content_str)
                except json.JSONDecodeError as e:
                    raise InvalidFileError(f"Cannot parse {file_path}: {e}")

        return content, content_hash

    def __enter__(self) -> "ConfigWatcher":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()

    def __del__(self) -> None:
        """Destructor to ensure watcher is stopped."""
        if self._running:
            self.stop()


class ConfigWatcherManager:
    """
    Manager for multiple configuration watchers.

    This class provides a centralized way to manage multiple ConfigWatcher
    instances for different configuration sets.
    """

    _instance: Optional["ConfigWatcherManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ConfigWatcherManager":
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize the manager."""
        if self._initialized:
            return

        self._watchers: Dict[str, ConfigWatcher] = {}
        self._lock = threading.RLock()
        self._initialized = True

    def create_watcher(
        self,
        name: str,
        **kwargs
    ) -> ConfigWatcher:
        """
        Create a new named watcher.

        Args:
            name: Unique name for the watcher.
            **kwargs: ConfigWatcher constructor arguments.

        Returns:
            Created ConfigWatcher instance.
        """
        with self._lock:
            if name in self._watchers:
                raise ValueError(f"Watcher '{name}' already exists")

            watcher = ConfigWatcher(**kwargs)
            self._watchers[name] = watcher
            return watcher

    def get_watcher(self, name: str) -> Optional[ConfigWatcher]:
        """
        Get a watcher by name.

        Args:
            name: Name of the watcher.

        Returns:
            ConfigWatcher instance or None if not found.
        """
        with self._lock:
            return self._watchers.get(name)

    def remove_watcher(self, name: str) -> bool:
        """
        Remove a watcher.

        Args:
            name: Name of the watcher.

        Returns:
            True if removed, False if not found.
        """
        with self._lock:
            if name not in self._watchers:
                return False

            watcher = self._watchers[name]
            if watcher.is_running:
                watcher.stop()

            del self._watchers[name]
            return True

    def stop_all(self) -> None:
        """Stop all watchers."""
        with self._lock:
            for watcher in self._watchers.values():
                if watcher.is_running:
                    watcher.stop()

    def list_watchers(self) -> List[str]:
        """List all watcher names."""
        with self._lock:
            return list(self._watchers.keys())


# Global watcher manager instance
watcher_manager = ConfigWatcherManager()


def get_watcher_manager() -> ConfigWatcherManager:
    """
    Get the global watcher manager instance.

    Returns:
        Global ConfigWatcherManager instance.
    """
    return watcher_manager


def watch_config(
    file_path: str,
    callback: Optional[Callable[[Dict[str, Any], "WatchedFile"], None]] = None,
    **kwargs
) -> ConfigWatcher:
    """
    Convenience function to create and start a watcher for a config file.

    Args:
        file_path: Path to the configuration file.
        callback: Optional callback on config change.
        **kwargs: Additional ConfigWatcher arguments.

    Returns:
        ConfigWatcher instance.
    """
    watcher = ConfigWatcher(**kwargs)
    watcher.watch_file(file_path, callback)
    watcher.start()
    return watcher


__all__ = [
    # Main classes
    "ConfigWatcher",
    "ConfigWatcherManager",
    # Supporting classes
    "WatchedFile",
    "ReloadEvent",
    "FileFormat",
    "ReloadMode",
    # Exceptions
    "ConfigWatcherError",
    "WatcherNotStartedError",
    "InvalidFileError",
    # Convenience functions
    "get_watcher_manager",
    "watch_config",
]
