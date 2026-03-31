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
class PromptRenderPolicy:
    """Controls how the renderer selects content density for each section.

    Decision authority: PromptBudgetManager is the sole writer of this policy.
    PromptReportRenderer is the sole reader — it never makes its own length decisions.

    Fields:
        submission_format_mode: Whether to render Submission Format Requirements at full
            or compact density.
        io_requirements_mode: Whether to render CRITICAL I/O REQUIREMENTS at full or
            compact density.
        folded_detail_artifacts: Subset of detail_artifacts that receive condensed
            rendering (header + role/status + column summary, no table_text).
            Must be a subset of AgentDataContext.detail_artifacts.
    """
    submission_format_mode: Literal["full", "compact"] = "full"
    io_requirements_mode: Literal["full", "compact"] = "full"
    folded_detail_artifacts: List[str] = field(default_factory=list)


@dataclass
class AgentDataContext:
    """Structured context passed through the budget → render pipeline.

    Artifact render states (three-tier):
        detail_artifacts:   fully rendered (header + detail_lines + table_text)
        render_policy.folded_detail_artifacts: condensed (header + summary, no table_text);
            must be a subset of detail_artifacts
        omitted_artifacts:  not rendered at all; only counted in Inventory Summary

    Critical sections (always rendered, never omitted):
        submission_artifact_requirements: Submission Artifact Requirements block text
        submission_format_requirements_full / _compact: two densities for Submission
            Format Requirements; render_policy decides which is used
        io_requirements_full / _compact: two densities for CRITICAL I/O REQUIREMENTS;
            render_policy decides which is used; empty string if not applicable
    """
    request: "DataPerceptionRequest"
    inventory: DataInventory
    summaries: List[ArtifactSummary] = field(default_factory=list)
    detail_artifacts: List[str] = field(default_factory=list)
    omitted_artifacts: List[str] = field(default_factory=list)

    # Critical sections — populated by DataPerceptionRuntime after service builds base context
    submission_artifact_requirements: str = ""
    submission_format_requirements_full: str = ""
    submission_format_requirements_compact: str = ""
    io_requirements_full: str = ""
    io_requirements_compact: str = ""

    # Render policy — written exclusively by PromptBudgetManager
    render_policy: PromptRenderPolicy = field(default_factory=PromptRenderPolicy)
