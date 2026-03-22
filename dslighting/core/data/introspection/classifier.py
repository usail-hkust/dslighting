"""Artifact classification helpers."""

from __future__ import annotations

from pathlib import Path

from .models import ArtifactDescriptor
from .request import DataPerceptionRequest

SUPPORTED_TABULAR_EXTENSIONS = (".csv", ".tsv", ".parquet", ".xlsx")
SUPPORTED_DOCUMENT_EXTENSIONS = (".yml", ".yaml", ".json", ".jsonl", ".md", ".txt", ".sql")
SUPPORTED_DATABASE_EXTENSIONS = (".db", ".sqlite", ".sqlite3")


def classify_artifact(file_path: Path, request: DataPerceptionRequest) -> ArtifactDescriptor | None:
    suffix = file_path.suffix.lower()

    if suffix in SUPPORTED_TABULAR_EXTENSIONS:
        kind = "tabular"
        role = _classify_tabular_role(file_path, request)
    elif request.enable_document_inspection and suffix in SUPPORTED_DOCUMENT_EXTENSIONS:
        kind = "document"
        role = _classify_document_role(file_path)
    elif request.enable_database_inspection and suffix in SUPPORTED_DATABASE_EXTENSIONS:
        kind = "database"
        role = _classify_database_role(file_path)
    else:
        return None

    try:
        size_bytes = int(file_path.stat().st_size)
    except OSError:
        size_bytes = 0

    return ArtifactDescriptor(
        path=file_path,
        relative_path=file_path.relative_to(request.data_dir).as_posix(),
        suffix=suffix,
        size_bytes=size_bytes,
        kind=kind,
        role=role,
    )


def _classify_tabular_role(file_path: Path, request: DataPerceptionRequest) -> str:
    stem = file_path.stem.lower()
    context = request.submission_context or {}
    sample_path = str(context.get("sample_submission_path") or "")
    submission_name = str(context.get("submission_filename") or "")

    if sample_path and Path(sample_path).name == file_path.name:
        return "output_template"
    if submission_name and submission_name == file_path.name:
        return "output_template"
    if "sample_submission" in stem or stem == "submission":
        return "output_template"
    return "input_table"


def _classify_document_role(file_path: Path) -> str:
    stem = file_path.stem.lower()
    if "schema" in stem or "ddl" in stem:
        return "schema_doc"
    return "auxiliary_doc"


def _classify_database_role(file_path: Path) -> str:
    return "database_template"
