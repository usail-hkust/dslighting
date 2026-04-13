"""Read-only helpers for expected output artifact contracts."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OutputContractStatus:
    expected_filename: str
    sandbox_expected_path: Path
    exists: bool
    accepted_path: Path | None
    accepted_via_fallback: bool
    size_bytes: int | None
    kind: str
    preview: str
    candidate_files: list[Path]
    error_message: str | None


def is_valid_output_path(path: Path) -> bool:
    """Return True if an output path exists and non-empty directories are not empty."""
    return path.exists() and (not path.is_dir() or any(path.iterdir()))


def find_runner_compatible_output_candidates(
    *,
    sandbox_workdir: Path,
    output_path: Path,
) -> list[Path]:
    """Find output candidates using the same hash-suffix fallback as the runner."""
    stem = output_path.stem
    parts = stem.rsplit("_", 1)
    if len(parts) != 2:
        return []
    pattern = f"{parts[0]}_*{output_path.suffix}"
    return [
        candidate
        for candidate in sorted(sandbox_workdir.glob(pattern))
        if is_valid_output_path(candidate)
    ]


def resolve_runner_output_candidate(
    *,
    sandbox_workdir: Path,
    output_path: Path,
    allow_runner_fallback: bool = True,
) -> tuple[Path, bool]:
    """Resolve the output path accepted by runner collection rules."""
    expected = sandbox_workdir / output_path.name
    if is_valid_output_path(expected):
        return expected, False
    if allow_runner_fallback:
        candidates = find_runner_compatible_output_candidates(
            sandbox_workdir=sandbox_workdir,
            output_path=output_path,
        )
        if candidates:
            return candidates[0], True
    return expected, False


def inspect_output_contract(
    *,
    sandbox_workdir: Path,
    output_path: Path,
    max_preview_rows: int = 3,
    max_candidate_files: int = 20,
    allow_runner_fallback: bool = True,
) -> OutputContractStatus:
    """Inspect whether the expected output artifact exists in the sandbox."""
    sandbox_expected_path = sandbox_workdir / output_path.name
    accepted_path, accepted_via_fallback = resolve_runner_output_candidate(
        sandbox_workdir=sandbox_workdir,
        output_path=output_path,
        allow_runner_fallback=allow_runner_fallback,
    )
    exists = is_valid_output_path(accepted_path)
    candidate_files = _list_candidate_files(
        sandbox_workdir,
        max_candidate_files=max_candidate_files,
    )

    if not exists:
        return OutputContractStatus(
            expected_filename=output_path.name,
            sandbox_expected_path=sandbox_expected_path,
            exists=False,
            accepted_path=None,
            accepted_via_fallback=False,
            size_bytes=None,
            kind="missing",
            preview="",
            candidate_files=candidate_files,
            error_message=f"Expected output `{output_path.name}` was not found in sandbox.",
        )

    return OutputContractStatus(
        expected_filename=output_path.name,
        sandbox_expected_path=sandbox_expected_path,
        exists=True,
        accepted_path=accepted_path,
        accepted_via_fallback=accepted_via_fallback,
        size_bytes=_path_size(accepted_path),
        kind=_detect_kind(accepted_path),
        preview=_preview_path(accepted_path, max_preview_rows=max_preview_rows),
        candidate_files=candidate_files,
        error_message=None,
    )


def render_output_contract_status(status: OutputContractStatus) -> str:
    """Render output contract status as a critical ReAct observation footer."""
    lines = [
        '<SubmissionStatus critical="true">',
        f"expected_filename: {status.expected_filename}",
        f"expected_path_in_sandbox: {status.sandbox_expected_path.name}",
        f"exists: {str(status.exists).lower()}",
    ]
    if status.accepted_path is not None:
        lines.append(f"accepted_filename: {status.accepted_path.name}")
        lines.append(f"accepted_via_fallback: {str(status.accepted_via_fallback).lower()}")
    if status.size_bytes is not None:
        lines.append(f"size_bytes: {status.size_bytes}")
    lines.append(f"kind: {status.kind}")
    if status.error_message:
        lines.append(f"error: {status.error_message}")
    if status.candidate_files:
        rendered_candidates = ", ".join(path.name for path in status.candidate_files[:10])
        lines.append(f"candidate_files: {rendered_candidates}")
    if status.preview:
        lines.append("preview:")
        lines.append(_limit_preview(status.preview))
    lines.append("</SubmissionStatus>")
    return "\n".join(lines)


def _list_candidate_files(
    sandbox_workdir: Path,
    *,
    max_candidate_files: int,
) -> list[Path]:
    if not sandbox_workdir.exists():
        return []
    candidates: list[Path] = []
    for path in sorted(sandbox_workdir.iterdir()):
        if path.name.startswith("_sandbox_script_"):
            continue
        if is_valid_output_path(path):
            candidates.append(path)
        if len(candidates) >= max_candidate_files:
            break
    return candidates


def _detect_kind(path: Path) -> str:
    if path.is_dir():
        return "directory"
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix == ".json":
        return "json"
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
        return "image"
    if suffix in {".txt", ".md", ".log"}:
        return "text"
    return "file"


def _path_size(path: Path) -> int | None:
    try:
        if path.is_dir():
            return sum(child.stat().st_size for child in path.rglob("*") if child.is_file())
        return path.stat().st_size
    except OSError:
        return None


def _preview_path(path: Path, *, max_preview_rows: int) -> str:
    if path.is_dir():
        entries = [child.name for child in sorted(path.iterdir())[:max_preview_rows]]
        return "\n".join(entries)
    if path.suffix.lower() == ".csv":
        return _preview_csv(path, max_preview_rows=max_preview_rows)
    if path.suffix.lower() == ".json":
        return _preview_json(path)
    if path.suffix.lower() in {".txt", ".md", ".log"}:
        return _preview_text(path)
    return ""


def _preview_csv(path: Path, *, max_preview_rows: int) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.reader(handle)
            rows = []
            for idx, row in enumerate(reader):
                rows.append(",".join(row[:12]))
                if idx >= max_preview_rows:
                    break
        return "\n".join(rows)
    except Exception as exc:
        return f"<csv preview unavailable: {exc}>"


def _preview_json(path: Path) -> str:
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return _preview_text(path)
    return _limit_preview(json.dumps(data, ensure_ascii=False, indent=2))


def _preview_text(path: Path) -> str:
    try:
        return _limit_preview(path.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        return f"<text preview unavailable: {exc}>"


def _limit_preview(text: str, *, max_chars: int = 1200) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 32] + "\n...[preview truncated]..."


__all__ = [
    "OutputContractStatus",
    "find_runner_compatible_output_candidates",
    "inspect_output_contract",
    "is_valid_output_path",
    "render_output_contract_status",
    "resolve_runner_output_candidate",
]
