"""Prompt budget selection for agent-facing data perception reports."""

from __future__ import annotations

from dataclasses import replace

from .models import AgentDataContext, ArtifactSummary, PromptRenderPolicy
from .renderers.prompt import PromptReportRenderer, RenderProfile


class PromptBudgetManager:
    """Apply a character budget to AgentDataContext, writing render policy decisions.

    Two-phase algorithm:
        Phase 1: Measure fixed critical sections at full density; if they already exceed
                 the budget, degrade submission_format and io_requirements to compact,
                 then try compressing directory section (last resort).
        Phase 2: With remaining budget, greedily add optional detail blocks; remove
                 lowest-priority blocks if still over budget.
        Phase 3: Within detail blocks, fold (remove table_text) before omitting.

    Decision authority: this class is the SOLE writer of AgentDataContext.render_policy.
    The renderer never makes length decisions.
    """

    def __init__(self, *, max_report_chars: int | None, renderer: PromptReportRenderer) -> None:
        self.max_report_chars = int(max_report_chars) if max_report_chars is not None else None
        self._renderer = renderer

    def apply(
        self,
        context: AgentDataContext,
        profile: RenderProfile = "data_report",
    ) -> AgentDataContext:
        budget = self.max_report_chars
        if budget is None or budget <= 0 or not context.summaries:
            return replace(
                context,
                detail_artifacts=[s.descriptor.relative_path for s in context.summaries],
                omitted_artifacts=[],
            )

        # Start with all artifacts in detail, default (full) policy
        full_context = replace(
            context,
            detail_artifacts=[s.descriptor.relative_path for s in context.summaries],
            omitted_artifacts=[],
        )
        if len(self._renderer.render(full_context, profile)) <= budget:
            return full_context

        # Phase 1: try degrading critical section density to fit fixed sections
        ctx = self._apply_critical_section_compaction(full_context, budget, profile)

        # Phase 2: select detail blocks with remaining budget
        ctx = self._apply_detail_budget(ctx, budget, profile)

        return ctx

    # ------------------------------------------------------------------
    # Phase 1: compact fallback for critical sections
    # ------------------------------------------------------------------

    def _apply_critical_section_compaction(
        self,
        context: AgentDataContext,
        budget: int,
        profile: RenderProfile,
    ) -> AgentDataContext:
        """Degrade submission_format and io_requirements to compact if over budget."""
        policy = context.render_policy

        # Try submission_format compact
        if len(self._renderer.render(context, profile)) > budget:
            policy = replace(policy, submission_format_mode="compact")
            context = replace(context, render_policy=policy)

        # Try io_requirements compact
        if profile == "combined_report" and len(self._renderer.render(context, profile)) > budget:
            policy = replace(policy, io_requirements_mode="compact")
            context = replace(context, render_policy=policy)

        return context

    # ------------------------------------------------------------------
    # Phase 2 & 3: detail block budget
    # ------------------------------------------------------------------

    def _apply_detail_budget(
        self,
        context: AgentDataContext,
        budget: int,
        profile: RenderProfile,
    ) -> AgentDataContext:
        """Select which detail blocks fit; fold table_text before omitting."""
        if len(self._renderer.render(context, profile)) <= budget:
            return context

        selected_paths = self._select_detail_paths(context, budget, profile)
        selected_set = set(selected_paths)
        omitted = [
            s.descriptor.relative_path
            for s in context.summaries
            if s.descriptor.relative_path not in selected_set
        ]
        ctx = replace(context, detail_artifacts=selected_paths, omitted_artifacts=omitted)

        # If still over budget after greedy selection, remove lowest-priority blocks
        while omitted and len(self._renderer.render(ctx, profile)) > budget:
            removable = self._find_lowest_priority_selected(ctx)
            if removable is None:
                break
            selected_paths = [p for p in selected_paths if p != removable]
            omitted.insert(0, removable)
            ctx = replace(context, detail_artifacts=selected_paths, omitted_artifacts=omitted)

        # Phase 3: fold table_text on lowest-priority remaining blocks to recover space
        ctx = self._apply_folding(ctx, budget, profile)

        return ctx

    def _apply_folding(
        self,
        context: AgentDataContext,
        budget: int,
        profile: RenderProfile,
    ) -> AgentDataContext:
        """Fold table_text on low-priority detail artifacts to stay within budget."""
        if len(self._renderer.render(context, profile)) <= budget:
            return context

        foldable = [
            s for s in self._renderer.select_detail_summaries(context)
            if not self._is_mandatory(s) and s.table_text
        ]
        foldable.sort(
            key=lambda s: (self._priority(s), -len(s.table_text or "")),
            reverse=True,
        )

        folded: list[str] = list(context.render_policy.folded_detail_artifacts)
        policy = context.render_policy

        for summary in foldable:
            path = summary.descriptor.relative_path
            if path in folded:
                continue
            folded.append(path)
            policy = replace(policy, folded_detail_artifacts=list(folded))
            ctx = replace(context, render_policy=policy)
            if len(self._renderer.render(ctx, profile)) <= budget:
                return ctx
            context = ctx

        return context

    def _select_detail_paths(
        self,
        context: AgentDataContext,
        budget: int,
        profile: RenderProfile,
    ) -> list[str]:
        mandatory: list[ArtifactSummary] = []
        optional: list[ArtifactSummary] = []
        for summary in context.summaries:
            if self._is_mandatory(summary):
                mandatory.append(summary)
            else:
                optional.append(summary)

        selected: list[ArtifactSummary] = list(mandatory)
        if not selected and context.summaries:
            selected.append(context.summaries[0])

        sorted_optional = sorted(
            optional,
            key=lambda s: (
                self._priority(s),
                len(self._renderer.render_summary_block(s)),
                context.summaries.index(s),
            ),
        )

        for summary in sorted_optional:
            candidate_paths = [s.descriptor.relative_path for s in selected + [summary]]
            candidate_ctx = replace(
                context,
                detail_artifacts=candidate_paths,
                omitted_artifacts=self._compute_omitted_paths(context, candidate_paths),
            )
            if len(self._renderer.render(candidate_ctx, profile)) <= budget:
                selected.append(summary)

        selected_set = {s.descriptor.relative_path for s in selected}
        return [
            s.descriptor.relative_path
            for s in context.summaries
            if s.descriptor.relative_path in selected_set
        ]

    @staticmethod
    def _compute_omitted_paths(context: AgentDataContext, selected_paths: list[str]) -> list[str]:
        selected = set(selected_paths)
        return [
            s.descriptor.relative_path
            for s in context.summaries
            if s.descriptor.relative_path not in selected
        ]

    def _find_lowest_priority_selected(self, context: AgentDataContext) -> str | None:
        selected = self._renderer.select_detail_summaries(context)
        removable = [s for s in selected if not self._is_mandatory(s)]
        if not removable:
            return None
        removable.sort(
            key=lambda s: (
                self._priority(s),
                len(self._renderer.render_summary_block(s)),
                s.descriptor.relative_path,
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
