"""Data preloader for parallel dataset loading.

This module provides utilities for preloading datasets in parallel to reduce
I/O wait time during task execution.
"""

from __future__ import annotations

import asyncio
import logging
import mmap
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


class DatasetPreloader:
    """
    Preloads datasets in parallel to reduce I/O overhead.

    Identifies unique datasets across problems and preloads them into memory
    or memory-mapped files for efficient access during task execution.

    Example:
        preloader = DatasetPreloader(max_concurrency=10)

        # Preload datasets from problems
        await preloader.preload_from_problems(problems)

        # Get preloaded dataset
        data = preloader.get_dataset("/path/to/train.csv")
    """

    def __init__(
        self,
        max_concurrency: int = 10,
        enable_mmap: bool = True,
        mmap_threshold_mb: float = 100.0,
    ):
        """
        Initialize the preloader.

        Args:
            max_concurrency: Maximum number of concurrent load operations
            enable_mmap: Whether to use memory-mapped files for large datasets
            mmap_threshold_mb: File size threshold (MB) for using mmap
        """
        self.max_concurrency = max_concurrency
        self.enable_mmap = enable_mmap
        self.mmap_threshold_bytes = mmap_threshold_mb * 1024 * 1024

        # Storage for preloaded datasets
        self._loaded_datasets: Dict[str, Any] = {}
        self._dataset_metadata: Dict[str, Dict[str, Any]] = {}

        # Semaphore for concurrency control
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def preload_from_problems(
        self,
        problems: List[Dict[str, Any]],
        dataset_keys: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Preload datasets from a list of problems.

        Args:
            problems: List of problem dictionaries
            dataset_keys: Keys to extract dataset paths from (default: ["train_path", "test_path"])

        Returns:
            Statistics about preloaded datasets
        """
        if dataset_keys is None:
            dataset_keys = ["train_path", "test_path", "prepared_path", "data_path"]

        # Identify unique datasets
        dataset_paths = self._extract_unique_datasets(problems, dataset_keys)

        logger.info(f"Found {len(dataset_paths)} unique datasets to preload")
        for path in dataset_paths:
            logger.debug(f"  - {path}")

        # Preload in parallel
        start_time = asyncio.get_event_loop().time()
        loaded_count = 0
        failed_count = 0
        total_size_mb = 0.0

        tasks = [
            self._load_dataset(path)
            for path in dataset_paths
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for path, result in zip(dataset_paths, results):
            if isinstance(result, Exception):
                logger.warning(f"Failed to preload {path}: {result}")
                failed_count += 1
            else:
                metadata = result
                loaded_count += 1
                total_size_mb += metadata.get("size_mb", 0.0)
                logger.debug(
                    f"Preloaded {path}: {metadata['size_mb']:.2f}MB, "
                    f"method={metadata['load_method']}"
                )

        elapsed = asyncio.get_event_loop().time() - start_time

        stats = {
            "total_datasets": len(dataset_paths),
            "loaded": loaded_count,
            "failed": failed_count,
            "total_size_mb": total_size_mb,
            "elapsed_seconds": elapsed,
        }

        logger.info(
            f"Preloading complete: {loaded_count}/{len(dataset_paths)} datasets, "
            f"{total_size_mb:.1f}MB in {elapsed:.2f}s"
        )

        return stats

    def _extract_unique_datasets(
        self,
        problems: List[Dict[str, Any]],
        dataset_keys: List[str],
    ) -> List[str]:
        """Extract unique dataset paths from problems."""
        dataset_paths: Set[str] = set()

        for problem in problems:
            for key in dataset_keys:
                path = problem.get(key)
                if path:
                    # Convert to absolute path
                    path_str = str(Path(path).resolve())
                    # Check if file exists
                    if Path(path_str).exists():
                        dataset_paths.add(path_str)

        return sorted(dataset_paths)

    async def _load_dataset(self, path: str) -> Dict[str, Any]:
        """Load a single dataset."""
        async with self._semaphore:
            try:
                path_obj = Path(path)

                # Get file size
                size_bytes = path_obj.stat().st_size
                size_mb = size_bytes / (1024 * 1024)

                # Determine load method
                if self.enable_mmap and size_bytes >= self.mmap_threshold_bytes:
                    # Use memory-mapped file for large datasets
                    data = await self._load_mmap(path_obj)
                    load_method = "mmap"
                else:
                    # Load into memory for small datasets
                    data = await self._load_to_memory(path_obj)
                    load_method = "memory"

                # Store
                self._loaded_datasets[path] = data
                self._dataset_metadata[path] = {
                    "size_bytes": size_bytes,
                    "size_mb": size_mb,
                    "load_method": load_method,
                    "rows": len(data) if hasattr(data, "__len__") else None,
                }

                return self._dataset_metadata[path]

            except Exception as exc:
                logger.error(f"Error loading dataset {path}: {exc}")
                return exc

    async def _load_to_memory(self, path: Path) -> Any:
        """Load dataset into memory (runs in thread pool)."""
        loop = asyncio.get_event_loop()

        def load():
            # Try to load as CSV
            if path.suffix in [".csv", ".CSV"]:
                return pd.read_csv(path)
            # Try to load as JSON
            elif path.suffix in [".json", ".JSON"]:
                import json
                with open(path, "r") as f:
                    return json.load(f)
            # Try to load as pickle
            elif path.suffix in [".pkl", ".pickle", ".PKL", ".PICKLE"]:
                import pickle
                with open(path, "rb") as f:
                    return pickle.load(f)
            else:
                # Return raw bytes for unknown formats
                with open(path, "rb") as f:
                    return f.read()

        return await loop.run_in_executor(None, load)

    async def _load_mmap(self, path: Path) -> mmap.mmap:
        """Load dataset using memory mapping."""
        loop = asyncio.get_event_loop()

        def load():
            # Open file for memory mapping
            fd = os.open(path, os.O_RDONLY)
            try:
                # Create memory mapping
                return mmap.mmap(fd, 0, access=mmap.ACCESS_READ)
            finally:
                # Keep fd open for mmap
                pass

        return await loop.run_in_executor(None, load)

    def get_dataset(self, path: str) -> Optional[Any]:
        """
        Get a preloaded dataset.

        Args:
            path: Path to the dataset

        Returns:
            Preloaded data, or None if not preloaded
        """
        # Normalize path
        path_str = str(Path(path).resolve())
        return self._loaded_datasets.get(path_str)

    def get_metadata(self, path: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a preloaded dataset."""
        path_str = str(Path(path).resolve())
        return self._dataset_metadata.get(path_str)

    def is_preloaded(self, path: str) -> bool:
        """Check if a dataset is preloaded."""
        path_str = str(Path(path).resolve())
        return path_str in self._loaded_datasets

    def get_all_datasets(self) -> Dict[str, Any]:
        """Get all preloaded datasets."""
        return self._loaded_datasets.copy()

    def unload(self, path: str) -> None:
        """
        Unload a dataset from memory.

        For memory-mapped files, this closes the mapping.
        """
        path_str = str(Path(path).resolve())

        if path_str in self._loaded_datasets:
            data = self._loaded_datasets[path_str]

            # Close mmap if applicable
            if isinstance(data, mmap.mmap):
                try:
                    data.close()
                except Exception as exc:
                    logger.warning(f"Error closing mmap for {path_str}: {exc}")

            # Remove from storage
            del self._loaded_datasets[path_str]
            if path_str in self._dataset_metadata:
                del self._dataset_metadata[path_str]

            logger.debug(f"Unloaded dataset: {path_str}")

    def unload_all(self) -> None:
        """Unload all datasets."""
        for path in list(self._loaded_datasets.keys()):
            self.unload(path)

        logger.info("All datasets unloaded")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about preloaded datasets."""
        total_size_mb = sum(
            meta.get("size_mb", 0.0)
            for meta in self._dataset_metadata.values()
        )

        load_methods = {}
        for meta in self._dataset_metadata.values():
            method = meta.get("load_method", "unknown")
            load_methods[method] = load_methods.get(method, 0) + 1

        return {
            "dataset_count": len(self._loaded_datasets),
            "total_size_mb": total_size_mb,
            "load_methods": load_methods,
        }

    def __len__(self) -> int:
        """Return number of preloaded datasets."""
        return len(self._loaded_datasets)


__all__ = [
    "DatasetPreloader",
    "preload_datasets_async",
]


async def preload_datasets_async(
    problems: List[Dict[str, Any]],
    max_concurrency: int = 10,
    enable_mmap: bool = True,
) -> DatasetPreloader:
    """
    Convenience function to preload datasets from problems.

    Args:
        problems: List of problem dictionaries
        max_concurrency: Maximum concurrent load operations
        enable_mmap: Whether to use memory mapping for large files

    Returns:
        DatasetPreloader instance with loaded datasets
    """
    preloader = DatasetPreloader(
        max_concurrency=max_concurrency,
        enable_mmap=enable_mmap,
    )

    await preloader.preload_from_problems(problems)
    return preloader
