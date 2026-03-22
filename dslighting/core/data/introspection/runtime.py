"""Configured runtime wrapper around DataPerceptionService for agent-facing reports."""

from __future__ import annotations

import json
import logging
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from dslighting.core.types.task import TaskType
from dslighting.utils.constants import DEFAULT_CACHE_MAX_ENTRIES
from dslighting.utils.submission_contract import (
    build_tag_contract_reminder,
    extract_submission_tag_contract,
    find_sample_submission_file,
    normalize_submission_tag_contract,
)

from .cache import DataPerceptionCache
from .request import DataPerceptionRequest
from .service import DataPerceptionService

logger = logging.getLogger(__name__)


class DataPerceptionRuntime:
    """Config-bound runtime used by main execution paths instead of DataAnalyzer."""

    def __init__(
        self,
        *,
        cache_enabled: bool = True,
        cache_dir: Optional[Path] = None,
        cache_max_entries: int = DEFAULT_CACHE_MAX_ENTRIES,
        analyzer_version: str = "analyzer_v2",
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

    def analyze(
        self,
        data_dir: Path,
        output_filename: str,
        task_type: Optional[TaskType] = None,
        optimization_context: bool = False,
        task_id: Optional[str] = None,
        submission_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        report = self.analyze_data(
            data_dir,
            task_type=task_type,
            task_id=task_id,
            submission_context=submission_context,
        )
        report += self.generate_io_instructions(output_filename, optimization_context)
        return report

    def analyze_data(
        self,
        data_dir: Path,
        task_type: Optional[TaskType] = None,
        task_id: Optional[str] = None,
        submission_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        normalized_submission_context = self._normalize_submission_context(submission_context)
        request = self.build_request(
            data_dir,
            task_type=task_type,
            task_id=task_id,
            submission_context=normalized_submission_context,
        )
        report = DataPerceptionService(request, cache=self._cache).build_report()
        if task_type == "kaggle":
            submission_analysis = self._analyze_kaggle_submission_format(
                data_dir,
                submission_context=normalized_submission_context,
            )
            if submission_analysis:
                report += f"## Submission Format Requirements\n{submission_analysis}\n\n"
        return report

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

    @staticmethod
    def generate_io_instructions(output_filename: str, optimization_context: bool = False) -> str:
        output_suffix = Path(output_filename).suffix.lower()

        input_instructions = (
            "1. **INPUT DATA:**\n"
            "   - All input files are located in the **current working directory** (./).\n"
            "   - Example: Use `pd.read_csv('train.csv')`."
        )

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

        normalized_contract = normalize_submission_tag_contract(
            submission_context.get("submission_contract")
        )
        if normalized_contract:
            normalized["submission_contract"] = normalized_contract

        return normalized

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
