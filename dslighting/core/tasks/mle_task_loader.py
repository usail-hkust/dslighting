"""
Registry-first task loader for benchmark-style tasks.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import yaml

from dslighting.error import BenchmarkError, ConfigurationError

logger = logging.getLogger(__name__)


class MLETaskLoader:
    """
    Load benchmark task metadata and data paths from registry definitions.

    Contract:
    - `task_id` must resolve to `<registry_root>/<task_id>/config.yaml`.
    - `config.yaml` must contain required grading fields.
    """

    def __init__(self) -> None:
        self.last_task_type: str = "kaggle"
        self.last_registry_root: Optional[Path] = None
        self.last_registry_task_dir: Optional[Path] = None

    @staticmethod
    def _candidate_registry_roots() -> list[Path]:
        package_root = Path(__file__).resolve().parents[2]
        return [
            package_root / "benchmark" / "vendor" / "mlebench" / "competitions",
            package_root / "benchmark" / "vendor" / "dabench" / "competitions",
            package_root / "benchmark" / "vendor" / "sciencebench" / "competitions",
            Path.cwd() / "dslighting" / "benchmark" / "vendor" / "mlebench" / "competitions",
            Path.cwd() / "dslighting" / "benchmark" / "vendor" / "dabench" / "competitions",
            Path.cwd() / "dslighting" / "benchmark" / "vendor" / "sciencebench" / "competitions",
            Path.cwd() / "benchmark" / "vendor" / "mlebench" / "competitions",
            Path.cwd() / "benchmark" / "vendor" / "dabench" / "competitions",
            Path.cwd() / "benchmark" / "vendor" / "sciencebench" / "competitions",
        ]

    @staticmethod
    def _normalize_registry_inputs(
        task_id: str,
        registry_dir: Optional[Union[str, Path]],
    ) -> Tuple[Path, Path]:
        if registry_dir is not None:
            user_path = Path(registry_dir).expanduser().resolve()
            if (user_path / "config.yaml").exists() and user_path.name == task_id:
                return user_path.parent, user_path
            if (user_path / task_id / "config.yaml").exists():
                return user_path, user_path / task_id
            raise BenchmarkError(
                f"Registry contract not found for task '{task_id}' under '{user_path}'. "
                "Expected '<registry_root>/<task_id>/config.yaml'."
            )

        for root in MLETaskLoader._candidate_registry_roots():
            task_dir = root / task_id
            if (task_dir / "config.yaml").exists():
                return root, task_dir

        raise BenchmarkError(
            f"Registry contract not found for task '{task_id}'. "
            "Pass `registry_dir=` explicitly for custom tasks."
        )

    @staticmethod
    def _validate_registry_contract(task_id: str, task_registry_dir: Path) -> Dict:
        config_path = task_registry_dir / "config.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

        required_top_level = ("id", "grader", "dataset")
        missing_top_level = [key for key in required_top_level if key not in config]
        if missing_top_level:
            raise ConfigurationError(
                f"Task '{task_id}' config missing required fields: {missing_top_level} ({config_path})."
            )

        dataset = config.get("dataset") or {}
        required_dataset = ("answers", "sample_submission")
        missing_dataset = [key for key in required_dataset if key not in dataset]
        if missing_dataset:
            raise ConfigurationError(
                f"Task '{task_id}' config missing dataset fields: {missing_dataset} ({config_path})."
            )

        config_id = str(config.get("id", "")).strip()
        if config_id != task_id:
            raise ConfigurationError(
                f"Task id mismatch: expected '{task_id}', found '{config_id}' in {config_path}."
            )
        return config

    @staticmethod
    def _infer_data_root(task_id: str, data_dir: Optional[Path]) -> Path:
        if data_dir is None:
            default_root = Path.cwd() / "data" / "competitions"
            if default_root.exists():
                return default_root
            raise ValueError(
                f"Cannot infer data root for task '{task_id}'. "
                "Pass `data_dir=` (e.g. '<root>/<task_id>/prepared/public')."
            )

        p = Path(data_dir).expanduser().resolve()
        if p.name in ("public", "public_val") and p.parent.name in ("prepared", "prepared_val"):
            return p.parent.parent.parent
        if p.name == task_id and (p / "prepared").exists():
            return p.parent
        if (p / task_id / "prepared").exists():
            return p
        return p

    @staticmethod
    def _build_registry(task_id: str, registry_root: Path, data_root: Path):
        registry_root_lower = str(registry_root).lower()
        if task_id.startswith("dabench-") or "/dabench/" in registry_root_lower:
            from dslighting.benchmark.vendor.dabench.registry import Registry as DABenchRegistry

            return DABenchRegistry().set_data_dir(data_root)
        if "/sciencebench/" in registry_root_lower:
            from dslighting.benchmark.vendor.sciencebench.registry import Registry as ScienceBenchRegistry

            return ScienceBenchRegistry().set_data_dir(data_root)

        from dslighting.benchmark.vendor.mlebench.registry import Registry as MLERegistry

        return MLERegistry().set_data_dir(data_root)

    def load_task(
        self,
        task_id: str,
        data_dir: Optional[Path] = None,
        registry_dir: Optional[Union[str, Path]] = None,
    ) -> Tuple[str, str, Path, Path]:
        logger.info("Load benchmark task: %s", task_id)

        registry_root, task_registry_dir = self._normalize_registry_inputs(task_id, registry_dir)
        config = self._validate_registry_contract(task_id, task_registry_dir)
        self.last_registry_root = registry_root
        self.last_registry_task_dir = task_registry_dir
        self.last_task_type = str(config.get("task_type") or "kaggle").strip() or "kaggle"

        data_root = self._infer_data_root(task_id, data_dir=data_dir)
        registry = self._build_registry(task_id=task_id, registry_root=registry_root, data_root=data_root)
        competition = registry.get_competition(task_id)

        if data_dir is None:
            data_dir = competition.public_dir
        else:
            data_dir = Path(data_dir).expanduser().resolve()

        description = competition.description
        preferred_submission_name = getattr(competition, "submission_filename", None)
        sample_submission_path = getattr(competition, "sample_submission", None)
        suffix = (
            Path(preferred_submission_name).suffix
            if preferred_submission_name
            else (sample_submission_path.suffix if isinstance(sample_submission_path, Path) else ".csv")
        )
        if suffix and not suffix.startswith("."):
            suffix = f".{suffix}"
        output_filename = f"submission_{task_id}_{uuid.uuid4().hex[:6]}{suffix or '.csv'}"
        output_path = Path(output_filename)

        from dslighting.services.data_analyzer import DataAnalyzer

        analyzer = DataAnalyzer()
        submission_context = {
            "sample_submission_path": str(sample_submission_path) if isinstance(sample_submission_path, Path) else "",
            "submission_filename": preferred_submission_name or (sample_submission_path.name if isinstance(sample_submission_path, Path) else ""),
            "submission_format": suffix.lower() if suffix else "",
            "output_submission_path": str(output_path),
        }
        data_report = analyzer.analyze_data(
            data_dir,
            task_type=self.last_task_type,
            task_id=task_id,
            submission_context=submission_context,
        )
        io_instructions = analyzer.generate_io_instructions(output_path.name, optimization_context=False)
        full_description = f"{description}\n\n{data_report}"
        return full_description, io_instructions, data_dir, output_path

    def load_benchmark(
        self,
        task_id: str,
        data_dir: Optional[Path] = None,
        registry_dir: Optional[Union[str, Path]] = None,
    ):
        if data_dir is None:
            raise ValueError("`data_dir` is required to create a benchmark instance.")

        registry_root, _ = self._normalize_registry_inputs(task_id, registry_dir)
        data_root = self._infer_data_root(task_id, data_dir=data_dir)
        registry_root_lower = str(registry_root).lower()

        if task_id.startswith("dabench-") or "/dabench/" in registry_root_lower:
            from dslighting.benchmark.benchmarks.da_benchmark import DABenchmark

            return DABenchmark(
                name=f"direct_{task_id}",
                log_path="runs/benchmarks/direct",
                data_dir=str(data_root),
                competitions=[task_id],
                data_source="prepared",
            )

        from dslighting.benchmark.benchmarks.mle_benchmark import MLEBenchmark

        return MLEBenchmark(
            name=f"direct_{task_id}",
            file_path=None,
            log_path="runs/benchmarks/direct",
            data_dir=str(data_root),
            competitions=[task_id],
            data_source="prepared",
        )
