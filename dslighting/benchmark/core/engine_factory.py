from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from dslighting.benchmark.core.source_catalog import BenchmarkSourceCatalog, BenchmarkSourceDescriptor
from dslighting.error import BenchmarkError


class BenchmarkEngineFactory:
    """Construct benchmark instances from source descriptors."""

    def __init__(self, catalog: BenchmarkSourceCatalog) -> None:
        self.catalog = catalog

    def build_single_task_benchmark(
        self,
        source: BenchmarkSourceDescriptor,
        task_id: str,
        data_root: Path,
        *,
        name: Optional[str] = None,
        log_path: Optional[str] = None,
        runner: Optional[Any] = None,
        eval_fn: Optional[Any] = None,
    ):
        return self.build_benchmark(
            source,
            name=name or f"direct_{task_id}",
            data_dir=str(data_root),
            competitions=[task_id],
            log_path=log_path or "runs/benchmarks/direct",
            runner=runner,
            eval_fn=eval_fn,
        )

    def build_benchmark(
        self,
        source: BenchmarkSourceDescriptor,
        *,
        name: str,
        data_dir: str,
        competitions: list[str],
        log_path: Optional[str] = None,
        runner: Optional[Any] = None,
        eval_fn: Optional[Any] = None,
    ):
        resolved_log_path = log_path or f"runs/benchmarks/{name}"
        if source.engine_id == "mle":
            from dslighting.benchmark.benchmarks.mle_style_benchmark import MLEStyleBenchmark

            registry = self.catalog.build_registry(source, data_root=Path(data_dir))
            return MLEStyleBenchmark(
                name=name,
                file_path=None,
                log_path=resolved_log_path,
                data_dir=str(data_dir),
                competitions=competitions,
                data_source="prepared",
                runner=runner,
                eval_fn=eval_fn,
                registry=registry,
            )

        raise BenchmarkError(f"Unsupported benchmark engine: {source.engine_id}")
