"""High-level orchestration for agent-facing data perception."""

from __future__ import annotations

from collections import Counter

from .budget import PromptBudgetManager
from .cache import DataPerceptionCache
from .discovery import discover_artifacts, generate_file_tree
from .models import AgentDataContext, ArtifactDescriptor, ArtifactSummary, DataInventory
from .renderers.prompt import PromptReportRenderer
from .request import DataPerceptionRequest
from .samplers import DatabaseSampler, DocumentSampler, TabularSampler


class DataPerceptionService:
    """Inspect agent-visible files and build a structured AgentDataContext."""

    def __init__(
        self,
        request: DataPerceptionRequest,
        *,
        cache: DataPerceptionCache | None = None,
    ) -> None:
        self.request = request
        self._cache = cache
        self._renderer = PromptReportRenderer()
        self._budget = PromptBudgetManager(
            max_report_chars=request.max_report_chars,
            renderer=self._renderer,
        )
        self._tabular = TabularSampler(tolerant_fallback=request.tabular_tolerant_fallback)
        self._document = DocumentSampler(preview_lines=request.document_preview_lines)
        self._database = DatabaseSampler()

    def build_base_context(self) -> AgentDataContext:
        """Return an un-enriched, un-budgeted AgentDataContext.

        The context contains only what the service discovers: inventory and artifact
        summaries. Critical sections (submission requirements, I/O requirements) and
        render policy are set by DataPerceptionRuntime after this call returns.
        """
        inventory = self._load_inventory()
        summaries = [self._load_or_summarize_artifact(descriptor) for descriptor in inventory.artifacts]
        inventory = DataInventory(
            artifacts=inventory.artifacts,
            directory_structure_text=inventory.directory_structure_text,
            counts=inventory.counts,
            warnings=self._collect_warnings(summaries),
        )
        if self._cache is not None:
            self._cache.put_inventory(self.request, inventory)
        return AgentDataContext(
            request=self.request,
            inventory=inventory,
            summaries=summaries,
            detail_artifacts=[summary.descriptor.relative_path for summary in summaries],
        )

    def inspect(self) -> AgentDataContext:
        """Return a budgeted AgentDataContext (no critical section enrichment).

        Kept for internal use and tests that only need the base + budget step.
        For the full pipeline, prefer DataPerceptionRuntime.analyze_data().
        """
        context = self.build_base_context()
        return self._budget.apply(context)

    def render_prompt(self, context: AgentDataContext) -> str:
        return self._renderer.render(context)

    def build_report(self) -> str:
        """Convenience helper for tests and one-off calls.

        For the main execution path, use DataPerceptionRuntime.analyze_data() instead,
        which properly enriches critical sections and applies the two-phase budget.
        """
        context = self.inspect()
        return self.render_prompt(context)

    def _summarize_artifact(self, descriptor: ArtifactDescriptor) -> ArtifactSummary:
        if descriptor.kind == "tabular":
            return self._tabular.summarize(descriptor)
        if descriptor.kind == "document":
            return self._document.summarize(descriptor)
        if descriptor.kind == "database":
            return self._database.summarize(descriptor)
        return ArtifactSummary(
            descriptor=descriptor,
            status="error",
            detail_lines=["Kind: unsupported"],
        )

    def _load_inventory(self) -> DataInventory:
        if self._cache is not None:
            cached = self._cache.get_inventory(self.request)
            if cached is not None:
                return cached

        artifacts = discover_artifacts(self.request)
        counts = Counter(descriptor.kind for descriptor in artifacts)
        inventory = DataInventory(
            artifacts=artifacts,
            directory_structure_text=generate_file_tree(self.request.data_dir, display_root_name="."),
            counts={
                "total": len(artifacts),
                "tabular": counts.get("tabular", 0),
                "document": counts.get("document", 0),
                "database": counts.get("database", 0),
            },
        )
        if self._cache is not None:
            self._cache.put_inventory(self.request, inventory)
        return inventory

    def _load_or_summarize_artifact(self, descriptor: ArtifactDescriptor) -> ArtifactSummary:
        if self._cache is not None:
            cached = self._cache.get_summary(self.request, descriptor)
            if cached is not None:
                return cached
        summary = self._summarize_artifact(descriptor)
        if self._cache is not None:
            self._cache.put_summary(self.request, summary)
        return summary

    @staticmethod
    def _collect_warnings(summaries: list[ArtifactSummary]) -> list[str]:
        warnings: list[str] = []
        for summary in summaries:
            if summary.status == "degraded":
                warnings.append(f"{summary.descriptor.relative_path} required fallback analysis")
            elif summary.status == "error":
                warnings.append(f"{summary.descriptor.relative_path} could not be fully analyzed")
        return warnings
