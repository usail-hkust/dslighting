"""
Test MemoryManager vector store synchronization.

This test verifies that metadata updates are properly synchronized
with the vector store to ensure search operations return updated metadata.
"""

import pytest
from dslighting.state import MemoryManager, SimpleVectorStore


class TestMemoryManagerVectorSync:
    """Test vector store metadata synchronization."""

    def test_update_metadata_syncs_with_vector_store(self):
        """Test that update_metadata() synchronizes with vector store."""
        # Create a memory manager with a vector store
        vector_store = SimpleVectorStore()
        memory = MemoryManager(vector_store=vector_store)

        # Add a memory with an embedding vector
        test_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        memory.add(
            key="task_1",
            value="Important task data",
            metadata={"importance": "high", "status": "pending"},
            vector=test_vector
        )

        # Verify initial metadata in vector store
        vector_results = vector_store.search(test_vector, limit=10)
        assert len(vector_results) > 0
        key, score = vector_results[0]
        assert key == "task_1"

        # Get the stored metadata from vector store
        stored_vector, stored_metadata = vector_store._vectors["task_1"]
        assert stored_metadata["importance"] == "high"
        assert stored_metadata["status"] == "pending"

        # Update metadata using update_metadata()
        success = memory.update_metadata("task_1", {"status": "completed", "priority": 1})

        # Verify update was successful
        assert success is True

        # Verify metadata was updated in MemoryManager
        metadata = memory.get_metadata("task_1")
        assert metadata["importance"] == "high"  # Original value preserved
        assert metadata["status"] == "completed"  # Updated value
        assert metadata["priority"] == 1  # New value added

        # Verify metadata was synchronized with vector store
        stored_vector, stored_metadata = vector_store._vectors["task_1"]
        assert stored_metadata["importance"] == "high"
        assert stored_metadata["status"] == "completed"
        assert stored_metadata["priority"] == 1

        # Verify vector was not changed
        assert stored_vector == test_vector

    def test_update_metadata_nonexistent_key(self):
        """Test that update_metadata() returns False for nonexistent keys."""
        memory = MemoryManager()

        # Try to update metadata for a key that doesn't exist
        success = memory.update_metadata("nonexistent", {"status": "completed"})

        # Verify it returns False
        assert success is False

    def test_update_metadata_without_vector(self):
        """Test that update_metadata() works for memories without vectors."""
        memory = MemoryManager()

        # Add a memory without a vector
        memory.add(
            key="task_2",
            value="Simple task",
            metadata={"status": "pending"}
        )

        # Update metadata
        success = memory.update_metadata("task_2", {"status": "completed"})

        # Verify update was successful
        assert success is True
        metadata = memory.get_metadata("task_2")
        assert metadata["status"] == "completed"

    def test_vector_store_update_method(self):
        """Test SimpleVectorStore.update() method directly."""
        vector_store = SimpleVectorStore()

        # Add a vector with metadata
        vector = [0.1, 0.2, 0.3]
        vector_store.add("key1", vector, {"label": "initial"})

        # Update metadata
        success = vector_store.update("key1", {"label": "updated", "new_field": "value"})

        # Verify update
        assert success is True

        # Check that vector was preserved and metadata updated
        stored_vector, stored_metadata = vector_store._vectors["key1"]
        assert stored_vector == vector
        assert stored_metadata["label"] == "updated"
        assert stored_metadata["new_field"] == "value"

    def test_vector_store_update_nonexistent_key(self):
        """Test SimpleVectorStore.update() with nonexistent key."""
        vector_store = SimpleVectorStore()

        # Try to update a key that doesn't exist
        success = vector_store.update("nonexistent", {"label": "updated"})

        # Verify it returns False
        assert success is False

    def test_search_returns_updated_metadata(self):
        """Test that search() returns metadata that has been updated."""
        memory = MemoryManager()

        # Add memories with vectors
        vector1 = [0.1, 0.2, 0.3]
        vector2 = [0.4, 0.5, 0.6]

        memory.add(
            key="task_1",
            value="Task 1",
            metadata={"status": "pending"},
            vector=vector1
        )
        memory.add(
            key="task_2",
            value="Task 2",
            metadata={"status": "pending"},
            vector=vector2
        )

        # Update metadata for task_1
        memory.update_metadata("task_1", {"status": "completed"})

        # Search with vector1
        results = memory.search(vector=vector1, limit=5, include_metadata=True)

        # Verify we get updated metadata
        assert len(results) > 0
        key, value, metadata = results[0]
        assert key == "task_1"
        assert metadata["status"] == "completed"
