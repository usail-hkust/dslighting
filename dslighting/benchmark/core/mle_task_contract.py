from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

import yaml

from dslighting.benchmark.core.source_catalog import BenchmarkSourceDescriptor
from dslighting.benchmark.vendor.mlebench.grade_helpers import Grader
from dslighting.benchmark.vendor.mlebench.utils import import_fn
from dslighting.error import ConfigurationError


@dataclass(frozen=True)
class MLEStyleCompetition:
    id: str
    name: str
    description: str
    grader: Grader
    answers: Path
    gold_submission: Path
    sample_submission: Path
    competition_type: str
    prepare_fn: Callable[[Path, Path, Path], Path]
    raw_dir: Path
    private_dir: Path
    public_dir: Path
    checksums: Path
    leaderboard: Path
    submission_filename: Optional[str] = None

    def __post_init__(self) -> None:
        assert isinstance(self.id, str), "Competition id must be a string."
        assert isinstance(self.name, str), "Competition name must be a string."
        assert isinstance(self.description, str), "Competition description must be a string."
        assert isinstance(self.grader, Grader), "Competition grader must be of type Grader."
        assert isinstance(self.answers, Path), "Competition answers must be a Path."
        assert isinstance(self.gold_submission, Path), "Gold submission must be a Path."
        assert isinstance(self.sample_submission, Path), "Sample submission must be a Path."
        assert isinstance(self.competition_type, str), "Competition type must be a string."
        assert isinstance(self.checksums, Path), "Checksums must be a Path."
        assert isinstance(self.leaderboard, Path), "Leaderboard must be a Path."

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "MLEStyleCompetition":
        grader = Grader.from_dict(data["grader"])
        return MLEStyleCompetition(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            grader=grader,
            answers=data["answers"],
            sample_submission=data["sample_submission"],
            gold_submission=data["gold_submission"],
            competition_type=data["competition_type"],
            prepare_fn=data["prepare_fn"],
            raw_dir=data["raw_dir"],
            public_dir=data["public_dir"],
            private_dir=data["private_dir"],
            checksums=data["checksums"],
            leaderboard=data["leaderboard"],
            submission_filename=data.get("submission_filename"),
        )


