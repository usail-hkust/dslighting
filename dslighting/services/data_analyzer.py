"""Compatibility facade over the core data perception runtime."""

import hashlib
import json
import logging
import os
import threading
import time
import traceback
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from dslighting.core.data.introspection.discovery import (
    generate_file_tree as introspection_generate_file_tree,
    stable_directory_fingerprint_entries,
)
from dslighting.core.data.introspection.cache import DataPerceptionCache
from dslighting.core.data.introspection.request import DataPerceptionRequest
from dslighting.core.data.introspection.runtime import DataPerceptionRuntime
from dslighting.core.data.introspection.service import DataPerceptionService
from dslighting.core.types.task import TaskType
from dslighting.utils.constants import (
    DEFAULT_MAX_DEPTH,
    DEFAULT_MAX_FILES,
    DEFAULT_MAX_ITEMS_PER_DIR,
    DEFAULT_CACHE_MAX_ENTRIES,
    FINGERPRINT_MAX_FILES,
)
from dslighting.utils.submission_contract import (
    build_tag_contract_reminder,
    extract_submission_tag_contract,
    find_sample_submission_file,
    normalize_submission_tag_contract,
)

logger = logging.getLogger(__name__)


def generate_file_tree(
    start_path: Path,
    max_depth: int = DEFAULT_MAX_DEPTH,
    max_files: int = DEFAULT_MAX_FILES,
    max_items_per_dir: int = DEFAULT_MAX_ITEMS_PER_DIR,
    display_root_name: Optional[str] = None
) -> str:
    """
    Generates a textual representation of the file tree with intelligent truncation.

    This version prevents a single large directory from consuming the entire file limit,
    and it filters out common noise files.

    Args:
        start_path: The root directory to start the tree from.
        max_depth: The maximum depth to traverse into directories.
        max_files: The global limit for the total number of files to display.
        max_items_per_dir: The maximum number of items (files and dirs) to show per directory.
        display_root_name: An optional name to display for the root directory.
    """
    return introspection_generate_file_tree(
        start_path,
        max_depth=max_depth,
        max_files=max_files,
        max_items_per_dir=max_items_per_dir,
        display_root_name=display_root_name,
    )


__all__ = ["DataAnalyzer", "generate_file_tree"]


