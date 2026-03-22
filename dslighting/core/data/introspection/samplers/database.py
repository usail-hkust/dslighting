"""Database artifact sampling."""

from __future__ import annotations

import sqlite3

from ..models import ArtifactDescriptor, ArtifactSummary


class DatabaseSampler:
    def summarize(self, descriptor: ArtifactDescriptor) -> ArtifactSummary:
        with sqlite3.connect(descriptor.path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
            tables = [row[0] for row in cursor.fetchall()]

        detail_lines = [
            "Kind: sqlite database",
            f"Detected Tables ({len(tables)}):" if tables else "Detected Tables: none",
        ]
        detail_lines.extend(f"- {table_name}" for table_name in tables[:12])
        return ArtifactSummary(
            descriptor=descriptor,
            status="ok",
            detail_lines=detail_lines,
        )
