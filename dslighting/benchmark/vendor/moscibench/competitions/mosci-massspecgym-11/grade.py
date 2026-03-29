from __future__ import annotations

import ast
import re

import pandas as pd

TASK_NAME = 'mosci-massspecgym-11'
FAMILY = 'massspecgym'
LOCAL_TASK_ID = 11
GLOBAL_TASK_ID = 42
JUDGE_TYPE = '>'
EXPECTED_KIND = 'numeric'
TOLERANCE = 0.10


def _extract_row(df: pd.DataFrame) -> pd.Series:
    if df is None or df.empty:
        raise ValueError("Submission or answer dataframe is empty")
    if "id" in df.columns:
        matched = df[df["id"].astype(str) == str(GLOBAL_TASK_ID)]
        if not matched.empty:
            return matched.iloc[0]
    return df.iloc[0]


def _unwrap_answer(value: object) -> str:
    text = "" if value is None else str(value).strip()
    if text.startswith("@answer[") and text.endswith("]"):
        text = text[len("@answer[") : -1].strip()
    if text.lower().startswith("answer:"):
        text = text.split(":", 1)[1].strip()
    return text.strip().strip('"').strip("'")


def _normalized_text(text: str) -> str:
    return " ".join(str(text).strip().lower().split())


def _to_bool(text: str):
    lowered = _normalized_text(text)
    if re.search(r"\btrue\b", lowered) and not re.search(r"\bfalse\b", lowered):
        return True
    if re.search(r"\bfalse\b", lowered) and not re.search(r"\btrue\b", lowered):
        return False
    if lowered in {"1", "yes", "on"}:
        return True
    if lowered in {"0", "no", "off"}:
        return False
    return None


def _extract_float(text: str):
    matches = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text)
    if not matches:
        return None
    try:
        return float(matches[-1])
    except ValueError:
        return None


def _maybe_literal(text: str):
    stripped = text.strip()
    if not stripped or stripped[0] not in "[({":
        return None
    try:
        return ast.literal_eval(stripped)
    except Exception:
        return None


def _canonical_literal(value):
    if isinstance(value, tuple):
        return [_canonical_literal(v) for v in value]
    if isinstance(value, list):
        return [_canonical_literal(v) for v in value]
    if isinstance(value, dict):
        return {
            str(k): _canonical_literal(v)
            for k, v in sorted(value.items(), key=lambda item: str(item[0]))
        }
    return value


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    try:
        submission_row = _extract_row(submission)
        answer_row = _extract_row(answers)
        pred = _unwrap_answer(submission_row["answer"])
        gold = _unwrap_answer(answer_row["answer"])

        if EXPECTED_KIND == "bool":
            gold_bool = _to_bool(gold)
            pred_bool = _to_bool(pred)
            return 1.0 if gold_bool is not None and pred_bool == gold_bool else 0.0

        if EXPECTED_KIND == "numeric":
            gold_num = _extract_float(gold)
            pred_num = _extract_float(pred)
            if gold_num is None or pred_num is None:
                return 0.0
            if JUDGE_TYPE == "=":
                tol = abs(gold_num) * TOLERANCE if gold_num != 0 else TOLERANCE
                return 1.0 if abs(pred_num - gold_num) <= tol else 0.0
            if JUDGE_TYPE == ">":
                return 1.0 if pred_num > gold_num else 0.0
            if JUDGE_TYPE == ">=":
                return 1.0 if pred_num >= gold_num else 0.0
            if JUDGE_TYPE == "<":
                return 1.0 if pred_num < gold_num else 0.0
            if JUDGE_TYPE == "<=":
                return 1.0 if pred_num <= gold_num else 0.0
            return 0.0

        gold_lit = _maybe_literal(gold)
        pred_lit = _maybe_literal(pred)
        if gold_lit is not None and pred_lit is not None:
            return 1.0 if _canonical_literal(pred_lit) == _canonical_literal(gold_lit) else 0.0

        gold_norm = _normalized_text(gold)
        pred_norm = _normalized_text(pred)
        if pred_norm == gold_norm:
            return 1.0
        if gold_norm and gold_norm in pred_norm:
            return 1.0
        return 0.0
    except Exception as exc:
        print(f"Grading error in {TASK_NAME}: {exc}")
        return 0.0
