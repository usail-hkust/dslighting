"""Tabular artifact sampling with strict and tolerant parsing paths."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from dslighting.utils.constants import MAX_ROWS_PER_FILE

from ..models import ArtifactDescriptor, ArtifactSummary


class TabularSampler:
    CSV_ENCODINGS = ("utf-8", "utf-8-sig", "gbk", "latin1")
    DEFAULT_MALFORMED_ROW_EXAMPLES = 3

    def __init__(self, *, tolerant_fallback: bool = True, max_rows: int = MAX_ROWS_PER_FILE) -> None:
        self.tolerant_fallback = bool(tolerant_fallback)
        self.max_rows = int(max_rows)

    def summarize(self, descriptor: ArtifactDescriptor) -> ArtifactSummary:
        ext = descriptor.suffix.lower()
        if ext in {".csv", ".tsv"}:
            return self._summarize_delimited(descriptor)
        if ext == ".parquet":
            df = pd.read_parquet(descriptor.path).head(self.max_rows)
        elif ext == ".xlsx":
            df = pd.read_excel(descriptor.path).head(self.max_rows)
        else:  # pragma: no cover - descriptor classification should prevent this
            raise ValueError(f"Unsupported tabular extension: {ext}")

        return ArtifactSummary(
            descriptor=descriptor,
            status="ok",
            detail_lines=[
                f"Format: {ext.lstrip('.')}",
                f"Rows Sampled: {len(df)}",
                f"Columns Detected: {len(df.columns)}",
            ],
            table_text=self._build_dataframe_summary(df),
        )

    def _summarize_delimited(self, descriptor: ArtifactDescriptor) -> ArtifactSummary:
        sep = "\t" if descriptor.suffix.lower() == ".tsv" else ","
        strict_df, strict_encoding, strict_error = self._try_read_delimited_strict(descriptor.path, sep)

        if strict_df is not None:
            return ArtifactSummary(
                descriptor=descriptor,
                status="ok",
                detail_lines=[
                    f"Format: {descriptor.suffix.lower().lstrip('.') or 'delimited'}",
                    f"Encoding Used: {strict_encoding}",
                    f"Rows Sampled: {len(strict_df)}",
                    f"Columns Detected: {len(strict_df.columns)}",
                ],
                table_text=self._build_dataframe_summary(strict_df),
            )

        tolerant_df: Optional[pd.DataFrame] = None
        tolerant_encoding: Optional[str] = strict_encoding
        tolerant_error: Optional[Exception] = None
        if self.tolerant_fallback:
            tolerant_df, tolerant_encoding, tolerant_error = self._try_read_delimited_tolerant(
                descriptor.path,
                sep,
                strict_encoding,
            )

        inspected = self._inspect_delimited_rows(descriptor.path, sep, tolerant_encoding or strict_encoding)
        detail_lines = [
            f"Format: {descriptor.suffix.lower().lstrip('.') or 'delimited'}",
            f"Detected Columns: {inspected['header']}" if inspected["header"] else "Detected Columns: unavailable",
            f"Strict Parse: failed ({self._short_exception(strict_error)})",
        ]
        diagnostics: List[str] = []
        if tolerant_df is not None:
            detail_lines.append(
                f"Tolerant Parse: succeeded with skipped malformed rows (encoding={tolerant_encoding})"
            )
            diagnostics.append("strict_parse_failed")
            diagnostics.append("tolerant_parse_used")
        elif tolerant_error is not None:
            detail_lines.append(f"Tolerant Parse: failed ({self._short_exception(tolerant_error)})")
            diagnostics.append("strict_parse_failed")
            diagnostics.append("tolerant_parse_failed")

        malformed_examples = inspected["malformed_examples"]
        if malformed_examples:
            detail_lines.append("Malformed Row Examples:")
            detail_lines.extend(f"- {example}" for example in malformed_examples)

        return ArtifactSummary(
            descriptor=descriptor,
            status="degraded" if tolerant_df is not None else "error",
            detail_lines=detail_lines,
            table_text=self._build_dataframe_summary(tolerant_df) if tolerant_df is not None else None,
            diagnostics=diagnostics,
        )

    def _try_read_delimited_strict(
        self,
        file_path: Path,
        sep: str,
    ) -> Tuple[Optional[pd.DataFrame], Optional[str], Optional[Exception]]:
        last_error: Optional[Exception] = None
        for encoding in self.CSV_ENCODINGS:
            try:
                df = pd.read_csv(file_path, sep=sep, nrows=self.max_rows, encoding=encoding)
                return df, encoding, None
            except UnicodeDecodeError as exc:
                last_error = exc
                continue
            except Exception as exc:
                return None, encoding, exc
        return None, None, last_error

    def _try_read_delimited_tolerant(
        self,
        file_path: Path,
        sep: str,
        encoding_hint: Optional[str],
    ) -> Tuple[Optional[pd.DataFrame], Optional[str], Optional[Exception]]:
        encodings = [encoding_hint] if encoding_hint else []
        encodings.extend(enc for enc in self.CSV_ENCODINGS if enc != encoding_hint)

        last_error: Optional[Exception] = None
        for encoding in encodings:
            if not encoding:
                continue
            try:
                df = pd.read_csv(
                    file_path,
                    sep=sep,
                    nrows=self.max_rows,
                    encoding=encoding,
                    on_bad_lines="skip",
                    engine="python",
                )
                return df, encoding, None
            except UnicodeDecodeError as exc:
                last_error = exc
                continue
            except Exception as exc:
                last_error = exc
        return None, encoding_hint, last_error

    def _inspect_delimited_rows(
        self,
        file_path: Path,
        sep: str,
        encoding: Optional[str],
        max_examples: int = DEFAULT_MALFORMED_ROW_EXAMPLES,
        max_scan_lines: int = 200,
    ) -> Dict[str, List[str]]:
        selected_encoding = encoding or "utf-8"
        header: List[str] = []
        malformed_examples: List[str] = []

        try:
            with open(file_path, "r", encoding=selected_encoding, errors="replace") as handle:
                for line_no, raw_line in enumerate(handle, start=1):
                    if line_no > max_scan_lines:
                        break
                    row = next(csv.reader([raw_line], delimiter=sep))
                    if line_no == 1:
                        header = row
                        continue
                    if header and len(row) != len(header) and len(malformed_examples) < max_examples:
                        malformed_examples.append(
                            f"line {line_no}: expected {len(header)} fields, saw {len(row)} -> {raw_line.rstrip()}"
                        )
        except Exception as exc:
            malformed_examples.append(f"row inspection failed: {exc}")

        return {"header": header, "malformed_examples": malformed_examples}

    @staticmethod
    def _short_exception(exc: Optional[Exception]) -> str:
        if exc is None:
            return "unknown error"
        return f"{type(exc).__name__}: {exc}"

    @staticmethod
    def _build_dataframe_summary(df: pd.DataFrame) -> str:
        row_count = len(df)
        if row_count == 0:
            missing_pct = pd.Series(np.nan, index=df.columns)
        else:
            missing_pct = (df.isnull().sum() * 100 / row_count).round(2)

        summary = pd.DataFrame(
            {
                "Data Type": df.dtypes,
                "Missing (%)": missing_pct,
                "Cardinality": df.nunique(dropna=True),
            }
        )

        sample_values = [col.dropna().head(2).tolist() for _, col in df.items()]
        summary["Sample Values"] = sample_values
        summary["Sample Values"] = summary["Sample Values"].apply(
            lambda x: str(x) if len(str(x)) < 40 else str(x)[:37] + "..."
        )
        return summary.to_string()
