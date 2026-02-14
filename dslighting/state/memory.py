"""
DSLighting 2.0 - Memory Manager

This module provides memory management capabilities for agents.
Memory managers store and retrieve agent memories with support for
persistence, semantic search, and capacity management.

Features:
- Long-term memory storage across tasks
- Memory retrieval and search (keyword and semantic)
- Memory consolidation and pruning
- Experience-based memory prioritization
- Persistent storage with snapshot/restore
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import pickle
from abc import abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Protocol, runtime_checkable

import aiofiles
import numpy as np

logger = logging.getLogger(__name__)


@runtime_checkable
class VectorStoreProtocol(Protocol):
    """Protocol for vector storage backends.

    This defines the interface that all vector store implementations
    must follow. Using Protocol allows for structural typing while
    keeping the interface explicit.
    """

    def add(self, key: str, vector: list[float], metadata: dict[str, Any]) -> None:
        """Add a vector to the store."""
        ...

    def search(self, query: list[float], limit: int) -> list[tuple[str, float]]:
        """Search for similar vectors."""
        ...

    def delete(self, key: str) -> bool:
        """Delete a vector by key."""
        ...

    def update(self, key: str, metadata: dict[str, Any]) -> bool:
        """Update metadata for an existing vector."""
        ...

    def clear(self) -> None:
        """Clear all vectors."""
        ...

    def snapshot(self) -> bytes:
        """Create a snapshot of the vector store."""
        ...

    def restore(self, data: bytes) -> None:
        """Restore from a snapshot."""
        ...

    def retrieve(
        self,
        key: str,
        include_metadata: bool = True
    ) -> Optional[tuple[list[float], dict[str, Any]]]:
        """Retrieve a vector by its key (optional default implementation)."""
        ...

    def count(self) -> int:
        """Get the number of vectors in the store (optional default implementation)."""
        ...


# Keep VectorStore as alias for backward compatibility
VectorStore = VectorStoreProtocol


class SimpleVectorStore:
    """Simple in-memory vector store using brute-force similarity.

    Provides a straightforward implementation of the VectorStoreProtocol
    with optional default implementations for retrieve() and count().
    """

    def __init__(self):
        self._vectors: dict[str, tuple[list[float], dict[str, Any]]] = {}

    def add(self, key: str, vector: list[float], metadata: dict[str, Any]) -> None:
        self._vectors[key] = (vector, metadata)

    def search(self, query: list[float], limit: int) -> list[tuple[str, float]]:
        query_arr = np.array(query)
        results = []
        for key, (vec, _) in self._vectors.items():
            vec_arr = np.array(vec)
            similarity = float(np.dot(query_arr, vec_arr) / (np.linalg.norm(query_arr) * np.linalg.norm(vec_arr) + 1e-10))
            results.append((key, similarity))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def delete(self, key: str) -> bool:
        if key in self._vectors:
            del self._vectors[key]
            return True
        return False

    def update(self, key: str, metadata: dict[str, Any]) -> bool:
        """Update metadata for an existing vector."""
        if key in self._vectors:
            vector, _ = self._vectors[key]
            self._vectors[key] = (vector, metadata)
            return True
        return False

    def clear(self) -> None:
        self._vectors.clear()

    def snapshot(self) -> bytes:
        return pickle.dumps(self._vectors)

    def restore(self, data: bytes) -> None:
        self._vectors = pickle.loads(data)

    def retrieve(
        self,
        key: str,
        include_metadata: bool = True
    ) -> Optional[tuple[list[float], dict[str, Any]]]:
        """Retrieve a vector by its key."""
        if key in self._vectors:
            vector, metadata = self._vectors[key]
            if include_metadata:
                return (vector, metadata)
            return (vector, {})
        return None

    def count(self) -> int:
        """Get the number of vectors in the store."""
        return len(self._vectors)


class MemoryManager:
    """Memory Manager for agent memory operations.

    Provides persistent memory storage with support for:
    - Key-value storage with metadata
    - Semantic search via vector embeddings
    - Capacity management and eviction
    - Snapshot/restore for persistence

    Usage:
        ```python
        from dslighting.state import MemoryManager

        # Initialize memory manager
        memory = MemoryManager()

        # Store information
        memory.add("task_1", {"key": "value"}, metadata={"importance": "high"})

        # Retrieve information
        result = memory.get("task_1")

        # Search memories
        results = memory.search("important tasks", limit=5)
        ```
    """

    def __init__(
        self,
        capacity: int = 1000,
        persistent_path: str | None = None,
        vector_store: VectorStoreProtocol | None = None,
        auto_persist: bool = True,
        persist_interval: int = 100,
    ):
        """Initialize the MemoryManager.

        Args:
            capacity: Maximum number of memories to store. When exceeded,
                oldest entries are evicted (FIFO).
            persistent_path: Optional path to persist memory to disk.
                If provided, memory will be loaded/saved to this file.
            vector_store: Optional vector store for semantic search.
                If not provided, keyword-based search is used.
            auto_persist: Whether to auto-save after each add when
                persistent_path is set.
            persist_interval: Number of operations between auto-persists.
        """
        self.capacity = capacity
        self.persistent_path = Path(persistent_path) if persistent_path else None
        self.vector_store = vector_store or SimpleVectorStore()
        self.auto_persist = auto_persist
        self.persist_interval = persist_interval
        self._op_count = 0

        self._memories: dict[str, Any] = {}
        self._metadata: dict[str, dict[str, Any]] = {}
        self._created_at = datetime.now()

        # Load from disk if persistent path exists
        if self.persistent_path and self.persistent_path.exists():
            self._load()

    @property
    def created_at(self) -> datetime:
        """When this MemoryManager was created."""
        return self._created_at

    def add(
        self,
        key: str,
        value: Any,
        metadata: dict[str, Any] | None = None,
        vector: list[float] | None = None,
    ) -> bool:
        """Add a memory entry.

        Args:
            key: Unique identifier for the memory.
            value: The memory content to store.
            metadata: Optional metadata (tags, importance, timestamp, etc.).
            vector: Optional embedding vector for semantic search.

        Returns:
            True if memory was added successfully.

        Note:
            FIFO eviction only triggers when adding a new key that would exceed
            capacity. The capacity check is performed at addition time, not on
            retrieval operations. This ensures predictable eviction behavior.
        """
        # Evict oldest if at capacity
        if key not in self._memories and len(self._memories) >= self.capacity:
            if self._memories:
                oldest_key = next(iter(self._memories.keys()))
                self.delete(oldest_key)

        timestamp = datetime.now().isoformat()
        self._memories[key] = value
        self._metadata[key] = {
            "timestamp": timestamp,
            "created_at": timestamp,
            **(metadata or {}),
        }

        # Add to vector store if provided
        if vector is not None:
            self.vector_store.add(key, vector, self._metadata[key])

        self._op_count += 1
        self._auto_persist()

        return True

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a memory by key.

        Args:
            key: Memory identifier.
            default: Default value if key not found.

        Returns:
            The memory content or default value.
        """
        return self._memories.get(key, default)

    def search(
        self,
        query: str | None = None,
        vector: list[float] | None = None,
        limit: int = 10,
        include_metadata: bool = False,
    ) -> list[tuple[str, Any]] | list[tuple[str, Any, dict[str, Any]]]:
        """Search memories by keyword or semantic similarity.

        Args:
            query: Keyword search query (used if no vector provided).
            vector: Optional query vector for semantic search.
            limit: Maximum number of results to return.
            include_metadata: Whether to include metadata in results.

        Returns:
            List of (key, value) tuples, or (key, value, metadata) tuples
            if include_metadata is True.
        """
        results: list[tuple[str, Any, float]] = []

        if vector is not None:
            # Semantic search using vector store
            vector_results = self.vector_store.search(vector, limit * 2)
            for key, score in vector_results:
                if key in self._memories:
                    results.append((key, self._memories[key], score))
        else:
            # Keyword-based search
            query_lower = (query or "").lower()
            for key, value in self._memories.items():
                if query_lower in key.lower() or query_lower in str(value).lower():
                    # Simple relevance scoring
                    score = 1.0 if query_lower in key.lower() else 0.5
                    results.append((key, value, score))

        # Sort by score and limit
        results.sort(key=lambda x: x[2], reverse=True)
        final_results = results[:limit]

        if include_metadata:
            return [(k, v, self._metadata.get(k, {})) for k, v, _ in final_results]
        return [(k, v) for k, v, _ in final_results]

    def delete(self, key: str) -> bool:
        """Delete a memory.

        Args:
            key: Memory identifier.

        Returns:
            True if memory was deleted, False if key not found.
        """
        if key in self._memories:
            del self._memories[key]
            del self._metadata[key]
            self.vector_store.delete(key)
            self._auto_persist()
            return True
        return False

    def clear(self) -> None:
        """Clear all memories."""
        self._memories.clear()
        self._metadata.clear()
        self.vector_store.clear()
        self._persist()
        self._op_count = 0

    def list_keys(self) -> list[str]:
        """List all memory keys.

        Returns:
            List of all memory keys.
        """
        return list(self._memories.keys())

    def size(self) -> int:
        """Get the number of stored memories.

        Returns:
            Number of memories stored.
        """
        return len(self._memories)

    def get_metadata(self, key: str) -> dict[str, Any]:
        """Get metadata for a memory.

        Args:
            key: Memory identifier.

        Returns:
            Metadata dictionary, empty if key not found.
        """
        return self._metadata.get(key, {})

    def update_metadata(self, key: str, metadata: dict[str, Any]) -> bool:
        """Update metadata for an existing memory.

        Args:
            key: Memory identifier.
            metadata: New metadata to merge with existing.

        Returns:
            True if memory existed and was updated.
        """
        if key in self._metadata:
            self._metadata[key].update(metadata)
            # Sync with vector store
            self.vector_store.update(key, self._metadata[key])
            self._auto_persist()
            return True
        return False

    def get_timestamps(self, key: str) -> dict[str, str] | None:
        """Get creation and modification timestamps for a memory.

        Args:
            key: Memory identifier.

        Returns:
            Dictionary with 'created_at' and 'updated_at' timestamps,
            or None if key not found.
        """
        if key in self._metadata:
            meta = self._metadata[key]
            return {
                "created_at": meta.get("created_at", ""),
                "updated_at": meta.get("updated_at", ""),
            }
        return None

    def snapshot(self) -> bytes:
        """Create a checkpoint snapshot of all memories.

        Returns:
            Serialized state data as bytes.
        """
        data = {
            "memories": self._memories,
            "metadata": self._metadata,
            "vector_store": self.vector_store.snapshot(),
            "created_at": self._created_at.isoformat(),
            "version": "1.0",
        }
        return pickle.dumps(data)

    def restore(self, data: bytes) -> bool:
        """Restore memories from a checkpoint snapshot.

        Args:
            data: Serialized state data from a snapshot() call.

        Returns:
            True if restoration was successful.
        """
        try:
            loaded = pickle.loads(data)
            self._memories = loaded.get("memories", {})
            self._metadata = loaded.get("metadata", {})
            self._created_at = datetime.fromisoformat(loaded.get("created_at", datetime.now().isoformat()))
            self.vector_store.restore(loaded.get("vector_store", b""))
            return True
        except (pickle.PickleError, KeyError, ValueError) as e:
            logger.warning(f"Failed to restore memory snapshot: {e}")
            return False

    def _persist(self) -> None:
        """Save memories to disk if persistent path is configured."""
        if self.persistent_path:
            data = self.snapshot()
            self.persistent_path.parent.mkdir(parents=True, exist_ok=True)
            self.persistent_path.write_bytes(data)

    async def _persist_async(self) -> None:
        """Async version of _persist using aiofiles."""
        if self.persistent_path:
            data = self.snapshot()
            self.persistent_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(self.persistent_path, 'wb') as f:
                await f.write(data)

    def _load(self) -> bool:
        """Load memories from disk if persistent path exists.

        Returns:
            True if loaded successfully.
        """
        if self.persistent_path and self.persistent_path.exists():
            try:
                data = self.persistent_path.read_bytes()
                return self.restore(data)
            except (OSError, pickle.PickleError):
                return False
        return False

    async def _load_async(self) -> bool:
        """Async version of _load using aiofiles.

        Returns:
            True if loaded successfully.
        """
        if self.persistent_path and self.persistent_path.exists():
            try:
                async with aiofiles.open(self.persistent_path, 'rb') as f:
                    data = await f.read()
                return self.restore(data)
            except (OSError, pickle.PickleError):
                return False
        return False

    def _auto_persist(self) -> None:
        """Auto-persist if threshold reached."""
        if self.auto_persist and self.persistent_path and self._op_count >= self.persist_interval:
            self._persist()
            self._op_count = 0

    async def _auto_persist_async(self) -> None:
        """Async auto-persist if threshold reached."""
        if self.auto_persist and self.persistent_path and self._op_count >= self.persist_interval:
            await self._persist_async()
            self._op_count = 0

    def export(self, path: str, format: str = "json") -> bool:
        """Export memories to a file.

        Args:
            path: Output file path.
            format: Export format ('json' or 'pickle').

        Returns:
            True if export was successful.
        """
        try:
            if format == "json":
                export_data = {
                    "memories": self._memories,
                    "metadata": self._metadata,
                    "exported_at": datetime.now().isoformat(),
                }
                Path(path).write_text(json.dumps(export_data, indent=2, default=str))
            else:
                Path(path).write_bytes(self.snapshot())
            return True
        except (OSError, TypeError):
            return False

    async def export_async(self, path: str, format: str = "json") -> bool:
        """Async version of export using aiofiles.

        Args:
            path: Output file path.
            format: Export format ('json' or 'pickle').

        Returns:
            True if export was successful.
        """
        try:
            if format == "json":
                export_data = {
                    "memories": self._memories,
                    "metadata": self._metadata,
                    "exported_at": datetime.now().isoformat(),
                }
                content = json.dumps(export_data, indent=2, default=str)
                async with aiofiles.open(path, 'w', encoding='utf-8') as f:
                    await f.write(content)
            else:
                data = self.snapshot()
                async with aiofiles.open(path, 'wb') as f:
                    await f.write(data)
            return True
        except (OSError, TypeError):
            return False

    def import_(self, path: str, format: str = "json", merge: bool = True) -> bool:
        """Import memories from a file.

        Args:
            path: Input file path.
            format: Import format ('json' or 'pickle').
            merge: Whether to merge with existing memories or replace.

        Returns:
            True if import was successful.
        """
        try:
            if format == "json":
                import_data = json.loads(Path(path).read_text())
                new_memories = import_data.get("memories", {})
                new_metadata = import_data.get("metadata", {})
            else:
                data = Path(path).read_bytes()
                loaded = pickle.loads(data)
                new_memories = loaded.get("memories", {})
                new_metadata = loaded.get("metadata", {})

            if merge:
                self._memories.update(new_memories)
                self._metadata.update(new_metadata)
            else:
                self._memories = new_memories
                self._metadata = new_metadata
            return True
        except (OSError, json.JSONDecodeError, pickle.PickleError):
            return False

    async def import_async(self, path: str, format: str = "json", merge: bool = True) -> bool:
        """Async version of import_ using aiofiles.

        Args:
            path: Input file path.
            format: Import format ('json' or 'pickle').
            merge: Whether to merge with existing memories or replace.

        Returns:
            True if import was successful.
        """
        try:
            if format == "json":
                async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                import_data = json.loads(content)
                new_memories = import_data.get("memories", {})
                new_metadata = import_data.get("metadata", {})
            else:
                async with aiofiles.open(path, 'rb') as f:
                    data = await f.read()
                loaded = pickle.loads(data)
                new_memories = loaded.get("memories", {})
                new_metadata = loaded.get("metadata", {})

            if merge:
                self._memories.update(new_memories)
                self._metadata.update(new_metadata)
            else:
                self._memories = new_memories
                self._metadata = new_metadata
            return True
        except (OSError, json.JSONDecodeError, pickle.PickleError):
            return False

    def __repr__(self) -> str:
        return (
            f"MemoryManager(capacity={self.capacity}, "
            f"size={self.size()}, "
            f"persistent={self.persistent_path is not None})"
        )