class MLETaskContractLoader:
    """Shared loader for all sources using the MLE-style task contract."""

    def __init__(self, descriptor: BenchmarkSourceDescriptor) -> None:
        self.descriptor = descriptor

    @property
    def benchmark_root(self) -> Path:
        return self.descriptor.vendor_root.parent.parent.resolve()

    def load_task_config(self, task_dir: Path) -> dict[str, Any]:
        config_path = task_dir / "config.yaml"
        with open(config_path, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    def validate_task_config(
        self,
        task_id: str,
        config: dict[str, Any],
        config_path: Path,
        *,
        require_runtime_fields: bool = True,
    ) -> None:
        required_fields = ["id"]
        if require_runtime_fields:
            required_fields.extend(["name", "grader", "dataset", "preparer"])

        missing = [field for field in required_fields if field not in config]
        if missing:
            raise ConfigurationError(
                f"Task '{task_id}' config missing required fields: {missing} ({config_path})."
            )

        config_id = str(config.get("id", "")).strip()
        if config_id != task_id:
            raise ConfigurationError(
                f"Task id mismatch: expected '{task_id}', found '{config_id}' in {config_path}."
            )

        if require_runtime_fields:
            dataset = config.get("dataset") or {}
            missing_dataset = [
                field
                for field in ("answers", "sample_submission")
                if field not in dataset
            ]
            if missing_dataset:
                raise ConfigurationError(
                    f"Task '{task_id}' config missing dataset fields: {missing_dataset} ({config_path})."
                )

    def resolve_description(self, task_dir: Path, config: dict[str, Any]) -> str:
        direct = task_dir / "description.md"
        if direct.exists():
            return direct.read_text(encoding="utf-8").strip()

        desc_value = str(config.get("description") or "").strip()
        candidates = []
        if desc_value:
            desc_path = Path(desc_value)
            if desc_path.is_absolute():
                candidates.append(desc_path)
            candidates.append(task_dir / desc_path)
            candidates.append(self.benchmark_root / desc_path)
            candidates.append(task_dir / desc_path.name)

        for candidate in candidates:
            if candidate.exists():
                return candidate.read_text(encoding="utf-8").strip()

        raise ConfigurationError(
            f"Task description not found for '{task_dir.name}' ({task_dir / 'config.yaml'})."
        )

    @staticmethod
    def _switch_prepare_symbol(value: str, mode: str) -> str:
        return value

    @staticmethod
    def _resolve_prepare_variant(path: Path, fn_name: str, mode: str) -> tuple[Path, str]:
        if mode not in {"prepare", "validation"} or fn_name != "prepare":
            return path, fn_name
        sibling = path.with_name(f"{path.stem}_val{path.suffix}")
        if sibling.exists():
            return sibling.resolve(), "prepare"
        return path, "prepare_val"

    def _resolve_file_reference(self, task_dir: Path, path_part: str) -> Path:
        candidate = Path(path_part)
        if candidate.is_absolute():
            return candidate

        options = [
            task_dir / candidate,
            self.benchmark_root / candidate,
            task_dir / candidate.name,
        ]
        for option in options:
            if option.exists():
                return option.resolve()
        return (task_dir / candidate).resolve()

    def resolve_callable_ref(self, task_dir: Path, ref: str, mode: str) -> str:
        normalized = self._switch_prepare_symbol(str(ref).strip(), mode)
        if normalized.startswith("file:"):
            path_part, fn_name = normalized[len("file:") :].rsplit(":", 1)
            resolved_path = self._resolve_file_reference(task_dir, path_part)
            resolved_path, fn_name = self._resolve_prepare_variant(resolved_path, fn_name, mode)
            return f"file:{resolved_path}:{fn_name}"

        if ":" not in normalized:
            raise ConfigurationError(f"Invalid callable reference: {normalized}")

        module_str, fn_name = normalized.rsplit(":", 1)
        if module_str.endswith(".py"):
            resolved_path = self._resolve_file_reference(task_dir, module_str)
            resolved_path, fn_name = self._resolve_prepare_variant(resolved_path, fn_name, mode)
            return f"file:{resolved_path}:{fn_name}"

        leaf = module_str.split(".")[-1]
        candidate = task_dir / f"{leaf}.py"
        if not candidate.exists() and leaf.endswith("_val"):
            fallback = task_dir / f"{leaf[:-4]}.py"
            if fallback.exists():
                candidate = fallback
        if candidate.exists():
            candidate, fn_name = self._resolve_prepare_variant(candidate.resolve(), fn_name, mode)
            return f"file:{candidate.resolve()}:{fn_name}"
        return normalized

    def resolve_preparer(self, task_dir: Path, config: dict[str, Any], mode: str) -> Callable:
        preparer_ref = self.resolve_callable_ref(task_dir, str(config["preparer"]), mode)
        return import_fn(preparer_ref)

    def resolve_grade_fn(self, task_dir: Path, config: dict[str, Any], mode: str) -> Optional[str]:
        grader_cfg = config.get("grader") or {}
        grade_ref = grader_cfg.get("grade_fn")
        if not grade_ref:
            return None
        return self.resolve_callable_ref(task_dir, str(grade_ref), mode)

    def resolve_dataset_paths(
        self,
        task_dir: Path,
        data_root: Path,
        config: dict[str, Any],
        mode: str,
    ) -> dict[str, Path]:
        dataset_cfg = dict(config.get("dataset") or {})
        answers_rel = str(dataset_cfg["answers"])
        sample_rel = str(dataset_cfg["sample_submission"])
        gold_rel = str(dataset_cfg.get("gold_submission") or answers_rel)
        public_folder = "public"
        private_folder = "private"

        base_answers_rel = answers_rel
        base_sample_rel = sample_rel
        base_gold_rel = gold_rel

        if mode == "validation":
            answers_rel = answers_rel.replace("/private/", "/private_val/")
            sample_rel = sample_rel.replace("/public/", "/public_val/")
            gold_rel = gold_rel.replace("/private/", "/private_val/")
            public_folder = "public_val"
            private_folder = "private_val"

        answers = data_root / answers_rel
        sample_submission = data_root / sample_rel
        gold_submission = data_root / gold_rel
        public_dir = data_root / task_dir.name / "prepared" / public_folder
        private_dir = data_root / task_dir.name / "prepared" / private_folder

        if mode == "validation":
            if not (
                answers.exists()
                and sample_submission.exists()
                and public_dir.exists()
                and private_dir.exists()
            ):
                answers = data_root / base_answers_rel
                sample_submission = data_root / base_sample_rel
                gold_submission = data_root / base_gold_rel
                public_dir = data_root / task_dir.name / "prepared" / "public"
                private_dir = data_root / task_dir.name / "prepared" / "private"

        return {
            "answers": answers,
            "gold_submission": gold_submission,
            "sample_submission": sample_submission,
            "raw_dir": data_root / task_dir.name / "raw",
            "public_dir": public_dir,
            "private_dir": private_dir,
        }

    def build_competition_payload(
        self,
        task_dir: Path,
        data_root: Path,
        config: dict[str, Any],
        mode: str,
    ) -> dict[str, Any]:
        config_path = task_dir / "config.yaml"
        self.validate_task_config(task_dir.name, config, config_path, require_runtime_fields=True)

        prepared_config = dict(config)
        prepared_grader = dict(prepared_config.get("grader") or {})
        grade_fn_ref = self.resolve_grade_fn(task_dir, prepared_config, mode)
        if grade_fn_ref:
            prepared_grader["grade_fn"] = grade_fn_ref
        prepared_config["grader"] = prepared_grader

        dataset_paths = self.resolve_dataset_paths(task_dir, data_root, prepared_config, mode)
        preparer_fn = self.resolve_preparer(task_dir, prepared_config, mode)

        return {
            **prepared_config,
            "description": self.resolve_description(task_dir, prepared_config),
            "answers": dataset_paths["answers"],
            "gold_submission": dataset_paths["gold_submission"],
            "sample_submission": dataset_paths["sample_submission"],
            "prepare_fn": preparer_fn,
            "raw_dir": dataset_paths["raw_dir"],
            "private_dir": dataset_paths["private_dir"],
            "public_dir": dataset_paths["public_dir"],
            "checksums": task_dir / "checksums.yaml",
            "leaderboard": task_dir / "leaderboard.csv",
            "submission_filename": (prepared_config.get("dataset") or {}).get("submission_filename"),
        }
