"""Prompt renderer for structured data perception."""

from __future__ import annotations

from ..models import AgentDataContext, ArtifactSummary


class PromptReportRenderer:
    """Render AgentDataContext into the existing COMPREHENSIVE DATA REPORT style."""

    def render(self, context: AgentDataContext) -> str:
        sections = ["\n\n--- COMPREHENSIVE DATA REPORT ---\n\n"]
        sections.append(self.render_directory_section(context))

        summary_section = self.render_inventory_summary(context)
        if summary_section:
            sections.append(summary_section)

        detail_summaries = self.select_detail_summaries(context)
        detail_section = self.render_detail_section(detail_summaries)
        if detail_section:
            sections.append(detail_section)

        return "".join(sections)

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

    def render_detail_section(self, summaries: list[ArtifactSummary]) -> str:
        if not summaries:
            return ""
        blocks = [self.render_summary_block(summary) for summary in summaries]
        return "## Data Schema Analysis\n" + "\n\n".join(blocks) + "\n\n"

    def render_summary_block(self, summary: ArtifactSummary) -> str:
        parts = [f"### Analysis of `{summary.descriptor.relative_path}`"]
        if summary.detail_lines:
            parts.append(self._detail_block(summary.detail_lines))
        if summary.table_text:
            parts.append(f"```text\n{summary.table_text}\n```")
        return "\n\n".join(parts)

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
