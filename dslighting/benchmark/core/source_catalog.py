from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path
from typing import Callable, Iterable, Optional, Sequence

import yaml

from dslighting.error import BenchmarkError, ConfigurationError


@dataclass(frozen=True)
class BenchmarkSourceDescriptor:
    source_id: str
    contract_id: str
    engine_id: str
    vendor_root: Path
    registry_root: Path
    manifest_path: Optional[Path] = None
    default_data_env_var: Optional[str] = None
    supports_single_task_loader: bool = True
    legacy_task_prefixes: tuple[str, ...] = ()


@dataclass(frozen=True)
class BenchmarkPresetDescriptor:
    preset_id: str
    source_id: str
    description: str
    task_ids: Optional[list[str]] = None
    task_provider: Optional[Callable[[], list[str]]] = None

    def get_task_ids(self) -> list[str]:
        if self.task_ids is not None:
            return list(self.task_ids)
        if self.task_provider is None:
            return []
        return list(self.task_provider())


@dataclass(frozen=True)
class ResolvedBenchmarkSource:
    descriptor: BenchmarkSourceDescriptor
    registry_root: Path
    task_dir: Optional[Path]
    manifest_path: Optional[Path]


class BenchmarkSourceCatalog:
    """Single source of truth for benchmark source discovery and routing."""

    def __init__(
        self,
        descriptors: Optional[Sequence[BenchmarkSourceDescriptor]] = None,
        presets: Optional[Sequence[BenchmarkPresetDescriptor]] = None,
    ) -> None:
        loaded_descriptors = list(descriptors) if descriptors is not None else self.load_builtin_sources()
        loaded_presets = list(presets) if presets is not None else self.load_builtin_presets()
        self._sources_by_id = {descriptor.source_id: descriptor for descriptor in loaded_descriptors}
        self._presets_by_id = {preset.preset_id: preset for preset in loaded_presets}

    @staticmethod
    def _benchmark_root() -> Path:
        return Path(__file__).resolve().parents[1]

    @classmethod
    def _builtin_vendor_root(cls) -> Path:
        return cls._benchmark_root() / "vendor"

    @classmethod
    def _load_descriptor_from_manifest(cls, manifest_path: Path) -> BenchmarkSourceDescriptor:
        payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        vendor_root = manifest_path.parent.resolve()
        registry_rel = str(payload.get("registry_root") or "competitions").strip() or "competitions"
        registry_root = (vendor_root / registry_rel).resolve()
        source_id = str(payload.get("source_id", "")).strip()
        contract_id = str(payload.get("contract_id", "")).strip()
        engine_id = str(payload.get("engine_id", "")).strip()
        if not source_id or not contract_id or not engine_id:
            raise ConfigurationError(
                f"Invalid benchmark manifest: {manifest_path}",
                details={"manifest_path": str(manifest_path)},
            )
        prefixes = tuple(
            str(prefix).strip()
            for prefix in payload.get("legacy_task_prefixes") or ()
            if str(prefix).strip()
        )
        return BenchmarkSourceDescriptor(
            source_id=source_id,
            contract_id=contract_id,
            engine_id=engine_id,
            vendor_root=vendor_root,
            registry_root=registry_root,
            manifest_path=manifest_path.resolve(),
            default_data_env_var=(payload.get("default_data_env_var") or None),
            supports_single_task_loader=bool(payload.get("supports_single_task_loader", True)),
            legacy_task_prefixes=prefixes,
        )

    @classmethod
    def load_builtin_sources(cls) -> list[BenchmarkSourceDescriptor]:
        vendor_root = cls._builtin_vendor_root()
        if not vendor_root.exists():
            return []

        descriptors: list[BenchmarkSourceDescriptor] = []
        for child in sorted(vendor_root.iterdir()):
            manifest_path = child / "benchmark.yaml"
            if manifest_path.exists():
                descriptors.append(cls._load_descriptor_from_manifest(manifest_path))
        return descriptors

    @staticmethod
    def load_builtin_presets() -> list[BenchmarkPresetDescriptor]:
        from dslighting.api.task_loader import TaskLoader

        presets = [
            BenchmarkPresetDescriptor(
                preset_id="mle-lite",
                source_id="mlebench",
                description="Curated MLEBench lite preset.",
                task_ids=list(TaskLoader.MLE_LITE_TASKS),
            )
        ]
        for preset_id in TaskLoader.DABENCH_SUBSETS:
            presets.append(
                BenchmarkPresetDescriptor(
                    preset_id=preset_id,
                    source_id="dabench",
                    description=f"DABench preset: {preset_id}",
                    task_provider=lambda preset_id=preset_id: list(
                        TaskLoader.get_dabench_subset_tasks(preset_id) or []
                    ),
                )
            )
        return presets

    def get_source(self, source_id: str) -> BenchmarkSourceDescriptor:
        try:
            return self._sources_by_id[source_id]
        except KeyError as exc:
            raise BenchmarkError(f"Unknown benchmark source: {source_id}") from exc

    def resolve_preset(self, benchmark_type: str) -> Optional[BenchmarkPresetDescriptor]:
        return self._presets_by_id.get(benchmark_type)

    def list_available_benchmark_types(self) -> list[str]:
        return sorted(set(self._sources_by_id) | set(self._presets_by_id))

    def _load_manifest_descriptor(self, manifest_path: Path) -> BenchmarkSourceDescriptor:
        descriptor = self._load_descriptor_from_manifest(manifest_path.resolve())
        existing = self._sources_by_id.get(descriptor.source_id)
        return existing or descriptor

    @staticmethod
    def _iter_search_bases(search_hints: Optional[Iterable[Path]]) -> list[Path]:
        bases: list[Path] = []
        seen: set[Path] = set()
        for hint in search_hints or ():
            if hint is None:
                continue
            try:
                resolved = Path(hint).expanduser().resolve()
            except OSError:
                continue
            for base in [resolved] + list(resolved.parents)[:6]:
                if base not in seen:
                    seen.add(base)
                    bases.append(base)
        cwd = Path.cwd().resolve()
        if cwd not in seen:
            bases.append(cwd)
        return bases

    @classmethod
    def _iter_manifest_paths_from_bases(cls, bases: Iterable[Path]) -> list[Path]:
        manifests: list[Path] = []
        seen: set[Path] = set()
        for base in bases:
            vendor_candidates = [
                base / "benchmark" / "vendor",
                base / "dslighting" / "benchmark" / "vendor",
            ]
            for vendor_root in vendor_candidates:
                if not vendor_root.exists():
                    continue
                for child in sorted(vendor_root.iterdir()):
                    manifest_path = (child / "benchmark.yaml").resolve()
                    if manifest_path.exists() and manifest_path not in seen:
                        seen.add(manifest_path)
                        manifests.append(manifest_path)
        return manifests

    @classmethod
    def _iter_legacy_registry_roots_from_bases(cls, bases: Iterable[Path]) -> list[Path]:
        registry_roots: list[Path] = []
        seen: set[Path] = set()
        for base in bases:
            vendor_candidates = [
                base / "benchmark" / "vendor",
                base / "dslighting" / "benchmark" / "vendor",
            ]
            for vendor_root in vendor_candidates:
                if not vendor_root.exists():
                    continue
                for child in sorted(vendor_root.iterdir()):
                    registry_root = (child / "competitions").resolve()
                    if not registry_root.exists() or registry_root in seen:
                        continue
                    if any(registry_root.glob("*/config.yaml")):
                        seen.add(registry_root)
                        registry_roots.append(registry_root)
        return registry_roots

    def _iter_descriptors(
        self,
        search_hints: Optional[Iterable[Path]] = None,
    ) -> list[BenchmarkSourceDescriptor]:
        descriptors: list[BenchmarkSourceDescriptor] = []
        known_roots: set[Path] = set()
        search_bases = self._iter_search_bases(search_hints)
        extra_manifests = self._iter_manifest_paths_from_bases(search_bases)
        for manifest_path in extra_manifests:
            descriptor = self._load_manifest_descriptor(manifest_path)
            if descriptor.registry_root.resolve() not in known_roots:
                descriptors.append(descriptor)
                known_roots.add(descriptor.registry_root.resolve())
        extra_legacy_roots = self._iter_legacy_registry_roots_from_bases(search_bases)
        for registry_root in extra_legacy_roots:
            if registry_root.resolve() not in known_roots:
                descriptor = self._legacy_external_descriptor(registry_root)
                descriptors.append(descriptor)
                known_roots.add(descriptor.registry_root.resolve())
        for descriptor in self._sources_by_id.values():
            if descriptor.registry_root.resolve() not in known_roots:
                descriptors.append(descriptor)
                known_roots.add(descriptor.registry_root.resolve())
        return descriptors

    def iter_registry_roots(
        self,
        search_hints: Optional[Iterable[Path]] = None,
    ) -> list[Path]:
        return [descriptor.registry_root for descriptor in self._iter_descriptors(search_hints)]

    @staticmethod
    def _legacy_external_descriptor(registry_root: Path) -> BenchmarkSourceDescriptor:
        vendor_root = registry_root.parent.resolve()
        source_name = vendor_root.name.strip() or "external"
        source_id = f"external-{source_name}"
        env_name = f"DSLIGHTING_{source_name.upper()}_DATA"
        return BenchmarkSourceDescriptor(
            source_id=source_id,
            contract_id="mle_task_contract/v1",
            engine_id="mle",
            vendor_root=vendor_root,
            registry_root=registry_root.resolve(),
            manifest_path=None,
            default_data_env_var=env_name,
            supports_single_task_loader=True,
        )

    def resolve_source_by_registry_root(
        self,
        registry_root: Path,
        search_hints: Optional[Iterable[Path]] = None,
    ) -> BenchmarkSourceDescriptor:
        resolved_root = Path(registry_root).expanduser().resolve()
        if (resolved_root / "config.yaml").exists():
            resolved_root = resolved_root.parent

        for descriptor in self._iter_descriptors(search_hints):
            if descriptor.registry_root.resolve() == resolved_root:
                return descriptor

        manifest_candidates = [
            resolved_root / "benchmark.yaml",
            resolved_root.parent / "benchmark.yaml",
        ]
        for manifest_path in manifest_candidates:
            if manifest_path.exists():
                return self._load_manifest_descriptor(manifest_path)

        return self._legacy_external_descriptor(resolved_root)

    def resolve_task(
        self,
        task_id: str,
        registry_dir: str | Path | None = None,
        search_hints: Optional[Iterable[Path]] = None,
    ) -> ResolvedBenchmarkSource:
        if registry_dir is not None:
            user_path = Path(registry_dir).expanduser().resolve()
            if (user_path / "config.yaml").exists() and user_path.name == task_id:
                task_dir = user_path
                registry_root = user_path.parent
            elif (user_path / task_id / "config.yaml").exists():
                task_dir = user_path / task_id
                registry_root = user_path
            else:
                raise BenchmarkError(
                    f"Registry contract not found for task '{task_id}' under '{user_path}'. "
                    "Expected '<registry_root>/<task_id>/config.yaml'."
                )
            descriptor = self.resolve_source_by_registry_root(registry_root, search_hints=search_hints)
            return ResolvedBenchmarkSource(
                descriptor=descriptor,
                registry_root=registry_root,
                task_dir=task_dir,
                manifest_path=descriptor.manifest_path,
            )

        for descriptor in self._iter_descriptors(search_hints):
            task_dir = descriptor.registry_root / task_id
            if (task_dir / "config.yaml").exists():
                return ResolvedBenchmarkSource(
                    descriptor=descriptor,
                    registry_root=descriptor.registry_root,
                    task_dir=task_dir,
                    manifest_path=descriptor.manifest_path,
                )

        raise BenchmarkError(
            f"Registry contract not found for task '{task_id}'. "
            "Pass `registry_dir=` explicitly for custom tasks."
        )

    def resolve_data_dir(self, source: BenchmarkSourceDescriptor, explicit_data_dir: Optional[str]) -> str:
        if explicit_data_dir:
            return explicit_data_dir
        env_key = source.default_data_env_var
        if env_key:
            env_value = os.getenv(env_key)
            if env_value:
                return env_value
        raise ValueError(
            f"Cannot determine data path for {source.source_id}. "
            f"Set {env_key} or provide data_dir explicitly."
            if env_key
            else f"Cannot determine data path for {source.source_id}. Provide data_dir explicitly."
        )

    def discover_tasks(
        self,
        source: BenchmarkSourceDescriptor,
        data_dir: str,
        require_prepared: bool = True,
    ) -> list[str]:
        from dslighting.api.task_loader import TaskLoader

        return TaskLoader.auto_discover_all_tasks(
            data_dir=data_dir,
            vendor_comp_dir=str(source.registry_root),
            prefix=None,
            require_prepared=require_prepared,
        )

    def build_registry(
        self,
        source: str | BenchmarkSourceDescriptor,
        data_root: Path,
        mode: str = "test",
    ):
        descriptor = self.get_source(source) if isinstance(source, str) else source
        if descriptor.contract_id == "mle_task_contract/v1":
            from dslighting.benchmark.core.mle_style_registry import MLEStyleRegistry

            registry = MLEStyleRegistry(descriptor=descriptor, data_dir=Path(data_root), mode=mode)
            registry.set_mode(mode)
            return registry
        raise BenchmarkError(f"Unsupported benchmark source contract: {descriptor.contract_id}")

    def build_benchmark(
        self,
        source: str | BenchmarkSourceDescriptor,
        **kwargs,
    ):
        descriptor = self.get_source(source) if isinstance(source, str) else source
        from dslighting.benchmark.core.engine_factory import BenchmarkEngineFactory

        return BenchmarkEngineFactory(self).build_benchmark(descriptor, **kwargs)

    def build_single_task_benchmark(
        self,
        source: str | BenchmarkSourceDescriptor,
        task_id: str,
        data_root: Path,
        **kwargs,
    ):
        descriptor = self.get_source(source) if isinstance(source, str) else source
        from dslighting.benchmark.core.engine_factory import BenchmarkEngineFactory

        return BenchmarkEngineFactory(self).build_single_task_benchmark(
            descriptor,
            task_id=task_id,
            data_root=data_root,
            **kwargs,
        )


@lru_cache(maxsize=1)
def get_benchmark_source_catalog() -> BenchmarkSourceCatalog:
    return BenchmarkSourceCatalog()
