"""
DSLighting 2.0 - Checkpoint Mechanism

This module provides workflow checkpoint functionality for saving and restoring
workflow states with support for multiple storage backends.

Features:
- Save and restore workflow states
- Multiple storage backends (local filesystem, cloud storage)
- Support for different serializers (pickle, json)
- Thread-safe operations
- Automatic checkpoint cleanup
- Checkpoint metadata management

Usage:
    ```python
    from dslighting.checkpoint import CheckpointManager, CheckpointMetadata

    # Initialize checkpoint manager
    manager = CheckpointManager(checkpoint_dir="./checkpoints")

    # Save a checkpoint
    checkpoint = manager.save(
        workflow_id="workflow_001",
        state={"step": 5, "data": {"accuracy": 0.95}},
        step=5,
        description="After training epoch 5"
    )

    # Load the latest checkpoint
    restored = manager.load_latest("workflow_001")

    # List all checkpoints for a workflow
    checkpoints = manager.list_checkpoints("workflow_001")

    # Clean up old checkpoints
    manager.cleanup("workflow_001", keep=3)
    ```
"""

import json
import os
import pickle
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


# Type aliases
PathType = Union[str, Path]
TimestampType = datetime


class CheckpointError(Exception):
    """Base exception for checkpoint-related errors.

    Attributes:
        error_code: Unique error code in format 'CHK-XXX'.
        message: Human-readable error message.
        details: Additional error details (optional).
        suggestion: Actionable suggestion for resolving (optional).
        cause: The underlying exception that caused this error (optional).
    """

    error_code: str = "CHK-000"

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        self.message = message or "An unspecified checkpoint error occurred."
        self.error_code = error_code if error_code is not None else type(self).error_code
        self.details = details or {}
        self.suggestion = suggestion
        self.cause = cause
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return formatted error string."""
        if self.details:
            details_str = ", ".join(f"{k}={v!r}" for k, v in self.details.items())
            return f"[{self.error_code}] {self.message} | Details: {details_str}"
        return f"[{self.error_code}] {self.message}"

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code!r}, "
            f"details={self.details!r}"
            ")"
        )


class InvalidCheckpointKeyError(CheckpointError):
    """Raised when a checkpoint key format is invalid."""

    error_code: str = "CHK-001"

    def __init__(
        self,
        key: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        msg = message or f"Invalid checkpoint key format: '{key}'. Expected format: 'workflow_id/checkpoint_id'."
        super().__init__(
            message=msg,
            error_code=self.error_code,
            details={"key": key, **(details or {})},
            suggestion="Ensure the key contains a workflow_id and checkpoint_id separated by '/'."
        )


class CheckpointWriteError(CheckpointError):
    """Raised when writing a checkpoint fails."""

    error_code: str = "CHK-002"

    def __init__(
        self,
        key: str,
        cause: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=f"Failed to write checkpoint: '{key}'",
            error_code=self.error_code,
            details={"key": key, **(details or {})},
            suggestion="Check that the storage directory is writable and has sufficient space.",
            cause=cause
        )


class CheckpointReadError(CheckpointError):
    """Raised when reading a checkpoint fails."""

    error_code: str = "CHK-003"

    def __init__(
        self,
        key: str,
        cause: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=f"Failed to read checkpoint: '{key}'",
            error_code=self.error_code,
            details={"key": key, **(details or {})},
            suggestion="Verify that the checkpoint exists and the file is accessible.",
            cause=cause
        )


class CheckpointDeleteError(CheckpointError):
    """Raised when deleting a checkpoint fails."""

    error_code: str = "CHK-004"

    def __init__(
        self,
        key: str,
        cause: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=f"Failed to delete checkpoint: '{key}'",
            error_code=self.error_code,
            details={"key": key, **(details or {})},
            suggestion="Check that the checkpoint exists and the file is not locked.",
            cause=cause
        )


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def write(self, key: str, data: bytes) -> bool:
        """Write data to storage.

        Returns:
            True if write succeeds.
        """
        raise NotImplementedError("Subclasses must implement write().")

    @abstractmethod
    def read(self, key: str) -> Optional[bytes]:
        """Read data from storage."""
        raise NotImplementedError("Subclasses must implement read().")

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete data from storage.

        Returns:
            True if delete succeeds.
        """
        raise NotImplementedError("Subclasses must implement delete().")

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in storage."""
        raise NotImplementedError("Subclasses must implement exists().")

    @abstractmethod
    def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys with optional prefix."""
        raise NotImplementedError("Subclasses must implement list_keys().")

    @abstractmethod
    def get_size(self, key: str) -> int:
        """Get the size of stored data in bytes."""
        raise NotImplementedError("Subclasses must implement get_size().")

    @abstractmethod
    def get_metadata_path(self, key: str) -> str:
        """Get the path for metadata file."""
        raise NotImplementedError("Subclasses must implement get_metadata_path().")


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend."""

    def __init__(self, base_dir: PathType):
        """Initialize local storage backend.

        Args:
            base_dir: Base directory for storing checkpoints.
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_checkpoint_dir(self, workflow_id: str) -> Path:
        """Get the directory for a specific workflow."""
        return self.base_dir / workflow_id

    def _ensure_workflow_dir(self, workflow_id: str) -> Path:
        """Ensure workflow directory exists."""
        workflow_dir = self._get_checkpoint_dir(workflow_id)
        workflow_dir.mkdir(parents=True, exist_ok=True)
        return workflow_dir

    def _parse_key(self, key: str) -> tuple[str, str]:
        """Parse a checkpoint key into workflow_id and checkpoint_id.

        Args:
            key: Checkpoint key in format 'workflow_id/checkpoint_id'.

        Returns:
            Tuple of (workflow_id, checkpoint_id).

        Raises:
            InvalidCheckpointKeyError: If key format is invalid.
        """
        parts = key.split("/", 1)
        if len(parts) != 2:
            raise InvalidCheckpointKeyError(key)
        return parts[0], parts[1]

    def write(self, key: str, data: bytes) -> bool:
        """Write data to local filesystem.

        Args:
            key: Checkpoint key in format 'workflow_id/checkpoint_id'.
            data: Data bytes to write.

        Returns:
            True if write operation succeeds.

        Raises:
            InvalidCheckpointKeyError: If key format is invalid.
            CheckpointWriteError: If write operation fails.
        """
        workflow_id, checkpoint_id = self._parse_key(key)

        try:
            checkpoint_dir = self._ensure_workflow_dir(workflow_id)
            checkpoint_path = checkpoint_dir / checkpoint_id
            checkpoint_path.write_bytes(data)
            return True
        except (OSError, IOError) as e:
            raise CheckpointWriteError(key, cause=e) from e

    def read(self, key: str) -> bytes:
        """Read data from local filesystem.

        Args:
            key: Checkpoint key in format 'workflow_id/checkpoint_id'.

        Returns:
            Data bytes.

        Raises:
            InvalidCheckpointKeyError: If key format is invalid.
            CheckpointReadError: If read operation fails or checkpoint does not exist.
        """
        workflow_id, checkpoint_id = self._parse_key(key)
        checkpoint_path = self._get_checkpoint_dir(workflow_id) / checkpoint_id

        try:
            if not checkpoint_path.exists():
                raise CheckpointReadError(
                    key,
                    details={"reason": "checkpoint_not_found"}
                )
            return checkpoint_path.read_bytes()
        except (OSError, IOError) as e:
            raise CheckpointReadError(key, cause=e) from e

    def delete(self, key: str) -> bool:
        """Delete data from local filesystem.

        Args:
            key: Checkpoint key in format 'workflow_id/checkpoint_id'.

        Returns:
            True if delete operation succeeds.

        Raises:
            InvalidCheckpointKeyError: If key format is invalid.
            CheckpointDeleteError: If delete operation fails.
        """
        workflow_id, checkpoint_id = self._parse_key(key)
        checkpoint_path = self._get_checkpoint_dir(workflow_id) / checkpoint_id

        try:
            if not checkpoint_path.exists():
                raise CheckpointDeleteError(
                    key,
                    details={"reason": "checkpoint_not_found"}
                )
            checkpoint_path.unlink()
            return True
        except (OSError, IOError) as e:
            raise CheckpointDeleteError(key, cause=e) from e

    def exists(self, key: str) -> bool:
        """Check if key exists in local filesystem.

        Args:
            key: Checkpoint key in format 'workflow_id/checkpoint_id'.

        Returns:
            True if checkpoint exists.

        Raises:
            InvalidCheckpointKeyError: If key format is invalid.
        """
        workflow_id, checkpoint_id = self._parse_key(key)
        checkpoint_path = self._get_checkpoint_dir(workflow_id) / checkpoint_id
        return checkpoint_path.exists()

    def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys in local filesystem.

        Args:
            prefix: Optional prefix to filter keys (e.g., 'workflow_id/').

        Returns:
            List of checkpoint keys.
        """
        keys = []
        if prefix:
            parts = prefix.split("/", 1)
            if len(parts) == 2:
                workflow_id = parts[0]
                workflow_dir = self._get_checkpoint_dir(workflow_id)
                if workflow_dir.exists():
                    for f in workflow_dir.iterdir():
                        if f.is_file():
                            keys.append(f"{workflow_id}/{f.name}")
            else:
                if self.base_dir.exists():
                    for d in self.base_dir.iterdir():
                        if d.is_dir():
                            for f in d.iterdir():
                                if f.is_file():
                                    keys.append(f"{d.name}/{f.name}")
        else:
            if self.base_dir.exists():
                for d in self.base_dir.iterdir():
                    if d.is_dir():
                        for f in d.iterdir():
                            if f.is_file():
                                keys.append(f"{d.name}/{f.name}")
        return keys

    def get_size(self, key: str) -> int:
        """Get the size of data in bytes.

        Args:
            key: Checkpoint key in format 'workflow_id/checkpoint_id'.

        Returns:
            Size in bytes, or 0 if checkpoint does not exist.

        Raises:
            InvalidCheckpointKeyError: If key format is invalid.
        """
        workflow_id, checkpoint_id = self._parse_key(key)
        checkpoint_path = self._get_checkpoint_dir(workflow_id) / checkpoint_id

        if not checkpoint_path.exists():
            return 0

        try:
            return checkpoint_path.stat().st_size
        except (OSError, IOError):
            return 0

    def get_metadata_path(self, key: str) -> str:
        """Get the path for metadata file.

        Args:
            key: Checkpoint key in format 'workflow_id/checkpoint_id'.

        Returns:
            Path to metadata file.

        Raises:
            InvalidCheckpointKeyError: If key format is invalid.
        """
        workflow_id, checkpoint_id = self._parse_key(key)
        checkpoint_dir = self._get_checkpoint_dir(workflow_id)
        return str(checkpoint_dir / f"{checkpoint_id}.meta")


@dataclass
class CheckpointMetadata:
    """Metadata for a checkpoint.

    Attributes:
        id: Unique identifier for the checkpoint.
        workflow_id: ID of the workflow this checkpoint belongs to.
        step: The workflow step at which the checkpoint was created.
        created_at: Timestamp when the checkpoint was created.
        size_bytes: Size of the checkpoint data in bytes.
        description: Optional description of the checkpoint.
        version: Version of the checkpoint format.
    """
    id: str
    workflow_id: str
    step: int
    created_at: datetime
    size_bytes: int = 0
    description: str = ""
    version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "step": self.step,
            "created_at": self.created_at.isoformat(),
            "size_bytes": self.size_bytes,
            "description": self.description,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CheckpointMetadata":
        """Create metadata from dictionary."""
        return cls(
            id=data["id"],
            workflow_id=data["workflow_id"],
            step=data["step"],
            created_at=datetime.fromisoformat(data["created_at"]),
            size_bytes=data.get("size_bytes", 0),
            description=data.get("description", ""),
            version=data.get("version", "1.0"),
        )


@dataclass
class Checkpoint:
    """A checkpoint containing workflow state and metadata.

    Attributes:
        id: Unique identifier for the checkpoint.
        workflow_id: ID of the workflow this checkpoint belongs to.
        step: The workflow step at which the checkpoint was created.
        created_at: Timestamp when the checkpoint was created.
        state: The workflow state data.
        metadata: Optional description of the checkpoint.
    """
    id: str
    workflow_id: str
    step: int
    created_at: datetime
    state: Dict[str, Any]
    size_bytes: int = 0
    description: str = ""
    version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert checkpoint to dictionary."""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "step": self.step,
            "created_at": self.created_at.isoformat(),
            "state": self.state,
            "size_bytes": self.size_bytes,
            "description": self.description,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checkpoint":
        """Create checkpoint from dictionary."""
        return cls(
            id=data["id"],
            workflow_id=data["workflow_id"],
            step=data["step"],
            created_at=datetime.fromisoformat(data["created_at"]),
            state=data["state"],
            size_bytes=data.get("size_bytes", 0),
            description=data.get("description", ""),
            version=data.get("version", "1.0"),
        )


