"""
Defines the abstract base class for all state management services in DSLighting.
"""
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, Any
from datetime import datetime

T = TypeVar("T")


class State(ABC, Generic[T]):
    """Abstract base class for state managers.

    State managers provide persistence and continuity for agent workflows,
    enabling features like:
    - Checkpoint/resume from failures
    - History tracking for analysis
    - Branch exploration (tree-based search)

    Subclasses implement different storage backends (memory, disk, database, etc.)
    while providing a consistent interface for state management operations.
    """

    @abstractmethod
    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """Get a value by key.

        Args:
            key: The unique identifier for the stored value.
            default: Default value to return if key not found.

        Returns:
            The stored value or default if key not found.
        """
        raise NotImplementedError("Subclasses must implement get().")

    @abstractmethod
    def set(self, key: str, value: T) -> None:
        """Set a value by key.

        Args:
            key: The unique identifier for the value.
            value: The value to store.
        """
        raise NotImplementedError("Subclasses must implement set().")

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a key, return True if existed.

        Args:
            key: The unique identifier to delete.

        Returns:
            True if the key existed and was deleted, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement delete().")

    @abstractmethod
    def clear(self) -> None:
        """Clear all state.

        Removes all stored keys and values from this state manager.
        """
        raise NotImplementedError("Subclasses must implement clear().")

    @abstractmethod
    def snapshot(self) -> bytes:
        """Create a checkpoint snapshot.

        Creates a serialized byte representation of the current state
        that can be used to restore the state later.

        Returns:
            Serialized state data as bytes.
        """
        raise NotImplementedError("Subclasses must implement snapshot().")

    @abstractmethod
    def restore(self, data: bytes) -> bool:
        """Restore from checkpoint snapshot.

        Args:
            data: Serialized state data from a previous snapshot() call.

        Returns:
            True if restoration was successful, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement restore().")

    @property
    @abstractmethod
    def created_at(self) -> datetime:
        """When this state was created.

        Returns:
            The datetime when this state instance was created.
        """
        raise NotImplementedError("Subclasses must implement created_at.")
