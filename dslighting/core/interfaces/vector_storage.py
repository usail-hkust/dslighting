"""
Unified vector storage interface for DSLighting.

This module provides the abstract interface for vector storage implementations,
ensuring that MemoryManager and VDBService follow the same contract.

The vector storage interface supports:
- Adding vectors with metadata
- Searching by similarity
- Retrieving by key
- Updating and deleting vectors
- Persistence (snapshot/restore)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union


class VectorStorageInterface(ABC):
    """
    Abstract interface for vector storage backends.

    This interface defines the contract that all vector storage implementations
    must follow, enabling interchangeable use of different storage backends
    (in-memory, disk-based, remote services, etc.).

    Implementations:
    - SimpleVectorStore (in-memory, state/memory.py)
    - VDBService (transformer-based, services/vdb.py)
    - Future: ChromaDB, FAISS, Pinecone, etc.
    """

    @abstractmethod
    def add(
        self,
        key: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a vector to the store.

        Args:
            key: Unique identifier for the vector
            vector: Embedding vector (list of floats)
            metadata: Optional metadata dictionary
        """
        pass

    @abstractmethod
    def search(
        self,
        query: Union[List[float], str],
        limit: int = 10,
        **kwargs
    ) -> List[Tuple[str, float]]:
        """
        Search for similar vectors.

        Args:
            query: Query vector (list of floats) or text query
            limit: Maximum number of results to return
            **kwargs: Additional search parameters

        Returns:
            List of (key, similarity_score) tuples, sorted by similarity
        """
        pass

    @abstractmethod
    def retrieve(
        self,
        key: str,
        include_metadata: bool = True
    ) -> Optional[Tuple[List[float], Dict[str, Any]]]:
        """
        Retrieve a vector by its key.

        Args:
            key: Vector identifier
            include_metadata: Whether to include metadata in result

        Returns:
            (vector, metadata) tuple or None if not found
        """
        pass

    @abstractmethod
    def update(
        self,
        key: str,
        vector: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an existing vector's metadata or vector data.

        Args:
            key: Vector identifier
            vector: New vector data (optional)
            metadata: New metadata (optional)

        Returns:
            True if updated, False if key not found
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete a vector by key.

        Args:
            key: Vector identifier

        Returns:
            True if deleted, False if key not found
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all vectors from the store."""
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Get the number of vectors in the store.

        Returns:
            Number of stored vectors
        """
        pass

    # Optional: Persistence support

    def snapshot(self) -> bytes:
        """
        Create a snapshot of the vector store.

        Returns:
            Serialized snapshot data

        Raises:
            NotImplementedError: If persistence is not supported
        """
        raise NotImplementedError("Persistence not supported by this implementation")

    def restore(self, data: bytes) -> None:
        """
        Restore from a snapshot.

        Args:
            data: Serialized snapshot data

        Raises:
            NotImplementedError: If persistence is not supported
        """
        raise NotImplementedError("Persistence not supported by this implementation")

    # Optional: Batch operations

    def add_batch(
        self,
        items: List[Tuple[str, List[float], Dict[str, Any]]]
    ) -> None:
        """
        Add multiple vectors in a batch.

        Args:
            items: List of (key, vector, metadata) tuples

        Note:
            Default implementation calls add() repeatedly.
            Override for efficient batch processing.
        """
        for key, vector, metadata in items:
            self.add(key, vector, metadata)

    def search_batch(
        self,
        queries: List[Union[List[float], str]],
        limit: int = 10,
        **kwargs
    ) -> List[List[Tuple[str, float]]]:
        """
        Search multiple queries in batch.

        Args:
            queries: List of query vectors or text queries
            limit: Maximum results per query
            **kwargs: Additional search parameters

        Returns:
            List of result lists, one per query

        Note:
            Default implementation calls search() repeatedly.
            Override for efficient batch processing.
        """
        return [self.search(q, limit, **kwargs) for q in queries]


class VectorStorageConfig:
    """
    Configuration for vector storage implementations.

    Attributes:
        backend: Storage backend type ("simple", "vdb", "chroma", etc.)
        dimension: Vector dimension (if fixed)
        metric: Similarity metric ("cosine", "euclidean", "dot")
        persist_path: Path for persistent storage (optional)
    """

    def __init__(
        self,
        backend: str = "simple",
        dimension: Optional[int] = None,
        metric: str = "cosine",
        persist_path: Optional[str] = None,
        **kwargs
    ):
        self.backend = backend
        self.dimension = dimension
        self.metric = metric
        self.persist_path = persist_path
        self.extra_params = kwargs


def create_vector_storage(config: VectorStorageConfig) -> VectorStorageInterface:
    """
    Factory function to create vector storage instances.

    Args:
        config: Vector storage configuration

    Returns:
        Vector storage instance

    Raises:
        ValueError: If backend type is unknown
    """
    backend = config.backend.lower()

    if backend == "simple":
        from dslighting.state.memory import SimpleVectorStore
        return SimpleVectorStore()
    elif backend == "vdb":
        from dslighting.services.vdb import VDBService
        # VDBService requires case_dir, so we need special handling
        raise ValueError(
            "VDBService requires a case directory. "
            "Instantiate VDBService directly instead."
        )
    else:
        raise ValueError(f"Unknown vector storage backend: {backend}")