class CheckpointSerializer:
    """Serializer for checkpoint data."""

    def __init__(self, format: str = "pickle"):
        """Initialize serializer.

        Args:
            format: Serialization format ('pickle' or 'json').
        """
        self.format = format.lower()
        if self.format not in ("pickle", "json"):
            raise ValueError(f"Unsupported serializer format: {format}. Use 'pickle' or 'json'.")

    def serialize(self, data: Dict[str, Any]) -> bytes:
        """Serialize checkpoint data.

        Args:
            data: Checkpoint data to serialize.

        Returns:
            Serialized data as bytes.
        """
        if self.format == "pickle":
            return pickle.dumps(data)
        else:
            # JSON serialization
            json_str = json.dumps(data, default=str, ensure_ascii=False)
            return json_str.encode("utf-8")

    def deserialize(self, data: bytes) -> Dict[str, Any]:
        """Deserialize checkpoint data.

        Args:
            data: Serialized data bytes.

        Returns:
            Deserialized checkpoint data.
        """
        if self.format == "pickle":
            return pickle.loads(data)
        else:
            return json.loads(data.decode("utf-8"))


class CheckpointManager:
    """Manages workflow checkpoints with thread-safe operations.

    Provides functionality for:
    - Saving workflow states to checkpoints
    - Restoring workflow states from checkpoints
    - Listing available checkpoints
    - Automatic cleanup of old checkpoints
    - Support for multiple storage backends and serializers

    Attributes:
        storage: Storage backend for checkpoint data.
        serializer: Serializer for checkpoint data.
        checkpoint_dir: Directory for storing checkpoints.
        max_checkpoints: Maximum number of checkpoints to keep per workflow.

    Usage:
        ```python
        from dslighting.checkpoint import CheckpointManager

        manager = CheckpointManager(
            checkpoint_dir="./checkpoints",
            serializer="pickle",
            max_checkpoints=5
        )

        # Save checkpoint
        manager.save("workflow_1", {"accuracy": 0.9}, step=5)

        # Load checkpoint
        checkpoint = manager.load_latest("workflow_1")

        # List checkpoints
        checkpoints = manager.list_checkpoints("workflow_1")

        # Cleanup old checkpoints
        manager.cleanup("workflow_1", keep=3)
        ```
    """

    def __init__(
        self,
        storage_backend: Optional[StorageBackend] = None,
        serializer: str = "pickle",
        checkpoint_dir: PathType = "./checkpoints",
        max_checkpoints: int = 10,
    ):
        """Initialize the checkpoint manager.

        Args:
            storage_backend: Storage backend instance. If None, uses LocalStorageBackend.
            serializer: Serialization format ('pickle' or 'json').
            checkpoint_dir: Directory for storing checkpoints.
            max_checkpoints: Maximum number of checkpoints to keep per workflow.
        """
        self.storage = storage_backend or LocalStorageBackend(checkpoint_dir)
        self.serializer = CheckpointSerializer(serializer)
        self.checkpoint_dir = Path(checkpoint_dir)
        self.max_checkpoints = max_checkpoints
        self._lock = threading.RLock()

    def _generate_checkpoint_id(self, workflow_id: str) -> str:
        """Generate a unique checkpoint ID.

        Args:
            workflow_id: The workflow ID.

        Returns:
            Unique checkpoint ID string.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"cp_{timestamp}"

    def save(
        self,
        workflow_id: str,
        state: Dict[str, Any],
        step: int,
        description: str = "",
    ) -> Checkpoint:
        """Save a workflow checkpoint.

        Args:
            workflow_id: Unique identifier for the workflow.
            state: Workflow state data to save.
            step: Current step in the workflow.
            description: Optional description of the checkpoint.

        Returns:
            The created Checkpoint object.

        Raises:
            ValueError: If state is not a dictionary.
        """
        if not isinstance(state, dict):
            raise ValueError("State must be a dictionary")

        with self._lock:
            checkpoint_id = self._generate_checkpoint_id(workflow_id)
            now = datetime.now()

            # Create checkpoint object
            checkpoint = Checkpoint(
                id=checkpoint_id,
                workflow_id=workflow_id,
                step=step,
                created_at=now,
                state=state,
                description=description,
            )

            # Serialize checkpoint data
            data = checkpoint.to_dict()
            serialized_data = self.serializer.serialize(data)

            # Get storage key
            storage_key = f"{workflow_id}/{checkpoint_id}.chk"

            # Write to storage
            success = self.storage.write(storage_key, serialized_data)

            if not success:
                raise IOError(f"Failed to write checkpoint to storage: {storage_key}")

            # Write metadata
            metadata = CheckpointMetadata(
                id=checkpoint_id,
                workflow_id=workflow_id,
                step=step,
                created_at=now,
                size_bytes=len(serialized_data),
                description=description,
            )
            metadata_key = self.storage.get_metadata_path(storage_key)
            metadata_path = Path(metadata_key)
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            metadata_path.write_text(json.dumps(metadata.to_dict(), indent=2))

            # Update checkpoint size
            checkpoint.size_bytes = len(serialized_data)

            return checkpoint

    def load(
        self,
        checkpoint_id: str,
        workflow_id: str,
    ) -> Optional[Checkpoint]:
        """Load a specific checkpoint.

        Args:
            checkpoint_id: ID of the checkpoint to load.
            workflow_id: Workflow ID the checkpoint belongs to.

        Returns:
            The Checkpoint object, or None if not found.
        """
        with self._lock:
            storage_key = f"{workflow_id}/{checkpoint_id}.chk"
            data = self.storage.read(storage_key)

            if data is None:
                return None

            try:
                deserialized = self.serializer.deserialize(data)
                return Checkpoint.from_dict(deserialized)
            except (pickle.PickleError, json.JSONDecodeError, KeyError):
                return None

    def load_latest(self, workflow_id: str) -> Optional[Checkpoint]:
        """Load the latest checkpoint for a workflow.

        Args:
            workflow_id: ID of the workflow.

        Returns:
            The latest Checkpoint object, or None if no checkpoints exist.
        """
        with self._lock:
            checkpoints = self.list_checkpoints(workflow_id)

            if not checkpoints:
                return None

            # Sort by created_at to get the latest
            sorted_checkpoints = sorted(
                checkpoints,
                key=lambda cp: cp.created_at,
                reverse=True
            )

            latest = sorted_checkpoints[0]
            return self.load(latest.id, workflow_id)

    def load_by_step(self, workflow_id: str, step: int) -> Optional[Checkpoint]:
        """Load checkpoint at a specific step.

        Args:
            workflow_id: ID of the workflow.
            step: Step number to load.

        Returns:
            The Checkpoint object at the specified step, or None if not found.
        """
        with self._lock:
            checkpoints = self.list_checkpoints(workflow_id)

            for cp in checkpoints:
                if cp.step == step:
                    return self.load(cp.id, workflow_id)

            return None

    def list_checkpoints(
        self,
        workflow_id: str,
        limit: int = 50,
        sort_by: str = "created_at",
    ) -> List[CheckpointMetadata]:
        """List all checkpoints for a workflow.

        Args:
            workflow_id: ID of the workflow.
            limit: Maximum number of checkpoints to return.
            sort_by: Sort field ('created_at', 'step', or 'size').

        Returns:
            List of CheckpointMetadata objects.
        """
        with self._lock:
            keys = self.storage.list_keys(f"{workflow_id}/")

            checkpoints = []
            for key in keys:
                if key.endswith(".chk"):
                    checkpoint_id = Path(key).stem  # Remove .chk extension
                    metadata_key = self.storage.get_metadata_path(key)

                    # Try to load metadata file first
                    metadata_path = Path(metadata_key)
                    if metadata_path.exists():
                        try:
                            metadata_data = json.loads(metadata_path.read_text())
                            metadata = CheckpointMetadata.from_dict(metadata_data)
                            checkpoints.append(metadata)
                            continue
                        except (json.JSONDecodeError, KeyError):
                            pass

                    # Fallback: load checkpoint directly
                    checkpoint = self.load(checkpoint_id, workflow_id)
                    if checkpoint:
                        checkpoints.append(CheckpointMetadata(
                            id=checkpoint.id,
                            workflow_id=checkpoint.workflow_id,
                            step=checkpoint.step,
                            created_at=checkpoint.created_at,
                            size_bytes=checkpoint.size_bytes,
                            description=checkpoint.description,
                        ))

            # Sort checkpoints
            if sort_by == "step":
                checkpoints.sort(key=lambda cp: cp.step, reverse=True)
            elif sort_by == "size":
                checkpoints.sort(key=lambda cp: cp.size_bytes, reverse=True)
            else:  # created_at
                checkpoints.sort(key=lambda cp: cp.created_at, reverse=True)

            return checkpoints[:limit]

    def list_all_workflows(self) -> List[str]:
        """List all workflows with checkpoints.

        Returns:
            List of workflow IDs.
        """
        with self._lock:
            keys = self.storage.list_keys()
            workflows = set()
            for key in keys:
                if key.endswith(".chk"):
                    parts = key.split("/", 1)
                    if len(parts) == 2:
                        workflows.add(parts[0])
            return sorted(list(workflows))

    def delete(
        self,
        checkpoint_id: str,
        workflow_id: str,
    ) -> bool:
        """Delete a specific checkpoint.

        Args:
            checkpoint_id: ID of the checkpoint to delete.
            workflow_id: Workflow ID the checkpoint belongs to.

        Returns:
            True if deletion was successful.
        """
        with self._lock:
            storage_key = f"{workflow_id}/{checkpoint_id}.chk"
            metadata_key = self.storage.get_metadata_path(storage_key)

            success = self.storage.delete(storage_key)

            # Also delete metadata file if it exists
            metadata_path = Path(metadata_key)
            if metadata_path.exists():
                metadata_path.unlink()

            return success

    def delete_all(self, workflow_id: str) -> int:
        """Delete all checkpoints for a workflow.

        Args:
            workflow_id: Workflow ID.

        Returns:
            Number of checkpoints deleted.
        """
        with self._lock:
            checkpoints = self.list_checkpoints(workflow_id, limit=1000)
            count = 0

            for cp in checkpoints:
                if self.delete(cp.id, workflow_id):
                    count += 1

            return count

    def cleanup(
        self,
        workflow_id: str,
        keep: Optional[int] = None,
    ) -> int:
        """Clean up old checkpoints, keeping the most recent ones.

        Args:
            workflow_id: Workflow ID.
            keep: Number of checkpoints to keep. If None, uses max_checkpoints.

        Returns:
            Number of checkpoints deleted.
        """
        with self._lock:
            keep_count = keep if keep is not None else self.max_checkpoints
            checkpoints = self.list_checkpoints(workflow_id, limit=1000)

            if len(checkpoints) <= keep_count:
                return 0

            # Sort by created_at (oldest first) and delete oldest ones
            sorted_checkpoints = sorted(checkpoints, key=lambda cp: cp.created_at)
            delete_count = 0

            for cp in sorted_checkpoints[:-keep_count]:
                if self.delete(cp.id, workflow_id):
                    delete_count += 1

            return delete_count

    def get_workflow_stats(self, workflow_id: str) -> Dict[str, Any]:
        """Get statistics for a workflow's checkpoints.

        Args:
            workflow_id: Workflow ID.

        Returns:
            Dictionary with workflow checkpoint statistics.
        """
        with self._lock:
            checkpoints = self.list_checkpoints(workflow_id, limit=1000)

            if not checkpoints:
                return {
                    "workflow_id": workflow_id,
                    "checkpoint_count": 0,
                    "total_size_bytes": 0,
                    "steps": [],
                    "oldest_checkpoint": None,
                    "latest_checkpoint": None,
                }

            sorted_by_time = sorted(checkpoints, key=lambda cp: cp.created_at)
            sorted_by_step = sorted(checkpoints, key=lambda cp: cp.step)

            return {
                "workflow_id": workflow_id,
                "checkpoint_count": len(checkpoints),
                "total_size_bytes": sum(cp.size_bytes for cp in checkpoints),
                "steps": [cp.step for cp in sorted_by_step],
                "step_range": {
                    "min": min(cp.step for cp in checkpoints),
                    "max": max(cp.step for cp in checkpoints),
                },
                "oldest_checkpoint": sorted_by_time[0].created_at.isoformat(),
                "latest_checkpoint": sorted_by_time[-1].created_at.isoformat(),
            }

    def exists(self, checkpoint_id: str, workflow_id: str) -> bool:
        """Check if a checkpoint exists.

        Args:
            checkpoint_id: Checkpoint ID.
            workflow_id: Workflow ID.

        Returns:
            True if checkpoint exists.
        """
        with self._lock:
            storage_key = f"{workflow_id}/{checkpoint_id}.chk"
            return self.storage.exists(storage_key)

    def size(self, checkpoint_id: str, workflow_id: str) -> int:
        """Get the size of a checkpoint in bytes.

        Args:
            checkpoint_id: Checkpoint ID.
            workflow_id: Workflow ID.

        Returns:
            Size in bytes, or 0 if not found.
        """
        with self._lock:
            storage_key = f"{workflow_id}/{checkpoint_id}.chk"
            return self.storage.get_size(storage_key)


# Convenience functions

def create_checkpoint_manager(
    checkpoint_dir: PathType = "./checkpoints",
    serializer: str = "pickle",
    max_checkpoints: int = 10,
) -> CheckpointManager:
    """Create a CheckpointManager with local filesystem storage.

    Args:
        checkpoint_dir: Directory for storing checkpoints.
        serializer: Serialization format ('pickle' or 'json').
        max_checkpoints: Maximum checkpoints per workflow.

    Returns:
        Configured CheckpointManager instance.
    """
    return CheckpointManager(
        storage_backend=LocalStorageBackend(checkpoint_dir),
        serializer=serializer,
        checkpoint_dir=checkpoint_dir,
        max_checkpoints=max_checkpoints,
    )


# Exports
__all__ = [
    "CheckpointManager",
    "CheckpointMetadata",
    "Checkpoint",
    "StorageBackend",
    "LocalStorageBackend",
    "CheckpointSerializer",
    "create_checkpoint_manager",
    # Exceptions
    "CheckpointError",
    "InvalidCheckpointKeyError",
    "CheckpointWriteError",
    "CheckpointReadError",
    "CheckpointDeleteError",
]