class DataAnalyzer:
    """
    Compatibility facade that preserves the legacy DataAnalyzer API while
    delegating prompt-oriented data perception to core.data.introspection.
    """
    CACHE_VERSION = "data_report_v2"
    DEFAULT_ANALYZER_VERSION = "analyzer_v2"
    ANALYZER_VERSION_ENV = "DSLIGHTING_DATA_ANALYZER_VERSION"
    DEFAULT_MAX_ARTIFACTS = 12
    DEFAULT_DOCUMENT_PREVIEW_LINES = 12

    _cache_lock = threading.RLock()
    _memory_cache: "OrderedDict[str, str]" = OrderedDict()
    _key_locks: Dict[str, threading.Lock] = {}

    # Class-level counters for aggregated cache statistics
    _global_cache_hits_memory: int = 0
    _global_cache_hits_disk: int = 0
    _global_cache_misses: int = 0
    _global_cache_write_errors: int = 0

    def __init__(
        self,
        *,
        cache_enabled: bool = True,
        cache_dir: Optional[Path] = None,
        cache_max_entries: int = DEFAULT_CACHE_MAX_ENTRIES,
        cache_debug_metrics: bool = False,
        analyzer_version: Optional[str] = None,
        profile: str = "balanced",
        max_artifacts: int = DEFAULT_MAX_ARTIFACTS,
        max_report_chars: Optional[int] = 14000,
        document_preview_lines: int = DEFAULT_DOCUMENT_PREVIEW_LINES,
        enable_document_inspection: bool = True,
        enable_database_inspection: bool = True,
        tabular_tolerant_fallback: bool = True,
    ):
        self.cache_enabled = bool(cache_enabled)
        self.cache_debug_metrics = bool(cache_debug_metrics)
        self.profile = str(profile or "balanced").strip() or "balanced"
        self.max_artifacts = max(1, int(max_artifacts))
        self.max_report_chars = None if max_report_chars is None else max(1000, int(max_report_chars))
        self.document_preview_lines = max(1, int(document_preview_lines))
        self.enable_document_inspection = bool(enable_document_inspection)
        self.enable_database_inspection = bool(enable_database_inspection)
        self.tabular_tolerant_fallback = bool(tabular_tolerant_fallback)

        # Dynamic cache sizing based on available system memory
        if cache_max_entries == DEFAULT_CACHE_MAX_ENTRIES:
            # Calculate cache size based on available memory
            try:
                import psutil
                available_gb = psutil.virtual_memory().available / (1024**3)
                # Use 100 cache entries per GB of available memory
                calculated_entries = int(available_gb * 100)
                # Clamp between 512 and 4096
                self.cache_max_entries = max(512, min(4096, calculated_entries))
                logger.debug(
                    f"DataAnalyzer: Dynamic cache size set to {self.cache_max_entries} "
                    f"based on {available_gb:.1f}GB available memory"
                )
            except ImportError:
                # psutil not available, use default
                self.cache_max_entries = max(1, int(cache_max_entries))
            except Exception as exc:
                logger.warning("Failed to calculate dynamic cache size, using default: %s", exc)
                self.cache_max_entries = max(1, int(cache_max_entries))
        else:
            # Use explicit value
            self.cache_max_entries = max(1, int(cache_max_entries))

        env_analyzer_version = os.getenv(self.ANALYZER_VERSION_ENV, "").strip()
        explicit_analyzer_version = (analyzer_version or "").strip()
        self.analyzer_version = (
            explicit_analyzer_version
            or env_analyzer_version
            or self.DEFAULT_ANALYZER_VERSION
        )

        # Instance-specific cache debugging metrics
        self._instance_cache_hits_memory = 0
        self._instance_cache_hits_disk = 0
        self._instance_cache_misses = 0
        self._instance_cache_write_errors = 0

        self.cache_dir = self._resolve_cache_dir(cache_dir) if self.cache_enabled else None
        self._perception_cache = DataPerceptionCache(
            enabled=self.cache_enabled,
            cache_dir=self.cache_dir,
            cache_max_entries=self.cache_max_entries,
            analyzer_version=self.analyzer_version,
        )

    @property
    def cache_hits_memory(self) -> int:
        return self._instance_cache_hits_memory

    @property
    def cache_hits_disk(self) -> int:
        return self._instance_cache_hits_disk

    @property
    def cache_misses(self) -> int:
        return self._instance_cache_misses


    @staticmethod
    def _resolve_cache_dir(cache_dir: Optional[Path]) -> Optional[Path]:
        target = cache_dir
        if target is None:
            target = Path.home() / ".cache" / "dslighting" / "data_reports"
        try:
            target = Path(target).expanduser().resolve()
            target.mkdir(parents=True, exist_ok=True)
            return target
        except Exception as exc:
            logger.warning("DataAnalyzer cache dir unavailable (%s), falling back to memory-only cache.", exc)
            return None

    @classmethod
    def _clear_in_memory_cache_for_tests(cls) -> None:
        DataPerceptionCache._clear_in_memory_cache_for_tests()
        with cls._cache_lock:
            cls._memory_cache.clear()
            cls._key_locks.clear()
            cls._global_cache_hits_memory = 0
            cls._global_cache_hits_disk = 0
            cls._global_cache_misses = 0
            cls._global_cache_write_errors = 0

    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """
        获取所有 DataAnalyzer 实例的缓存统计聚合。

        Returns:
            包含缓存统计的字典：
            - hits_memory: 内存缓存命中次数
            - hits_disk: 磁盘缓存命中次数
            - misses: 缓存未命中次数
            - hit_rate: 缓存命中率（0.0-1.0）
            - size_bytes: 内存缓存大小（字节）
            - size_mb: 内存缓存大小（MB）
        """
        total_hits = cls._global_cache_hits_memory + cls._global_cache_hits_disk
        total_accesses = total_hits + cls._global_cache_misses
        hit_rate = (total_hits / total_accesses) if total_accesses > 0 else 0.0

        # 计算内存缓存大小
        size_bytes = 0
        with cls._cache_lock:
            for key, value in cls._memory_cache.items():
                size_bytes += len(key.encode('utf-8')) + len(value.encode('utf-8'))

        return {
            'hits_memory': cls._global_cache_hits_memory,
            'hits_disk': cls._global_cache_hits_disk,
            'misses': cls._global_cache_misses,
            'hit_rate': round(hit_rate, 4),
            'write_errors': cls._global_cache_write_errors,
            'size_bytes': size_bytes,
            'size_mb': round(size_bytes / (1024 * 1024), 4),
            'entries': len(cls._memory_cache),
        }

    @staticmethod
    def _task_type_key(task_type: Optional[TaskType]) -> str:
        return str(task_type) if task_type is not None else ""

    @staticmethod
    def _normalize_task_id(task_id: Optional[str]) -> Optional[str]:
        value = (task_id or "").strip()
        return value or None

    @staticmethod
    def _normalize_submission_context(submission_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not isinstance(submission_context, dict):
            return {}

        normalized: Dict[str, Any] = {}
        for key in (
            "sample_submission_path",
            "submission_filename",
            "submission_format",
        ):
            raw_value = submission_context.get(key)
            if raw_value is None:
                continue
            value = str(raw_value).strip()
            if value:
                normalized[key] = value

        raw_output_path = submission_context.get("output_submission_path")
        if raw_output_path is not None:
            output_value = str(raw_output_path).strip()
            if output_value:
                normalized["output_submission_path"] = output_value

        artifact_payload = submission_context.get("submission_artifact_contract")
        if isinstance(artifact_payload, dict):
            normalized["submission_artifact_contract"] = dict(artifact_payload)

        normalized_contract = normalize_submission_tag_contract(
            submission_context.get("submission_contract")
        )
        if normalized_contract:
            normalized["submission_contract"] = normalized_contract

        return normalized


    def _compute_directory_fingerprint(self, data_dir: Path) -> Dict[str, Any]:
        """
        Compute directory fingerprint with incremental caching.
        Uses a fingerprint cache file to avoid rescanning unchanged directories.
        Limits scan depth to 3 levels to reduce overhead on large directory trees.
        """
        # Check for cached fingerprint
        cache_key_path = data_dir / ".dslighting_fingerprint_cache"
        if cache_key_path.exists():
            try:
                with open(cache_key_path, "r") as f:
                    cached = json.load(f)

                # Check if root directory modification time has changed
                current_mtime = data_dir.stat().st_mtime_ns
                cached_mtime = cached.get("root_mtime_ns", 0)

                if current_mtime <= cached_mtime:
                    # Cache is valid, return cached fingerprint
                    return cached
            except (json.JSONDecodeError, OSError, KeyError) as exc:
                logger.debug("Failed to read fingerprint cache, recomputing: %s", exc)

        entries = stable_directory_fingerprint_entries(data_dir)
        scanned_files = len(entries)
        truncated = scanned_files > FINGERPRINT_MAX_FILES
        if truncated:
            entries = entries[:FINGERPRINT_MAX_FILES]

        try:
            root_stat = data_dir.stat()
            root_mtime_ns = int(root_stat.st_mtime_ns)
            root_size = int(root_stat.st_size)
        except OSError:
            root_mtime_ns = 0
            root_size = 0

        entries.sort()
        fingerprint = {
            "root_mtime_ns": root_mtime_ns,
            "root_size": root_size,
            "scanned_files": scanned_files,
            "truncated": truncated,
            "entries": entries,
        }

        # Save fingerprint cache for future use
        try:
            with open(cache_key_path, "w") as f:
                json.dump(fingerprint, f)
        except (OSError, TypeError) as exc:
            logger.debug("Failed to write fingerprint cache: %s", exc)

        return fingerprint

    def _build_cache_key(
        self,
        data_dir: Path,
        task_type: Optional[TaskType],
        submission_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        try:
            fingerprint = self._compute_directory_fingerprint(data_dir)
            payload = {
                "version": self.CACHE_VERSION,
                "analyzer_version": self.analyzer_version,
                "cache_scope": "fingerprint",
                "task_type": self._task_type_key(task_type),
                "data_dir": str(data_dir.resolve()),
                "submission_context": self._normalize_submission_context(submission_context),
                "fingerprint": {
                    "entries": fingerprint.get("entries", []),
                    "scanned_files": fingerprint.get("scanned_files", 0),
                    "truncated": fingerprint.get("truncated", False),
                },
            }
            raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        except Exception as exc:
            logger.warning("Failed to build DataAnalyzer cache key: %s", exc)
            return None
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _build_task_cache_key(
        self,
        task_id: Optional[str],
        data_dir: Path,
        task_type: Optional[TaskType],
        submission_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        normalized_task_id = self._normalize_task_id(task_id)
        if normalized_task_id is None:
            return None

        payload = {
            "version": self.CACHE_VERSION,
            "analyzer_version": self.analyzer_version,
            "cache_scope": "task_id",
            "task_type": self._task_type_key(task_type),
            "task_id": normalized_task_id,
            "analysis_root": str(data_dir.resolve()),
            "submission_context": self._normalize_submission_context(submission_context),
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _cache_file_path(self, cache_key: str) -> Optional[Path]:
        if not self.cache_dir:
            return None
        return self.cache_dir / cache_key[:2] / f"{cache_key}.json"

    @classmethod
    def _get_key_lock(cls, cache_key: str) -> threading.Lock:
        with cls._cache_lock:
            lock = cls._key_locks.get(cache_key)
            if lock is None:
                lock = threading.Lock()
                cls._key_locks[cache_key] = lock
            return lock

    def _memory_get(self, cache_key: str) -> Optional[str]:
        with self._cache_lock:
            value = self._memory_cache.get(cache_key)
            if value is None:
                return None
            self._memory_cache.move_to_end(cache_key)
            self._instance_cache_hits_memory += 1
            DataAnalyzer._global_cache_hits_memory += 1 # Increment class-level counter
            return value

    def _memory_put(self, cache_key: str, report: str) -> None:
        with self._cache_lock:
            self._memory_cache[cache_key] = report
            self._memory_cache.move_to_end(cache_key)
            while len(self._memory_cache) > self.cache_max_entries:
                self._memory_cache.popitem(last=False)

    def _disk_read(self, cache_key: str) -> Optional[str]:
        cache_path = self._cache_file_path(cache_key)
        if cache_path is None or not cache_path.exists():
            return None
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            if not isinstance(payload, dict):
                return None
            if payload.get("version") != self.CACHE_VERSION:
                return None
            if payload.get("analyzer_version") != self.analyzer_version:
                return None
            report = payload.get("report")
            if isinstance(report, str):
                self._instance_cache_hits_disk += 1
                DataAnalyzer._global_cache_hits_disk += 1  # Increment class-level counter
                return report
        except Exception as exc:
            logger.warning("Failed to read DataAnalyzer disk cache '%s': %s", cache_path, exc)
        return None

    def _disk_write(
        self,
        cache_key: str,
        report: str,
        task_type: Optional[TaskType],
        data_dir: Path,
        *,
        task_id: Optional[str] = None,
        cache_scope: str = "fingerprint",
    ) -> None:
        cache_path = self._cache_file_path(cache_key)
        if cache_path is None:
            return
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": self.CACHE_VERSION,
                "analyzer_version": self.analyzer_version,
                "created_at": time.time(),
                "cache_scope": cache_scope,
                "task_type": self._task_type_key(task_type),
                "task_id": self._normalize_task_id(task_id),
                "data_dir": str(data_dir.resolve()),
                "report": report,
            }
            temp_path = cache_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)
            os.replace(temp_path, cache_path)
        except Exception as exc:
            DataAnalyzer._global_cache_write_errors += 1  # Increment class-level counter
            logger.warning("Failed to write DataAnalyzer disk cache '%s': %s", cache_path, exc)

    async def _disk_write_async(
        self,
        cache_key: str,
        report: str,
        task_type: Optional[TaskType],
        data_dir: Path,
        *,
        task_id: Optional[str] = None,
        cache_scope: str = "fingerprint",
    ) -> None:
        """
        Async version of disk write using aiofiles for better performance.
        Falls back to sync write if aiofiles is not available.
        """
        cache_path = self._cache_file_path(cache_key)
        if cache_path is None:
            return

        try:
            import aiofiles
        except ImportError:
            # Fall back to sync write if aiofiles is not available
            logger.debug("aiofiles not available, falling back to sync write")
            return self._disk_write(cache_key, report, task_type, data_dir, task_id=task_id, cache_scope=cache_scope)

        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": self.CACHE_VERSION,
                "analyzer_version": self.analyzer_version,
                "created_at": time.time(),
                "cache_scope": cache_scope,
                "task_type": self._task_type_key(task_type),
                "task_id": self._normalize_task_id(task_id),
                "data_dir": str(data_dir.resolve()),
                "report": report,
            }
            temp_path = cache_path.with_suffix(".tmp")
            async with aiofiles.open(temp_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(payload, ensure_ascii=False))
            os.replace(temp_path, cache_path)
        except Exception as exc:
            DataAnalyzer._global_cache_write_errors += 1  # Increment class-level counter
            logger.warning("Failed to write DataAnalyzer disk cache (async) '%s': %s", cache_path, exc)

    def _log_cache_event(self, event: str, cache_key: str, started_at: float) -> None:
        if not self.cache_debug_metrics:
            return
        elapsed_ms = round((time.perf_counter() - started_at) * 1000.0, 2)
        logger.debug(
            "DataAnalyzer cache %s key=%s elapsed_ms=%s hits(mem=%s,disk=%s) misses=%s",
            event,
            cache_key[:12],
            elapsed_ms,
            self.cache_hits_memory,
            self.cache_hits_disk,
            self.cache_misses,
        )

    def analyze(
        self,
        data_dir: Path,
        output_filename: str,
        task_type: Optional[TaskType] = None,
        optimization_context: bool = False,
        task_id: Optional[str] = None,
        submission_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Analyzes the data directory and returns a formatted overview string,
        including critical I/O instructions.
        """
        report = self.analyze_data(
            data_dir,
            task_type,
            task_id=task_id,
            submission_context=submission_context,
        )
        report += self.generate_io_instructions(
            output_filename,
            optimization_context,
            submission_context=submission_context,
        )
        return report

    def analyze_data(
        self,
        data_dir: Path,
        task_type: Optional[TaskType] = None,
        task_id: Optional[str] = None,
        submission_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Analyzes the data directory and returns ONLY the data report (structure, format, etc.).
        Does NOT include I/O instructions.
        """
        data_dir = Path(data_dir) if data_dir is not None else None
        if not data_dir or not data_dir.exists() or not data_dir.is_dir():
            logger.error(f"Data directory issue during analysis: {data_dir}")
            return "Error: Input data directory not found, not provided, or is not a directory."

        normalized_submission_context = self._normalize_submission_context(submission_context)

        if not self.cache_enabled:
            return self._compute_data_report(
                data_dir,
                task_type,
                submission_context=normalized_submission_context,
            )

        started_at = time.perf_counter()
        cache_scope = "task_id"
        cache_key = self._build_task_cache_key(
            task_id,
            data_dir,
            task_type,
            submission_context=normalized_submission_context,
        )
        if cache_key is None:
            cache_scope = "fingerprint"
            cache_key = self._build_cache_key(
                data_dir,
                task_type,
                submission_context=normalized_submission_context,
            )
        if not cache_key:
            # If cache key can't be built, treat as a miss and proceed without caching.
            self._instance_cache_misses += 1
            self._global_cache_misses += 1
            return self._compute_data_report(
                data_dir,
                task_type,
                submission_context=normalized_submission_context,
            )

        # _memory_get and _disk_read will now increment their respective global hit counters.
        # We only need to increment misses if both memory and disk fail to provide a hit.

        cached = self._memory_get(cache_key)
        if cached is not None:
            self._log_cache_event("hit(memory)", cache_key, started_at)
            return cached

        key_lock = self._get_key_lock(cache_key)
        with key_lock:
            # Check memory cache again after acquiring lock (double-checked locking)
            cached = self._memory_get(cache_key)
            if cached is not None:
                self._log_cache_event("hit(memory-after-lock)", cache_key, started_at)
                return cached

            cached = self._disk_read(cache_key)
            if cached is not None:
                self._memory_put(cache_key, cached)
                self._log_cache_event("hit(disk)", cache_key, started_at)
                return cached

            self._instance_cache_misses += 1
            self._global_cache_misses += 1 # Increment class-level counter for a true miss
            report = self._compute_data_report(
                data_dir,
                task_type,
                submission_context=normalized_submission_context,
            )
            self._memory_put(cache_key, report)
            self._disk_write(
                cache_key,
                report,
                task_type,
                data_dir,
                task_id=task_id,
                cache_scope=cache_scope,
            )
            self._log_cache_event("miss", cache_key, started_at)
            return report

    def _compute_data_report(
        self,
        data_dir: Path,
        task_type: Optional[TaskType] = None,
        submission_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Compute a fresh report via the core.data introspection runtime."""
        request = self._build_perception_request(
            data_dir,
            task_type=task_type,
            submission_context=submission_context,
        )
        report = DataPerceptionService(request, cache=self._perception_cache).build_report()
        artifact_analysis = DataPerceptionRuntime._analyze_submission_artifact_requirements(
            submission_context or {}
        )
        if artifact_analysis:
            report += f"## Submission Artifact Requirements\n{artifact_analysis}\n\n"

        if task_type == "kaggle":
            contract = DataPerceptionRuntime._coerce_submission_artifact_contract(submission_context)
            submission_analysis = ""
            if contract is None or contract.root_kind == "file":
                submission_analysis = self._analyze_kaggle_submission_format(
                    data_dir,
                    submission_context=submission_context,
                )
            if submission_analysis:
                report += f"## Submission Format Requirements\n{submission_analysis}\n\n"

        return report

    def _build_perception_request(
        self,
        data_dir: Path,
        *,
        task_type: Optional[TaskType],
        submission_context: Optional[Dict[str, Any]],
    ) -> DataPerceptionRequest:
        return DataPerceptionRequest(
            data_dir=data_dir,
            task_type=task_type,
            task_id=None,
            submission_context=submission_context or {},
            profile=self.profile,
            max_artifacts=self.max_artifacts,
            max_report_chars=self.max_report_chars,
            document_preview_lines=self.document_preview_lines,
            enable_document_inspection=self.enable_document_inspection,
            enable_database_inspection=self.enable_database_inspection,
            tabular_tolerant_fallback=self.tabular_tolerant_fallback,
        )

    def generate_io_instructions(
        self,
        output_filename: str,
        optimization_context: bool = False,
        submission_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate standardized I/O instructions reflecting that CWD is the input directory."""
        return DataPerceptionRuntime.generate_io_instructions(
            output_filename,
            optimization_context,
            submission_context=submission_context,
        )

    def _analyze_kaggle_submission_format(
        self,
        data_dir: Path,
        submission_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Analyze sample submission requirements for Kaggle-style tasks.

        Supports CSV/TSV, NPY, JSONL, and Parquet. Falls back to generic file-level
        guidance for unknown formats.
        """
        context = self._normalize_submission_context(submission_context)
        sample_submission_file = self._find_sample_submission(
            data_dir,
            submission_context=context,
        )

        submission_contract = normalize_submission_tag_contract(
            context.get("submission_contract")
        )
        if not submission_contract:
            submission_contract = extract_submission_tag_contract(sample_submission_file)
        tag_contract_reminder = build_tag_contract_reminder(submission_contract)

        def with_tag_contract(message: str) -> str:
            base = message.rstrip()
            if tag_contract_reminder:
                return f"{base}\n\n{tag_contract_reminder}\n"
            return f"{base}\n"

        if not sample_submission_file:
            return f"{tag_contract_reminder}\n" if tag_contract_reminder else ""

        suffix = sample_submission_file.suffix.lower()

        try:
            if suffix in {".csv", ".tsv"}:
                sep = "\t" if suffix == ".tsv" else ","
                sample_df = pd.read_csv(sample_submission_file, sep=sep, nrows=2000)

                head_info = sample_df.head().to_string(index=False)
                dtypes_info = sample_df.dtypes.to_string()
                required_columns = sample_df.columns.tolist()

                columns_instruction = f"""
**Required Submission Columns:**
Your submission file MUST contain the following columns in this exact order:
```
{required_columns}
```
This is a strict requirement for the submission to be graded correctly.
"""

                return with_tag_contract(f"""
**CRITICAL:** Your final submission file MUST EXACTLY match the sample submission format (`{sample_submission_file.name}`).
This includes column names, column order, and data types.

{columns_instruction}

**Format Details:**
*First rows preview:*
```text
{head_info}
```

*Detected data types:*
```text
{dtypes_info}
```
""")

            if suffix == ".npy":
                try:
                    arr = np.load(sample_submission_file, mmap_mode="r", allow_pickle=False)
                except ValueError:
                    arr = np.load(sample_submission_file, mmap_mode="r", allow_pickle=True)

                flat_preview = arr.reshape(-1)[:5].tolist() if getattr(arr, "size", 0) else []
                return with_tag_contract(f"""
**CRITICAL:** Your final submission file must follow the NumPy array format shown by `{sample_submission_file.name}`.

**Format Details:**
- File type: `npy`
- Shape: `{tuple(int(dim) for dim in arr.shape)}`
- Dtype: `{arr.dtype}`
- Value preview: `{flat_preview}`
""")

            if suffix == ".jsonl":
                preview_lines: List[str] = []
                parsed_rows: List[Any] = []
                with open(sample_submission_file, "r", encoding="utf-8", errors="ignore") as f:
                    for _ in range(5):
                        line = f.readline()
                        if not line:
                            break
                        line = line.rstrip("\n")
                        if not line.strip():
                            continue
                        preview_lines.append(line)
                        try:
                            parsed_rows.append(json.loads(line))
                        except json.JSONDecodeError:
                            parsed_rows.append(line)

                key_summary = ""
                if parsed_rows and all(isinstance(row, dict) for row in parsed_rows):
                    keys = sorted({k for row in parsed_rows for k in row.keys()})
                    key_summary = f"\n- Detected keys: `{keys}`"

                preview = "\n".join(preview_lines) if preview_lines else "(empty sample)"
                return with_tag_contract(f"""
**CRITICAL:** Your final submission file must match the JSONL structure of `{sample_submission_file.name}`.

**Format Details:**
- File type: `jsonl`{key_summary}
- Line preview:
```text
{preview}
```
""")

            if suffix == ".parquet":
                sample_df = pd.read_parquet(sample_submission_file).head(5)
                head_info = sample_df.to_string(index=False)
                dtypes_info = sample_df.dtypes.to_string()
                required_columns = sample_df.columns.tolist()

                return with_tag_contract(f"""
**CRITICAL:** Your final submission file must follow the Parquet schema of `{sample_submission_file.name}`.

**Format Details:**
- Required columns (order preserved): `{required_columns}`
- Dtypes:
```text
{dtypes_info}
```
- Row preview:
```text
{head_info}
```
""")

            return with_tag_contract(f"""
**CRITICAL:** Your final submission must match the sample submission file `{sample_submission_file.name}`.

Detected format: `{suffix or '<no extension>'}`.
Please inspect this file directly and preserve its structure exactly.
""")

        except Exception:
            logger.warning(
                "Could not parse sample submission file '%s': %s",
                sample_submission_file,
                traceback.format_exc(),
            )
            return with_tag_contract(f"""
**CRITICAL:** Your final submission file MUST match the format of `{sample_submission_file.name}`.
(Automatic format analysis failed; inspect the sample file manually.)
""")

    def _find_sample_submission(
        self,
        data_dir: Path,
        submission_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Path]:
        """Locate sample submission file with explicit metadata first, then heuristics."""
        context = self._normalize_submission_context(submission_context)

        try:
            return find_sample_submission_file(
                data_dir,
                sample_submission_path=str(context.get("sample_submission_path", "") or ""),
                submission_filename=str(context.get("submission_filename", "") or ""),
            )
        except Exception:
            logger.warning("Could not scan data directory '%s': %s", data_dir, traceback.format_exc())
            return None
