"""Prompt budget selection for agent-facing data perception reports."""

from __future__ import annotations

from dataclasses import replace

from .models import AgentDataContext, ArtifactSummary
from .renderers.prompt import PromptReportRenderer


class PromptBudgetManager:
    """Select which artifact detail blocks enter the rendered data report."""

    def __init__(self, *, max_report_chars: int | None, renderer: PromptReportRenderer) -> None:
        self.max_report_chars = int(max_report_chars) if max_report_chars is not None else None
        self._renderer = renderer

    def apply(self, context: AgentDataContext) -> AgentDataContext:
        budget = self.max_report_chars
        if budget is None or budget <= 0 or not context.summaries:
            return replace(
                context,
                detail_artifacts=[summary.descriptor.relative_path for summary in context.summaries],
                omitted_artifacts=[],
            )

        full_context = replace(
            context,
            detail_artifacts=[summary.descriptor.relative_path for summary in context.summaries],
            omitted_artifacts=[],
        )
        if len(self._renderer.render(full_context)) <= budget:
            return full_context

        selected_paths = self._select_detail_paths(context, budget)
        selected_set = set(selected_paths)
        omitted = [
            summary.descriptor.relative_path
            for summary in context.summaries
            if summary.descriptor.relative_path not in selected_set
        ]
        budgeted_context = replace(
            context,
            detail_artifacts=selected_paths,
            omitted_artifacts=omitted,
        )

        while omitted and len(self._renderer.render(budgeted_context)) > budget:
            removable = self._find_lowest_priority_selected(budgeted_context)
            if removable is None:
                break
            selected_paths = [path for path in selected_paths if path != removable]
            omitted.insert(0, removable)
            budgeted_context = replace(
                context,
                detail_artifacts=selected_paths,
                omitted_artifacts=omitted,
            )

        return budgeted_context

    def _select_detail_paths(self, context: AgentDataContext, budget: int) -> list[str]:
        mandatory: list[ArtifactSummary] = []
        optional: list[ArtifactSummary] = []
        for summary in context.summaries:
            if self._is_mandatory(summary):
                mandatory.append(summary)
            else:
                optional.append(summary)

        selected: list[ArtifactSummary] = []
        for summary in mandatory:
            selected.append(summary)

        if not selected and context.summaries:
            selected.append(context.summaries[0])

        sorted_optional = sorted(
            optional,
            key=lambda summary: (
                self._priority(summary),
                len(self._renderer.render_summary_block(summary)),
                context.summaries.index(summary),
            ),
        )

        for summary in sorted_optional:
            candidate_paths = [item.descriptor.relative_path for item in selected + [summary]]
            candidate_context = replace(
                context,
                detail_artifacts=candidate_paths,
                omitted_artifacts=self._compute_omitted_paths(context, candidate_paths),
            )
            if len(self._renderer.render(candidate_context)) <= budget:
                selected.append(summary)

        selected_paths = {summary.descriptor.relative_path for summary in selected}
        return [
            summary.descriptor.relative_path
            for summary in context.summaries
            if summary.descriptor.relative_path in selected_paths
        ]

    @staticmethod
    def _compute_omitted_paths(context: AgentDataContext, selected_paths: list[str]) -> list[str]:
        selected = set(selected_paths)
        return [
            summary.descriptor.relative_path
            for summary in context.summaries
            if summary.descriptor.relative_path not in selected
        ]

    def _find_lowest_priority_selected(self, context: AgentDataContext) -> str | None:
        selected = self._renderer.select_detail_summaries(context)
        removable = [summary for summary in selected if not self._is_mandatory(summary)]
        if not removable:
            return None
        removable.sort(
            key=lambda summary: (
                self._priority(summary),
                len(self._renderer.render_summary_block(summary)),
                summary.descriptor.relative_path,
            ),
            reverse=True,
        )
        return removable[0].descriptor.relative_path

    def _is_mandatory(self, summary: ArtifactSummary) -> bool:
        role = summary.descriptor.role
        return (
            role in {"output_template", "database_template", "schema_doc"}
            or summary.status != "ok"
        )

    @staticmethod
    def _priority(summary: ArtifactSummary) -> int:
        role = summary.descriptor.role
        if role in {"output_template", "database_template"}:
            return 0
        if role == "schema_doc":
            return 1
        if summary.status != "ok":
            return 2
        if role == "input_table":
            return 3
        if role == "auxiliary_doc":
            return 4
        return 5
