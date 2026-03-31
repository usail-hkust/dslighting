"""Artifact discovery utilities for agent-visible datasets."""

from __future__ import annotations

from itertools import islice
import os
from pathlib import Path
from typing import List

from dslighting.utils.constants import (
    DEEP_DISCOVERY_MAX_DIRS,
    DEFAULT_MAX_DEPTH,
    DEFAULT_MAX_FILES,
    DEFAULT_MAX_ITEMS_PER_DIR,
    FINGERPRINT_MAX_FILES,
    FINGERPRINT_SCAN_DEPTH,
)

from .classifier import classify_artifact
from .models import ArtifactDescriptor
from .request import DataPerceptionRequest


def generate_file_tree(
    start_path: Path,
    max_depth: int = DEFAULT_MAX_DEPTH,
    max_files: int = DEFAULT_MAX_FILES,
    max_items_per_dir: int = DEFAULT_MAX_ITEMS_PER_DIR,
    display_root_name: str | None = None,
) -> str:
    """Generate a truncated textual tree view for prompt rendering."""
    tree: List[str] = []
    start_path = Path(start_path)
    if not start_path.exists():
        return f"Directory not found: {start_path}"

    base_name = display_root_name if display_root_name is not None else start_path.name
    file_count = 0
    global_limit_reached = False

    def _walk(path: Path, prefix: str, depth: int) -> None:
        nonlocal file_count, global_limit_reached

        if depth > max_depth or global_limit_reached:
            return

        try:
            sampled = list(islice(path.iterdir(), max_items_per_dir + 1))
        except OSError:
            tree.append(f"{prefix}└── [Error reading directory]")
            return

        truncated_in_dir = len(sampled) > max_items_per_dir
        display_items = sampled[: max(1, max_items_per_dir // 2)] if truncated_in_dir else sampled
        display_items = sorted(display_items, key=lambda p: p.name)

        pointers = ["├── "] * (len(display_items) - 1) + ["└── "]
        if truncated_in_dir and pointers:
            pointers[-1] = "├── "

        for pointer, sub_path in zip(pointers, display_items):
            if global_limit_reached:
                return
            if not sub_path.is_dir():
                if file_count >= max_files:
                    global_limit_reached = True
                    return
                file_count += 1

            display_name = sub_path.name + ("/" if sub_path.is_dir() else "")
            tree.append(f"{prefix}{pointer}{display_name}")

            if sub_path.is_dir():
                extension = "│   " if pointer == "├── " else "    "
                _walk(sub_path, prefix=prefix + extension, depth=depth + 1)

        if truncated_in_dir:
            tree.append(f"{prefix}└── [... more items truncated ...]")

    tree.append(f"{base_name}/")
    _walk(start_path, prefix="", depth=1)

    if global_limit_reached:
        tree.append(f"\n[... Truncated. Total file limit ({max_files}) reached ...]")

    return "\n".join(tree)


def discover_artifacts(request: DataPerceptionRequest) -> List[ArtifactDescriptor]:
    """Discover agent-visible files that should enter the perception pipeline."""
    artifacts: List[ArtifactDescriptor] = []
    queue: List[tuple[Path, int]] = [(request.data_dir, 0)]
    visited_dirs = 0
    max_depth = 1 if request.profile == "fast" else 2
    per_dir_limit = max(8, DEFAULT_MAX_ITEMS_PER_DIR)

    while queue and len(artifacts) < request.max_artifacts and visited_dirs < DEEP_DISCOVERY_MAX_DIRS:
        current_dir, depth = queue.pop(0)
        visited_dirs += 1
        try:
            sampled = list(islice(current_dir.iterdir(), per_dir_limit + 1))
        except OSError:
            continue

        truncated = len(sampled) > per_dir_limit
        entries = sorted(sampled[:per_dir_limit] if truncated else sampled, key=lambda p: p.name)

        for entry in entries:
            if entry.is_dir():
                if depth < max_depth:
                    queue.append((entry, depth + 1))
                continue
            if entry.name.startswith("."):
                continue

            descriptor = classify_artifact(entry, request)
            if descriptor is None:
                continue
            artifacts.append(descriptor)
            if len(artifacts) >= request.max_artifacts:
                break

    return artifacts


def stable_directory_fingerprint_entries(data_dir: Path) -> list[tuple[str, int, int]]:
    """Return stable file fingerprint entries without self-generated cache files."""
    entries: list[tuple[str, int, int]] = []
    scanned_files = 0
    truncated = False
    for root, dir_names, file_names in os.walk(data_dir):
        try:
            rel_path = Path(root).relative_to(data_dir)
            depth = len(rel_path.parts) if str(rel_path) != "." else 0
        except ValueError:
            depth = 0
        if depth > FINGERPRINT_SCAN_DEPTH:
            dir_names.clear()
            continue

        file_names.sort()
        for file_name in file_names:
            if file_name == ".dslighting_fingerprint_cache":
                continue
            scanned_files += 1
            if scanned_files > FINGERPRINT_MAX_FILES:
                truncated = True
                break
            file_path = Path(root) / file_name
            try:
                stat = file_path.stat()
            except OSError:
                continue
            rel_path = file_path.relative_to(data_dir).as_posix()
            entries.append((rel_path, int(stat.st_size), int(stat.st_mtime_ns)))
        if truncated:
            break
    entries.sort()
    return entries
