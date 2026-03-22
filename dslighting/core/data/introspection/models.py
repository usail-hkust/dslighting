"""Structured models for data perception and prompt rendering."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Literal, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .request import DataPerceptionRequest


ArtifactKind = Literal["tabular", "document", "database", "other"]
ArtifactRole = Literal[
    "input_table",
    "schema_doc",
    "output_template",
    "database_template",
    "auxiliary_doc",
    "unknown",
]
ArtifactStatus = Literal["ok", "degraded", "error"]


@dataclass(frozen=True)
class ArtifactDescriptor:
    path: Path
    relative_path: str
    suffix: str
    size_bytes: int
    kind: ArtifactKind
    role: ArtifactRole
    origin: Literal["filesystem", "contract", "synthetic"] = "filesystem"
    accessible_to_agent: bool = True


@dataclass
class ArtifactSummary:
    descriptor: ArtifactDescriptor
    status: ArtifactStatus
    detail_lines: List[str] = field(default_factory=list)
    table_text: Optional[str] = None
    diagnostics: List[str] = field(default_factory=list)


@dataclass
class DataInventory:
    artifacts: List[ArtifactDescriptor] = field(default_factory=list)
    directory_structure_text: str = ""
    counts: Dict[str, int] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


@dataclass
class AgentDataContext:
    request: "DataPerceptionRequest"
    inventory: DataInventory
    summaries: List[ArtifactSummary] = field(default_factory=list)
    detail_artifacts: List[str] = field(default_factory=list)
    omitted_artifacts: List[str] = field(default_factory=list)
