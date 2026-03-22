"""Structured cache for data perception inventories and artifact summaries."""

from __future__ import annotations

import hashlib
import json
import os
import threading
from collections import OrderedDict
from pathlib import Path
from typing import Any

from .discovery import stable_directory_fingerprint_entries
from .models import ArtifactDescriptor, ArtifactSummary, DataInventory
from .request import DataPerceptionRequest


class DataPerceptionCache:
    """Cache structured data perception artifacts across service instances."""

    CACHE_VERSION = "perception_cache_v1"

    _cache_lock = threading.RLock()
    _memory_cache: "OrderedDict[str, dict[str, Any]]" = OrderedDict()
    _key_locks: dict[str, threading.Lock] = {}

    def __init__(
        self,
        *,
        enabled: bool,
        cache_dir: Path | None,
        cache_max_entries: int,
        analyzer_version: str,
    ) -> None:
        self.enabled = bool(enabled)
        self.cache_dir = cache_dir if self.enabled else None
        self.cache_max_entries = max(1, int(cache_max_entries))
        self.analyzer_version = analyzer_version

    @classmethod
    def _clear_in_memory_cache_for_tests(cls) -> None:
        with cls._cache_lock:
            cls._memory_cache.clear()
            cls._key_locks.clear()

    def get_inventory(self, request: DataPerceptionRequest) -> DataInventory | None:
        if not self.enabled:
            return None
        key = self._build_inventory_key(request)
        payload = self._read_payload(key)
        if not payload:
            return None
        return self._deserialize_inventory(request, payload)

    def put_inventory(self, request: DataPerceptionRequest, inventory: DataInventory) -> None:
        if not self.enabled:
            return
        key = self._build_inventory_key(request)
        payload = {
            "kind": "inventory",
            "inventory": self._serialize_inventory(inventory),
        }
        self._write_payload(key, payload)

    def get_summary(
        self,
        request: DataPerceptionRequest,
        descriptor: ArtifactDescriptor,
    ) -> ArtifactSummary | None:
        if not self.enabled:
            return None
        key = self._build_summary_key(request, descriptor)
        payload = self._read_payload(key)
        if not payload:
            return None
        return self._deserialize_summary(request, payload)

    def put_summary(
        self,
        request: DataPerceptionRequest,
        summary: ArtifactSummary,
    ) -> None:
        if not self.enabled:
            return
        key = self._build_summary_key(request, summary.descriptor)
        payload = {
            "kind": "summary",
            "summary": self._serialize_summary(summary),
        }
        self._write_payload(key, payload)

    def _build_inventory_key(self, request: DataPerceptionRequest) -> str:
        payload = {
            "version": self.CACHE_VERSION,
            "analyzer_version": self.analyzer_version,
            "cache_scope": "inventory",
            "data_dir": str(request.data_dir.resolve()),
            "profile": request.profile,
            "max_artifacts": request.max_artifacts,
            "enable_document_inspection": request.enable_document_inspection,
            "enable_database_inspection": request.enable_database_inspection,
            "submission_context": request.submission_context,
            "fingerprint_entries": stable_directory_fingerprint_entries(request.data_dir),
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _build_summary_key(self, request: DataPerceptionRequest, descriptor: ArtifactDescriptor) -> str:
        try:
            stat = descriptor.path.stat()
            mtime_ns = int(stat.st_mtime_ns)
            size_bytes = int(stat.st_size)
        except OSError:
            mtime_ns = 0
            size_bytes = descriptor.size_bytes

        payload = {
            "version": self.CACHE_VERSION,
            "analyzer_version": self.analyzer_version,
            "cache_scope": "summary",
            "data_dir": str(request.data_dir.resolve()),
            "relative_path": descriptor.relative_path,
            "kind": descriptor.kind,
            "role": descriptor.role,
            "size_bytes": size_bytes,
            "mtime_ns": mtime_ns,
            "document_preview_lines": request.document_preview_lines,
            "tabular_tolerant_fallback": request.tabular_tolerant_fallback,
            "profile": request.profile,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _cache_file_path(self, cache_key: str) -> Path | None:
        if self.cache_dir is None:
            return None
        return self.cache_dir / "perception" / cache_key[:2] / f"{cache_key}.json"

    @classmethod
    def _get_key_lock(cls, cache_key: str) -> threading.Lock:
        with cls._cache_lock:
            lock = cls._key_locks.get(cache_key)
            if lock is None:
                lock = threading.Lock()
                cls._key_locks[cache_key] = lock
            return lock

    def _read_payload(self, cache_key: str) -> dict[str, Any] | None:
        cached = self._memory_get(cache_key)
        if cached is not None:
            return cached

        key_lock = self._get_key_lock(cache_key)
        with key_lock:
            cached = self._memory_get(cache_key)
            if cached is not None:
                return cached
            payload = self._disk_read(cache_key)
            if payload is not None:
                self._memory_put(cache_key, payload)
            return payload

    def _write_payload(self, cache_key: str, payload: dict[str, Any]) -> None:
        self._memory_put(cache_key, payload)
        self._disk_write(cache_key, payload)

    def _memory_get(self, cache_key: str) -> dict[str, Any] | None:
        with self._cache_lock:
            payload = self._memory_cache.get(cache_key)
            if payload is None:
                return None
            self._memory_cache.move_to_end(cache_key)
            return payload

    def _memory_put(self, cache_key: str, payload: dict[str, Any]) -> None:
        with self._cache_lock:
            self._memory_cache[cache_key] = payload
            self._memory_cache.move_to_end(cache_key)
            while len(self._memory_cache) > self.cache_max_entries:
                self._memory_cache.popitem(last=False)

    def _disk_read(self, cache_key: str) -> dict[str, Any] | None:
        cache_path = self._cache_file_path(cache_key)
        if cache_path is None or not cache_path.exists():
            return None
        try:
            with open(cache_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if not isinstance(payload, dict):
                return None
            if payload.get("version") != self.CACHE_VERSION:
                return None
            if payload.get("analyzer_version") != self.analyzer_version:
                return None
            return payload.get("payload")
        except Exception:
            return None

    def _disk_write(self, cache_key: str, payload: dict[str, Any]) -> None:
        cache_path = self._cache_file_path(cache_key)
        if cache_path is None:
            return
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = cache_path.with_suffix(".tmp")
            envelope = {
                "version": self.CACHE_VERSION,
                "analyzer_version": self.analyzer_version,
                "payload": payload,
            }
            with open(temp_path, "w", encoding="utf-8") as handle:
                json.dump(envelope, handle, ensure_ascii=False)
            os.replace(temp_path, cache_path)
        except Exception:
            return

    @staticmethod
    def _serialize_descriptor(descriptor: ArtifactDescriptor) -> dict[str, Any]:
        return {
            "relative_path": descriptor.relative_path,
            "suffix": descriptor.suffix,
            "size_bytes": descriptor.size_bytes,
            "kind": descriptor.kind,
            "role": descriptor.role,
            "origin": descriptor.origin,
            "accessible_to_agent": descriptor.accessible_to_agent,
        }

    @staticmethod
    def _deserialize_descriptor(request: DataPerceptionRequest, payload: dict[str, Any]) -> ArtifactDescriptor:
        relative_path = str(payload["relative_path"])
        return ArtifactDescriptor(
            path=request.data_dir / relative_path,
            relative_path=relative_path,
            suffix=str(payload["suffix"]),
            size_bytes=int(payload["size_bytes"]),
            kind=str(payload["kind"]),
            role=str(payload["role"]),
            origin=str(payload.get("origin", "filesystem")),
            accessible_to_agent=bool(payload.get("accessible_to_agent", True)),
        )

    def _serialize_summary(self, summary: ArtifactSummary) -> dict[str, Any]:
        return {
            "descriptor": self._serialize_descriptor(summary.descriptor),
            "status": summary.status,
            "detail_lines": list(summary.detail_lines),
            "table_text": summary.table_text,
            "diagnostics": list(summary.diagnostics),
        }

    def _deserialize_summary(
        self,
        request: DataPerceptionRequest,
        payload: dict[str, Any],
    ) -> ArtifactSummary:
        summary_payload = payload["summary"]
        return ArtifactSummary(
            descriptor=self._deserialize_descriptor(request, summary_payload["descriptor"]),
            status=str(summary_payload["status"]),
            detail_lines=list(summary_payload.get("detail_lines", [])),
            table_text=summary_payload.get("table_text"),
            diagnostics=list(summary_payload.get("diagnostics", [])),
        )

    def _serialize_inventory(self, inventory: DataInventory) -> dict[str, Any]:
        return {
            "artifacts": [self._serialize_descriptor(descriptor) for descriptor in inventory.artifacts],
            "directory_structure_text": inventory.directory_structure_text,
            "counts": dict(inventory.counts),
            "warnings": list(inventory.warnings),
        }

    def _deserialize_inventory(
        self,
        request: DataPerceptionRequest,
        payload: dict[str, Any],
    ) -> DataInventory:
        inventory_payload = payload["inventory"]
        return DataInventory(
            artifacts=[
                self._deserialize_descriptor(request, descriptor_payload)
                for descriptor_payload in inventory_payload.get("artifacts", [])
            ],
            directory_structure_text=str(inventory_payload.get("directory_structure_text", "")),
            counts=dict(inventory_payload.get("counts", {})),
            warnings=list(inventory_payload.get("warnings", [])),
        )
