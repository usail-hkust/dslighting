"""Prompt renderer for structured data perception."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..models import AgentDataContext, ArtifactSummary

RenderProfile = Literal["data_report", "combined_report"]


@dataclass
class RenderedSectionSpan:
    """Span metadata for a single rendered section within the prompt text."""
    name: str
    start: int
    end: int
    kind: str
    critical: bool
    foldable: bool


@dataclass
class PromptRenderResult:
    """Output of render_with_map(): the rendered text plus structural section metadata."""
    text: str
    section_map: list[RenderedSectionSpan]


class PromptReportRenderer:
    """Render AgentDataContext into a structured prompt.

    Two render profiles are supported:
        data_report:     Directory → Inventory → Submission Artifact Req →
                         Submission Format Req → Data Schema Analysis
        combined_report: same as data_report but also includes CRITICAL I/O REQUIREMENTS
                         before Data Schema Analysis

    The renderer is a pure function: it never makes length/budget decisions.
    All policy decisions are made by PromptBudgetManager via AgentDataContext.render_policy.
    """

    def render(self, context: AgentDataContext, profile: RenderProfile = "data_report") -> str:
        return self.render_with_map(context, profile).text

    def render_with_map(
        self,
        context: AgentDataContext,
        profile: RenderProfile = "data_report",
    ) -> PromptRenderResult:
        """Render to text and return structural section metadata alongside."""
        text_parts: list[str] = []
        spans: list[RenderedSectionSpan] = []

        def _append(chunk: str, *, name: str, kind: str, critical: bool, foldable: bool) -> None:
            if not chunk:
                return
            start = sum(len(p) for p in text_parts)
            text_parts.append(chunk)
            end = start + len(chunk)
            spans.append(RenderedSectionSpan(
                name=name, start=start, end=end,
                kind=kind, critical=critical, foldable=foldable,
            ))

        _append(
            "\n\n--- COMPREHENSIVE DATA REPORT ---\n\n",
            name="header", kind="header", critical=True, foldable=False,
        )
        _append(
            self.render_directory_section(context),
            name="Directory Structure", kind="directory", critical=False, foldable=False,
        )

        inv = self.render_inventory_summary(context)
        if inv:
            _append(inv, name="Data Inventory Summary", kind="inventory", critical=False, foldable=False)

        if context.submission_artifact_requirements:
            _append(
                f"## Submission Artifact Requirements\n"
                f"{context.submission_artifact_requirements}\n\n",
                name="Submission Artifact Requirements", kind="submission_artifact",
                critical=True, foldable=False,
            )

        sub_fmt = self._pick_submission_format(context)
        if sub_fmt:
            _append(
                f"## Submission Format Requirements\n{sub_fmt}\n\n",
                name="Submission Format Requirements", kind="submission_format",
                critical=True, foldable=False,
            )

        if profile == "combined_report":
            io_req = self._pick_io_requirements(context)
            if io_req:
                _append(
                    io_req,
                    name="CRITICAL I/O REQUIREMENTS", kind="io_requirements",
                    critical=True, foldable=False,
                )

        detail_summaries = self.select_detail_summaries(context)
        detail_section = self.render_detail_section(detail_summaries, context)
        if detail_section:
            _append(
                detail_section,
                name="Data Schema Analysis", kind="schema_analysis",
                critical=False, foldable=True,
            )

        return PromptRenderResult(text="".join(text_parts), section_map=spans)

    # ------------------------------------------------------------------
    # Section renderers
    # ------------------------------------------------------------------

    def render_directory_section(self, context: AgentDataContext) -> str:
        return (
            "## Directory Structure (Current Working Directory)\n"
            f"```text\n{context.inventory.directory_structure_text}\n```\n\n"
        )

    def render_inventory_summary(self, context: AgentDataContext) -> str:
        counts = context.inventory.counts
        if not counts:
            return ""

        lines = [
            f"- Total analyzable artifacts: {counts.get('total', 0)}",
            f"- Tabular files: {counts.get('tabular', 0)}",
            f"- Document/schema files: {counts.get('document', 0)}",
            f"- Database files: {counts.get('database', 0)}",
        ]
        if context.inventory.warnings:
            lines.extend(f"- Warning: {warning}" for warning in context.inventory.warnings)
        if context.omitted_artifacts:
            preview = ", ".join(f"`{artifact}`" for artifact in context.omitted_artifacts[:3])
            suffix = " ..." if len(context.omitted_artifacts) > 3 else ""
            lines.append(
                "- Omitted detail sections due to report budget: "
                f"{len(context.omitted_artifacts)}"
                + (f" ({preview}{suffix})" if preview else "")
            )
        return "## Data Inventory Summary\n" + "\n".join(lines) + "\n\n"

    def render_detail_section(
        self,
        summaries: list[ArtifactSummary],
        context: AgentDataContext,
    ) -> str:
        if not summaries:
            return ""
        folded = set(context.render_policy.folded_detail_artifacts)
        blocks = [
            self.render_summary_block(summary, folded=summary.descriptor.relative_path in folded)
            for summary in summaries
        ]
        return "## Data Schema Analysis\n" + "\n\n".join(blocks) + "\n\n"

    def render_summary_block(self, summary: ArtifactSummary, *, folded: bool = False) -> str:
        parts = [f"### Analysis of `{summary.descriptor.relative_path}`"]
        if summary.detail_lines:
            parts.append(self._detail_block(summary.detail_lines))
        if not folded and summary.table_text:
            parts.append(f"```text\n{summary.table_text}\n```")
        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _pick_submission_format(self, context: AgentDataContext) -> str:
        mode = context.render_policy.submission_format_mode
        if mode == "compact":
            return context.submission_format_requirements_compact
        return context.submission_format_requirements_full

    def _pick_io_requirements(self, context: AgentDataContext) -> str:
        mode = context.render_policy.io_requirements_mode
        if mode == "compact":
            return context.io_requirements_compact
        return context.io_requirements_full

    @staticmethod
    def select_detail_summaries(context: AgentDataContext) -> list[ArtifactSummary]:
        if not context.detail_artifacts:
            return []
        selected = set(context.detail_artifacts)
        return [summary for summary in context.summaries if summary.descriptor.relative_path in selected]

    @staticmethod
    def _detail_block(lines: list[str]) -> str:
        cleaned = [line for line in lines if line]
        return "```text\n" + "\n".join(cleaned) + "\n```"
