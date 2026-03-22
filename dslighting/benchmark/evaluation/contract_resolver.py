from __future__ import annotations

from pathlib import Path

from dslighting.benchmark.core.source_catalog import get_benchmark_source_catalog
from dslighting.benchmark.evaluation.contract_builder import build_task_evaluation_contract
from dslighting.benchmark.evaluation.models import TaskEvaluationContract, TaskEvaluationContractRef
from dslighting.benchmark.grading.models import SubmissionArtifactContract


class EvaluationContractResolver:
    def __init__(self) -> None:
        self._catalog = get_benchmark_source_catalog()

    def hydrate(
        self,
        ref: TaskEvaluationContractRef,
        *,
        submission_artifact: SubmissionArtifactContract | None = None,
    ) -> TaskEvaluationContract:
        registry_root = ref.registry_root
        descriptor = (
            self._catalog.resolve_source_by_registry_root(registry_root)
            if registry_root is not None
            else self._catalog.get_source(ref.source_id)
        )
        if ref.data_root is None:
            raise ValueError(f"Cannot hydrate evaluation contract for '{ref.task_id}' without data_root.")
        registry = self._catalog.build_registry(descriptor, data_root=Path(ref.data_root), mode=ref.mode)
        competition = registry.get_competition(ref.task_id)
        contract, _ = build_task_evaluation_contract(
            competition=competition,
            source_id=descriptor.source_id,
            engine_id=ref.engine_id or descriptor.engine_id,
            registry_root=descriptor.registry_root,
            data_root=Path(ref.data_root),
            mode=ref.mode,
            output_submission_path=submission_artifact.output_submission_path if submission_artifact else None,
            evaluation_mode=ref.evaluation_mode,
        )
        if submission_artifact is not None and contract.grading is not None:
            from dataclasses import replace

            contract = replace(
                contract,
                grading=replace(contract.grading, submission=submission_artifact),
            )
        return contract
