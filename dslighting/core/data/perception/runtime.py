"""Configured runtime wrapper around DataPerceptionService for agent-facing reports."""

from __future__ import annotations

import json
import logging
import traceback
from dataclasses import asdict
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from dslighting.benchmark.grading.models import SubmissionArtifactContract, SubmissionEntrySpec
from dslighting.core.types.task import TaskType
from dslighting.utils.constants import DEFAULT_CACHE_MAX_ENTRIES, DEFAULT_DATA_PERCEPTION_ANALYZER_VERSION
from dslighting.utils.submission_contract import (
    build_tag_contract_reminder,
    extract_submission_tag_contract,
    find_sample_submission_file,
    normalize_submission_tag_contract,
)

from .budget import PromptBudgetManager
from .cache import DataPerceptionCache
from .models import AgentDataContext
from .renderers.prompt import PromptReportRenderer, RenderProfile
from .request import DataPerceptionRequest
from .service import DataPerceptionService

from dslighting.debug.section_map_context import clear_section_map, set_section_map

logger = logging.getLogger(__name__)


class DataPerceptionRuntime:
    """Config-bound runtime used by main execution paths.

    Main call flow (section-aware, no post-render string appending):
        analyze_data()  →  service.build_base_context()
                        →  _enrich_submission_sections(context)
                        →  budget.apply(context, profile="data_report")
                        →  renderer.render(context, profile="data_report")
                        →  str

        analyze()       →  service.build_base_context()
                        →  _enrich_submission_sections(context)
                        →  _enrich_io_requirements(context, ...)
                        →  budget.apply(context, profile="combined_report")
                        →  renderer.render(context, profile="combined_report")
                        →  str
    """

    def __init__(
        self,
        *,
        cache_enabled: bool = True,
        cache_dir: Optional[Path] = None,
        cache_max_entries: int = DEFAULT_CACHE_MAX_ENTRIES,
        analyzer_version: str = DEFAULT_DATA_PERCEPTION_ANALYZER_VERSION,
        profile: str = "balanced",
        max_artifacts: int = 12,
        max_report_chars: Optional[int] = 14000,
        document_preview_lines: int = 12,
        enable_document_inspection: bool = True,
        enable_database_inspection: bool = True,
        tabular_tolerant_fallback: bool = True,
    ) -> None:
        self.profile = str(profile or "balanced").strip() or "balanced"
        self.max_artifacts = max(1, int(max_artifacts))
        self.max_report_chars = None if max_report_chars is None else max(1000, int(max_report_chars))
        self.document_preview_lines = max(1, int(document_preview_lines))
        self.enable_document_inspection = bool(enable_document_inspection)
        self.enable_database_inspection = bool(enable_database_inspection)
        self.tabular_tolerant_fallback = bool(tabular_tolerant_fallback)
        self._cache = DataPerceptionCache(
            enabled=bool(cache_enabled),
            cache_dir=cache_dir,
            cache_max_entries=cache_max_entries,
            analyzer_version=analyzer_version,
        )
        self._renderer = PromptReportRenderer()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(
        self,
        data_dir: Path,
        output_filename: str,
        task_type: Optional[TaskType] = None,
        optimization_context: bool = False,
        task_id: Optional[str] = None,
        submission_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Return combined data + I/O report for agent consumption (combined_report profile)."""
        normalized = self._normalize_submission_context(submission_context)
        request = self.build_request(
            data_dir,
            task_type=task_type,
            task_id=task_id,
            submission_context=normalized,
        )
        context = self._build_enriched_context(
            request,
            normalized,
            task_type=task_type,
            output_filename=output_filename,
            optimization_context=optimization_context,
            include_io=True,
        )
        budget = PromptBudgetManager(
            max_report_chars=self.max_report_chars,
            renderer=self._renderer,
        )
        context = budget.apply(context, profile="combined_report")
        result = self._renderer.render_with_map(context, profile="combined_report")
        # Propagate section_map to debug observability via context variable.
        set_section_map([asdict(span) for span in result.section_map])
        try:
            return result.text
        finally:
            clear_section_map()

    def analyze_data(
        self,
        data_dir: Path,
        task_type: Optional[TaskType] = None,
        task_id: Optional[str] = None,
        submission_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Return data-only report (data_report profile, no I/O instructions)."""
        normalized = self._normalize_submission_context(submission_context)
        request = self.build_request(
            data_dir,
            task_type=task_type,
            task_id=task_id,
            submission_context=normalized,
        )
        context = self._build_enriched_context(
            request,
            normalized,
            task_type=task_type,
            include_io=False,
        )
        budget = PromptBudgetManager(
            max_report_chars=self.max_report_chars,
            renderer=self._renderer,
        )
        context = budget.apply(context, profile="data_report")
        result = self._renderer.render_with_map(context, profile="data_report")
        # Propagate section_map to debug observability via context variable.
        set_section_map([asdict(span) for span in result.section_map])
        try:
            return result.text
        finally:
            clear_section_map()

    def build_request(
        self,
        data_dir: Path,
        *,
        task_type: Optional[TaskType],
        task_id: Optional[str],
        submission_context: Optional[Dict[str, Any]],
    ) -> DataPerceptionRequest:
        return DataPerceptionRequest(
            data_dir=Path(data_dir),
            task_type=task_type,
            task_id=task_id,
            submission_context=self._normalize_submission_context(submission_context),
            profile=self.profile,
            max_artifacts=self.max_artifacts,
            max_report_chars=self.max_report_chars,
            document_preview_lines=self.document_preview_lines,
            enable_document_inspection=self.enable_document_inspection,
            enable_database_inspection=self.enable_database_inspection,
            tabular_tolerant_fallback=self.tabular_tolerant_fallback,
        )

    # ------------------------------------------------------------------
    # Internal enrichment pipeline
    # ------------------------------------------------------------------

    def _build_enriched_context(
        self,
        request: DataPerceptionRequest,
        submission_context: Dict[str, Any],
        *,
        task_type: Optional[TaskType],
        output_filename: str = "",
        optimization_context: bool = False,
        include_io: bool,
    ) -> AgentDataContext:
        """Build base context from service, then enrich with critical sections."""
        service = DataPerceptionService(request, cache=self._cache)
        context = service.build_base_context()

        # Enrich submission sections
        artifact_req = self._analyze_submission_artifact_requirements(submission_context)
        fmt_full = ""
        fmt_compact = ""
        if task_type == "kaggle":
            contract = self._coerce_submission_artifact_contract(submission_context)
            if contract is None or contract.root_kind == "file":
                fmt_full = self._analyze_kaggle_submission_format(
                    request.data_dir, submission_context=submission_context
                )
                fmt_compact = self._build_compact_submission_format(
                    request.data_dir, submission_context=submission_context
                )

        context = replace(
            context,
            submission_artifact_requirements=artifact_req,
            submission_format_requirements_full=fmt_full,
            submission_format_requirements_compact=fmt_compact,
        )

        # Enrich I/O requirements (only for combined_report profile)
        if include_io and output_filename:
            io_full = self.generate_io_instructions(
                output_filename,
                optimization_context,
                submission_context=submission_context,
            )
            io_compact = self._build_compact_io_instructions(
                output_filename,
                submission_context=submission_context,
            )
            context = replace(
                context,
                io_requirements_full=io_full,
                io_requirements_compact=io_compact,
            )

        return context

    # ------------------------------------------------------------------
    # I/O instructions
    # ------------------------------------------------------------------

    @staticmethod
    def generate_io_instructions(
        output_filename: str,
        optimization_context: bool = False,
        submission_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        contract = DataPerceptionRuntime._coerce_submission_artifact_contract(submission_context)
        if contract is not None:
            output_filename = contract.output_submission_path.name
        output_suffix = Path(output_filename).suffix.lower()

        input_instructions = (
            "1. **INPUT DATA:**\n"
            "   - All input files are located in the **current working directory** (./).\n"
            "   - Example: Use `pd.read_csv('train.csv')`."
        )

        if contract is not None and contract.root_kind == "directory":
            if optimization_context:
                output_instructions = (
                    "2. **OUTPUT ARTIFACT (Dynamic Workflow Context):**\n"
                    "   - Your workflow's `solve` method receives an `output_path` argument.\n"
                    "   - You MUST create a submission directory using `output_path.name` in the current working directory (./).\n"
                    "   - All required files must be written inside that directory.\n"
                )
            else:
                output_instructions = (
                    "2. **OUTPUT ARTIFACT:**\n"
                    "   - You MUST create exactly one submission directory in the current working directory (./).\n"
                    f"   - Required output directory name: `{contract.output_submission_path.name}`\n"
                    "   - Output kind: directory\n"
                )
            required_entries = DataPerceptionRuntime._render_directory_entry_lines(contract.entries)
            return f"""
--- CRITICAL I/O REQUIREMENTS ---

You MUST follow these file system rules precisely. Failure to do so will cause a fatal error.

{input_instructions}

{output_instructions}

3. **REQUIRED FILES INSIDE THE OUTPUT DIRECTORY:**
{required_entries}

**IMPORTANT:**
- Do not place the required files directly in `./`.
- They must all be created inside the required submission directory.
- Missing any required file will make the submission invalid.
"""

        if optimization_context:
            example_write = ""
            if output_suffix == ".csv":
                example_write = "   - **Example Write (Conceptual):** `final_df.to_csv(output_path.name, index=False)`"
            elif output_suffix == ".npy":
                example_write = "   - **Example Write (Conceptual):** `np.save(output_path.name, preds)`"

            output_instructions = (
                "2. **OUTPUT FILE (Dynamic Workflow Context):**\n"
                "   - Your workflow's `solve` method receives an `output_path` argument.\n"
                "   - You MUST save your final submission file using the filename derived from this argument (e.g., `output_path.name`).\n"
                "   - The file must be saved in the current working directory (./).\n"
                + (f"\n{example_write}" if example_write else "")
            )
        else:
            example_write = ""
            if output_suffix == ".csv":
                example_write = f"   - **Correct Example:** `submission_df.to_csv('{output_filename}', index=False)`"
            elif output_suffix == ".npy":
                example_write = f"   - **Correct Example:** `np.save('{output_filename}', preds)`"

            output_instructions = (
                f"2. **OUTPUT FILE:**\n"
                f"   - You MUST save your final submission file to the **current working directory** (./).\n"
                f"   - The required output filename is: `{output_filename}`\n"
                + (f"{example_write}\n" if example_write else "")
            )

        return f"""
--- CRITICAL I/O REQUIREMENTS ---

You MUST follow these file system rules precisely. Failure to do so will cause a fatal error.

{input_instructions}

{output_instructions}

**IMPORTANT:** These path requirements are non-negotiable and must be followed exactly.
"""

    @staticmethod
    def _build_compact_io_instructions(
        output_filename: str,
        submission_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Compact version of I/O instructions: filename/directory only, no examples."""
        contract = DataPerceptionRuntime._coerce_submission_artifact_contract(submission_context)
        if contract is not None:
            output_filename = contract.output_submission_path.name

        if contract is not None and contract.root_kind == "directory":
            required_entries = DataPerceptionRuntime._render_directory_entry_lines(contract.entries)
            return (
                f"\n--- CRITICAL I/O REQUIREMENTS ---\n\n"
                f"- Input files: current working directory (./)\n"
                f"- Output: create directory `{output_filename}` in ./\n"
                f"- Required files inside:\n{required_entries}\n"
            )

        return (
            f"\n--- CRITICAL I/O REQUIREMENTS ---\n\n"
            f"- Input files: current working directory (./)\n"
            f"- Output file: `{output_filename}` in ./\n"
        )

    # ------------------------------------------------------------------
    # Submission analysis helpers (unchanged logic, moved from analyze_data)
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_submission_context(submission_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not isinstance(submission_context, dict):
            return {}

        normalized: Dict[str, Any] = {}
        for key in ("sample_submission_path", "submission_filename", "submission_format"):
            raw_value = submission_context.get(key)
            if raw_value is None:
                continue
            value = str(raw_value).strip()
            if value:
                normalized[key] = value

        raw_output_path = submission_context.get("output_submission_path")
        if raw_output_path is not None:
            output_value = str(raw_output_path).strip()
            if output_value:
                normalized["output_submission_path"] = output_value

        artifact_payload = submission_context.get("submission_artifact_contract")
        if isinstance(artifact_payload, dict):
            normalized["submission_artifact_contract"] = dict(artifact_payload)

        normalized_contract = normalize_submission_tag_contract(
            submission_context.get("submission_contract")
        )
        if normalized_contract:
            normalized["submission_contract"] = normalized_contract

        return normalized

    @staticmethod
    def _coerce_submission_artifact_contract(
        submission_context: Optional[Dict[str, Any]],
    ) -> Optional[SubmissionArtifactContract]:
        if not isinstance(submission_context, dict):
            return None
        try:
            return SubmissionArtifactContract.from_payload(submission_context)
        except Exception:
            logger.warning(
                "Could not parse submission artifact contract from context: %s",
                traceback.format_exc(),
            )
            return None

    @staticmethod
    def _format_entry_descriptor(entry: SubmissionEntrySpec) -> str:
        details: list[str] = []
        if entry.format:
            details.append(entry.format)
        if entry.description:
            details.append(entry.description)
        if entry.sample_path is not None:
            details.append(f"sample: {entry.sample_path.name}")
        if not details:
            return ""
        return " — " + "; ".join(details)

    @classmethod
    def _render_directory_entry_lines(cls, entries: tuple[SubmissionEntrySpec, ...]) -> str:
        rendered: list[str] = []
        for entry in entries:
            if not entry.relative_path:
                continue
            rendered.append(f"   - `{entry.relative_path}`{cls._format_entry_descriptor(entry)}")
        return "\n".join(rendered) or "   - No required entries were declared."

    @classmethod
    def _analyze_submission_artifact_requirements(
        cls,
        submission_context: Optional[Dict[str, Any]],
    ) -> str:
        contract = cls._coerce_submission_artifact_contract(submission_context)
        if contract is None or (contract.root_kind == "file" and len(contract.entries) <= 1):
            return ""

        lines = [
            f"- Root artifact kind: `{contract.root_kind}`",
            f"- Required output root: `{contract.output_submission_path.name}`",
        ]
        if contract.entries:
            lines.append("")
            lines.append("### Required Entries")
            for entry in contract.entries:
                if not entry.relative_path:
                    continue
                lines.append(f"- `{entry.relative_path}`{cls._format_entry_descriptor(entry)}")
        return "\n".join(lines)

    def _analyze_kaggle_submission_format(
        self,
        data_dir: Path,
        submission_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        context = self._normalize_submission_context(submission_context)
        sample_submission_file = self._find_sample_submission(
            data_dir,
            submission_context=context,
        )

        submission_contract = normalize_submission_tag_contract(context.get("submission_contract"))
        if not submission_contract:
            submission_contract = extract_submission_tag_contract(sample_submission_file)
        tag_contract_reminder = build_tag_contract_reminder(submission_contract)

        def with_tag_contract(message: str) -> str:
            base = message.rstrip()
            if tag_contract_reminder:
                return f"{base}\n\n{tag_contract_reminder}\n"
            return f"{base}\n"

        if not sample_submission_file:
            return f"{tag_contract_reminder}\n" if tag_contract_reminder else ""

        suffix = sample_submission_file.suffix.lower()

        try:
            if suffix in {".csv", ".tsv"}:
                sep = "\t" if suffix == ".tsv" else ","
                sample_df = pd.read_csv(sample_submission_file, sep=sep, nrows=2000)

                head_info = sample_df.head().to_string(index=False)
                dtypes_info = sample_df.dtypes.to_string()
                required_columns = sample_df.columns.tolist()

                columns_instruction = f"""
**Required Submission Columns:**
Your submission file MUST contain the following columns in this exact order:
```
{required_columns}
```
This is a strict requirement for the submission to be graded correctly.
"""

                return with_tag_contract(f"""
**CRITICAL:** Your final submission file MUST EXACTLY match the sample submission format (`{sample_submission_file.name}`).
This includes column names, column order, and data types.

{columns_instruction}

**Format Details:**
*First rows preview:*
```text
{head_info}
```

*Detected data types:*
```text
{dtypes_info}
```
""")

            if suffix == ".npy":
                try:
                    arr = np.load(sample_submission_file, mmap_mode="r", allow_pickle=False)
                except ValueError:
                    arr = np.load(sample_submission_file, mmap_mode="r", allow_pickle=True)

                flat_preview = arr.reshape(-1)[:5].tolist() if getattr(arr, "size", 0) else []
                return with_tag_contract(f"""
**CRITICAL:** Your final submission file must follow the NumPy array format shown by `{sample_submission_file.name}`.

**Format Details:**
- File type: `npy`
- Shape: `{tuple(int(dim) for dim in arr.shape)}`
- Dtype: `{arr.dtype}`
- Value preview: `{flat_preview}`
""")

            if suffix == ".jsonl":
                preview_lines: List[str] = []
                parsed_rows: List[Any] = []
                with open(sample_submission_file, "r", encoding="utf-8", errors="ignore") as handle:
                    for _ in range(5):
                        line = handle.readline()
                        if not line:
                            break
                        line = line.rstrip("\n")
                        if not line.strip():
                            continue
                        preview_lines.append(line)
                        try:
                            parsed_rows.append(json.loads(line))
                        except json.JSONDecodeError:
                            parsed_rows.append(line)

                key_summary = ""
                if parsed_rows and all(isinstance(row, dict) for row in parsed_rows):
                    keys = sorted({k for row in parsed_rows for k in row.keys()})
                    key_summary = f"\n- Detected keys: `{keys}`"

                preview = "\n".join(preview_lines) if preview_lines else "(empty sample)"
                return with_tag_contract(f"""
**CRITICAL:** Your final submission file must match the JSONL structure of `{sample_submission_file.name}`.

**Format Details:**
- File type: `jsonl`{key_summary}
- Line preview:
```text
{preview}
```
""")

            if suffix == ".parquet":
                sample_df = pd.read_parquet(sample_submission_file).head(5)
                head_info = sample_df.to_string(index=False)
                dtypes_info = sample_df.dtypes.to_string()
                required_columns = sample_df.columns.tolist()

                return with_tag_contract(f"""
**CRITICAL:** Your final submission file must follow the Parquet schema of `{sample_submission_file.name}`.

**Format Details:**
- Required columns (order preserved): `{required_columns}`
- Dtypes:
```text
{dtypes_info}
```
- Row preview:
```text
{head_info}
```
""")

            return with_tag_contract(f"""
**CRITICAL:** Your final submission must match the sample submission file `{sample_submission_file.name}`.

Detected format: `{suffix or '<no extension>'}`.
Please inspect this file directly and preserve its structure exactly.
""")

        except Exception:
            logger.warning(
                "Could not parse sample submission file '%s': %s",
                sample_submission_file,
                traceback.format_exc(),
            )
            return with_tag_contract(f"""
**CRITICAL:** Your final submission file MUST match the format of `{sample_submission_file.name}`.
(Automatic format analysis failed; inspect the sample file manually.)
""")

    def _build_compact_submission_format(
        self,
        data_dir: Path,
        submission_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Compact version: filename + required columns only, no preview/dtypes."""
        context = self._normalize_submission_context(submission_context)
        sample_file = self._find_sample_submission(data_dir, submission_context=context)
        if not sample_file:
            return ""

        suffix = sample_file.suffix.lower()
        try:
            if suffix in {".csv", ".tsv"}:
                sep = "\t" if suffix == ".tsv" else ","
                sample_df = pd.read_csv(sample_file, sep=sep, nrows=1)
                required_columns = sample_df.columns.tolist()
                return (
                    f"**CRITICAL:** Match `{sample_file.name}` exactly.\n"
                    f"- Required columns (in order): `{required_columns}`\n"
                )
            if suffix == ".npy":
                try:
                    arr = np.load(sample_file, mmap_mode="r", allow_pickle=False)
                except ValueError:
                    arr = np.load(sample_file, mmap_mode="r", allow_pickle=True)
                return (
                    f"**CRITICAL:** Match `{sample_file.name}` — shape `{tuple(int(d) for d in arr.shape)}`, "
                    f"dtype `{arr.dtype}`.\n"
                )
        except Exception:
            pass
        return f"**CRITICAL:** Match `{sample_file.name}` format exactly.\n"

    def _find_sample_submission(
        self,
        data_dir: Path,
        submission_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Path]:
        context = self._normalize_submission_context(submission_context)

        try:
            return find_sample_submission_file(
                data_dir,
                sample_submission_path=str(context.get("sample_submission_path", "") or ""),
                submission_filename=str(context.get("submission_filename", "") or ""),
            )
        except Exception:
            logger.warning("Could not scan data directory '%s': %s", data_dir, traceback.format_exc())
            return None
